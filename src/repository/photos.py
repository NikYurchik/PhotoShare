import re
import qrcode
import aiofiles.os
import json
from typing import List, Optional

from fastapi import HTTPException, status, UploadFile
from sqlalchemy import insert, select, update, delete, desc, asc, and_
from sqlalchemy.orm import Session

from src.base import app, templates
from src.database.models import UserRole, Photo, User, PhotoURL, Tag, tag_photo_association as t2p
from src.repository.tags import TagRepository
from src.schemas import PhotoTransformModel, PhotoQRCodeModel, PhotoResponse
from src.conf import messages
from src.conf.config import MAX_TAGS_COUNT
from src.services.cloud_image import CloudImage
from src.services.validators import Validator
from src.services.custom_json import Jsons
from src.repository.comments import get_comments
from src.services.pager import Pagination



class PhotosRepository:

    async def upload_new_photo(self,
                               photo_description: str,
                               tags: List[str],
                               photo_file: UploadFile,
                               current_user: User,
                               session: Session) -> Photo:
        """
        Upload a new photo with description and tags, associated with the given user
        Args:
            user_id (int | None): The ID of the user who is uploading the photo.
            photo_description (str): The description of the photo.
            tags (str): A string containing tags separated by commas.
            photo (UploadFile): The uploaded photo file.
            current_user (User): The current user performing the upload.
            session: The database session
        Returns:
            dict: A dictionary containing the uploaded photo and its associated tags
        Raises:
            HTTPException: If an error occurs during the upload or database operation.
        """
        user_id = current_user.id
        try:
            photo_url = CloudImage.upload_image(photo_file=photo_file.file, user=current_user)

            query = insert(Photo).values(
                description=photo_description,
                file_url=photo_url,
                user_id=user_id,
            ).returning(Photo)
            new_photo = session.execute(query).scalar_one()

            tags_list = []
            if tags:
                tags_list = await TagRepository().add_tags_to_photo(tags, new_photo.id, session, False)
            session.commit()
            return new_photo

        except Exception as e:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))


    async def add_tag_to_photo(self, tags: List[str], photo_id: int, current_user: User, session: Session) -> PhotoResponse:
        """
        Add a tag to a photo and return the updated photo.
        Args:
            tag (str): The name of the tag to be added.
            photo_id (int): The ID of the photo to which the tag should be added.
            current_user (User): The current user performing the action.
            session (Session): The SQLAlchemy session.
        Returns:
            PhotoResponse: A response object containing the updated photo information.
        Raises:
            HTTPException: If the tag count validation fails or the tag does not exist.
        Example:
            photo = await add_tag_to_photo("nature", 1, current_user, session)
        """
        tags_photo = await TagRepository().get_tags_photo(photo_id, session)
        tags_new, tags_full = await TagRepository().get_different_tags(tags, tags_photo)
        await Validator().validate_tags_count(tags_str="", tags=tags_full)
        await TagRepository().add_tags_to_photo(tags_new, photo_id, session, False)
        session.commit()
        photo = await self.get_photo_by_id(photo_id=photo_id, session=session)
        return photo


    async def remove_tag_from_photo(self, tag: str, photo_id: int, current_user: User,
                                    session: Session) -> PhotoResponse:
        """
        Remove a tag from a photo and return the updated photo.
        Args:
            tag (str): The name of the tag to be removed.
            photo_id (int): The ID of the photo from which the tag should be removed.
            current_user (User): The current user performing the action.
            session (Session): The SQLAlchemy session.
        Returns:
            PhotoResponse: A response object containing the updated photo information.
        Raises:
            HTTPException: If the tag does not exist or could not be removed.
        Example:
            updated_photo = await remove_tag_from_photo("landscape", 1, current_user, session)
        """
        query = select(Tag).where(Tag.name == tag)
        tag_ = session.execute(query).scalar_one_or_none()
        if not tag_:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail=messages.TAG_PHOTO_NOT_FOUND)
        query = delete(t2p).where(t2p.c.tag_id == tag_.id, t2p.c.photo_id == photo_id)
        session.execute(query)
        session.commit()
        photo = await self.get_photo_by_id(photo_id=photo_id, session=session)
        return photo


    async def delete_photo(self, photo_id: int, current_user: User, session: Session) -> None:
        """
        Delete a photo with the given photo_id associated with the user
        Args:
            user_id (int | None): The ID of the user who is deleting the photo.
            photo_id (int): The ID of the photo to be deleted.
            current_user (User): The current user performing the delete.
            session: The database session
        Raises:
            HTTPException: If the photo is not found or an error occurs during deletion.
        """
        query = delete(Photo).where(Photo.id == photo_id).returning(Photo)
        photo = session.execute(query).scalar_one_or_none()
        tags = await TagRepository().get_tags_photo(photo_id, session)
        comm = await get_comments(page=0, per_page=0, photo_id=photo.id, db=session)

        if not photo:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail=messages.PHOTO_NOT_FOUND)
        elif photo.user_id != current_user.id and current_user.roles != UserRole.admin:
            session.rollback()
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail=messages.OPERATION_NOT_AVAILABLE)

        await self.delete_all_transform_photo(photo, session, is_commit=False)

        if photo.qr_url:
            result = CloudImage.delete_image(photo.qr_url)
            if result:
                session.rollback()
                raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=result)

        result = CloudImage.delete_image(photo.file_url)
        if result:
            session.rollback()
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=result)
        
        session.commit()
        return {"photo": photo, "tags": tags, "comments": comm}


    async def search_photos(self,
                            session: Session, 
                            page: int=None, 
                            per_page: int=None, 
                            user_id: int=None, 
                            keyword: str=None, 
                            tag: str=None, 
                            order_by: str=None):
        """
        Search for photos by keyword or tag and filter the results by rating or date.

        Args:
            keyword (str): The keyword to search for in photo descriptions.
            tag (str): The tag to filter photos by.
            order_by (str): The sorting criteria ('rating' or 'date').
            session (Session): The database session.

        Returns:
            List[Photo]: A list of Photo objects that match the search and filter criteria.
        """
        photos_query = select(Photo.id,
                              Photo.user_id,
                              Photo.file_url,
                              Photo.description,
                              Photo.created_at,
                              Photo.updated_at,
                              Photo.qr_url)

        if user_id:
            photos_query = photos_query.where(Photo.user_id == user_id)
            
        if keyword:
            keyword_filter = Photo.description.ilike(f"%{keyword}%")
            photos_query = photos_query.where(keyword_filter)

        if tag:
            tag_query = select(Tag).where(Tag.name == tag)
            tag_obj = session.execute(tag_query).scalar_one_or_none()

            if tag_obj:
                tag_filter = t2p.c.tag_id == tag_obj.id
                photos_query = photos_query.join(t2p).where(tag_filter)

        if order_by == 'newest':
            photos_query = photos_query.order_by(Photo.created_at.desc())
        elif order_by == 'oldest':
            photos_query = photos_query.order_by(Photo.created_at.asc())
        
        paginate = Pagination(photos_query, session, page, per_page)
        photos, pages = paginate.get_page()
        result = []
        for photo in photos:
            ph1 = await self.get_photo_by_id(photo_id=photo.id, session=session, limit_comment=MAX_TAGS_COUNT)
            result.append(ph1)
        return result, pages


    async def get_photo_by_id(self, photo_id: int, session: Session, limit_comment: int = 0) -> Optional[Photo]:
        """
        Retrieve a photo with the given photo_id associated with the user
        Args:
            user_id (int | None): The ID of the user who is fetching the photo.
            photo_id (int): The ID of the photo to be retrieved.
            current_user (User): The current user performing the fetch.
            session: The database session
        Returns:
            Photo: The retrieved photo
        Raises:
            HTTPException: If the photo is not found.
        """
        photo = session.query(Photo.id,
                              Photo.file_url,
                              Photo.qr_url,
                              Photo.description,
                              Photo.created_at,
                              Photo.user_id,
                              User.username
                            ) \
                    .select_from(Photo) \
                    .join(User) \
                    .filter(Photo.id == photo_id) \
                    .first()

        if not photo:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail=messages.PHOTO_NOT_FOUND)

        tags = await TagRepository().get_tags_photo(photo_id, session)
        comm = await get_comments(page=1, per_page=limit_comment, photo_id=photo.id, db=session)
        return {"photo": photo, "tags": tags, "comments": comm}


    async def update_photo_description(self, photo_id: int, description: str,
                                       current_user: User, session: Session) -> Optional[Photo]:
        """
        Update the description of a photo with the given photo_id associated with the user
        Args:
            user_id (int | None): The ID of the user who is updating the photo description.
            photo_id: The ID of the photo to be updated.
            body: The updated photo description.
            current_user (User): The current user performing the update.
            session: The database session
        Returns:
            Photo: The updated photo
        Raises:
            HTTPException: If the photo is not found.
        """
        query = (
            update(Photo)
            .where(Photo.id == photo_id)
            .values({"description": description})
            .returning(Photo)
        )
        photo = session.execute(query).scalar_one_or_none()

        if not photo:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Photo not found")
        elif photo.user_id != current_user.id and current_user.roles != UserRole.admin:
            session.rollback()
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail=messages.OPERATION_NOT_AVAILABLE)

        session.commit()
        tags = await TagRepository().get_tags_photo(photo_id, session)
        return {"photo": photo, "tags": tags}


    async def get_all_photos(self, page: int, per_page: int, session: Session) -> List[Photo]:
        """
        Retrieve a list of photos with pagination, sorted from newest to oldest
        Args:
            page (int): The current page.
            per_page (int): The number of photos per page.
            session: The database session
        Returns:
            List[Photo]: The list of photos
        """
        result = []
        offset = (page - 1) * per_page

        photos = session.query(Photo.id,
                               Photo.file_url,
                               Photo.qr_url,
                               Photo.description,
                               Photo.created_at,
                               Photo.user_id,
                               User.username
                              ) \
                    .select_from(Photo) \
                    .join(User) \
                    .all()

        for photo in photos:
            tags = tags = await TagRepository().get_tags_photo(photo.id, session)
            comm = await get_comments(page=0, per_page=0, photo_id=photo.id, db=session)
            result.append({"photo": photo, "tags": tags, "comments": comm})

        return result


    async def get_photos_by_user(self, user_id: int | None, current_user: User, page: int, per_page: int, session: Session) -> List[Photo]:
        """
        Retrieve a list of photos uploaded by a specific user with pagination, sorted from newest to oldest
        Args:
            user_id: The ID of the user whose photos are being fetched.
            page (int): The current page.
            per_page (int): The number of photos per page.
            session: The database session
        Returns:
            List[Photo]: The list of photos uploaded by the user
        """
        result = []
        offset = (page - 1) * per_page
        if user_id is None:
            user_id = current_user.id

        photos = session.query(Photo.id,
                               Photo.file_url,
                               Photo.qr_url,
                               Photo.description,
                               Photo.created_at,
                               Photo.user_id,
                               User.username
                              ) \
                    .select_from(Photo) \
                    .join(User) \
                    .filter(Photo.user_id == user_id) \
                    .all()

        for photo in photos:
            tags = tags = await TagRepository().get_tags_photo(photo.id, session)
            comm = await get_comments(page=0, per_page=0, photo_id=photo.id, db=session)
            result.append({"photo": photo, "tags": tags, "comments": comm})

        return result


    async def get_transform_photos(self, photo_id, session: Session):
        photo_transforms = session.query(PhotoURL) \
                                .filter(PhotoURL.photo_id == photo_id) \
                                .all()
        return photo_transforms


    async def get_transform_photo(self, photo_id, transform_id, session: Session):
        photo_transform = session.query(PhotoURL) \
                                .filter(and_(PhotoURL.photo_id == photo_id, PhotoURL.id == transform_id)) \
                                .first()
        return photo_transform


    async def upload_transform_photo(self, body: PhotoTransformModel, photo: Photo, db: Session) -> Photo:

        url_changed_photo = CloudImage.upload_transform_image(body, photo.file_url)
        # print(f">>> UpLoad_transform: {url_changed_photo}")
        err = await Validator().check_transform_url(url_changed_photo)
        if err:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=err)

        photourl = db.query(PhotoURL).filter(PhotoURL.file_url == url_changed_photo).first()
        if photourl:
            return photourl
        
        try:
            params = await Jsons.get_transform_params(body)
            params = json.dumps(params)
            # print(f">>> UpLoad_transform: {params}")

            new_photo = PhotoURL(file_url=url_changed_photo,
                                 photo=photo,
                                 params=params
                                )
            db.add(new_photo)
            db.commit()
            db.refresh(new_photo)
        except Exception as err:
            s = str(err)
            ind = s.find("\n")
            if ind > 0:
                s = s[0:ind]
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=s)
        
        return new_photo


    async def update_transform_photo(self, body: PhotoTransformModel, photo: Photo, trans_photo: PhotoURL,
                                     db: Session) -> Photo:

        url_changed_photo = CloudImage.upload_transform_image(body, photo.file_url)
        # print(f">>> update_transform: {url_changed_photo}")
        err = await Validator().check_transform_url(url_changed_photo)
        if err:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=err)

        photourl = db.query(PhotoURL).filter(PhotoURL.file_url == url_changed_photo).first()
        if photourl:
            return photourl
        
        try:
            params = await Jsons.get_transform_params(body)
            params = json.dumps(params)
            # print(f">>> update_transform: {params}")

            if trans_photo.params != params and trans_photo.qr_url:     # Изменился URL и есть старый QR
                result = CloudImage.delete_image(trans_photo.qr_url)    # Удалить QR
                if result:
                    raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=result)
                trans_photo.qr_url = None

            trans_photo.file_url = url_changed_photo
            trans_photo.params = params
            db.commit()
        except Exception as err:
            s = str(err)
            ind = s.find("\n")
            if ind > 0:
                s = s[0:ind]
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=s)
        
        return trans_photo


    async def update_qr_url(self, body: PhotoQRCodeModel, photo: Photo | PhotoURL, is_transform: bool=False) -> str:
        qr_name = f"c{photo.id}" if is_transform else f"b{photo.id}"
        qr_extension = "png"

        qr_os_folder = "./temp_qr_photo"
        qr_os_path = f"{qr_os_folder}/{qr_name}.{qr_extension}"

        cl_math = re.search(r"/v\d+/(.+)/\w+\.\w+$", photo.file_url)
        if not cl_math:
            cl_math = re.search(r"/v\d+/(.+)/\w+$", photo.file_url)
        ci_folder = cl_math.group(1)
        qr_ci_folder = f"{ci_folder}/qr"

        if not await aiofiles.os.path.exists(qr_os_folder):
            await aiofiles.os.mkdir(qr_os_folder)

        qr = qrcode.QRCode()
        qr.add_data(photo.file_url)
        qr.make(fit=True)

        img = qr.make_image(fill_color=body.fill_color, back_color=body.back_color)
        img.save(qr_os_path)

        photo_qr_url = CloudImage.upload_qrcode(qr_os_path, qr_ci_folder, qr_name)

        await aiofiles.os.remove(qr_os_path)
        return photo_qr_url


    async def update_photo_qr_url(self, body: PhotoQRCodeModel, photo: Photo | PhotoURL,
                                  db: Session) -> Photo | PhotoURL:
        if not photo.qr_url:
            photo_qr_url = await self.update_qr_url(body, photo)
            photo.qr_url = photo_qr_url
            db.commit()

        return photo


    async def update_transphoto_qr_url(self, body: PhotoQRCodeModel, photo: Photo | PhotoURL,
                                        db: Session) -> Photo | PhotoURL:
        if not photo.qr_url:
            photo_qr_url = await self.update_qr_url(body, photo, True)
            photo.qr_url = photo_qr_url
            db.commit()
        return photo


    async def delete_transform_photo(self, photo: PhotoURL, db: Session) -> None:

        db.delete(photo)

        if photo.qr_url:
            result = CloudImage.delete_image(photo.qr_url)
            if result:
                db.rollback()
                raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=result)

        db.commit()


    async def delete_all_transform_photo(self, photo: Photo, db: Session, is_commit: bool=True) -> None:

        photos_to_del = db.query(PhotoURL).filter(PhotoURL.photo_id == photo.id).all()

        query = delete(PhotoURL).where(PhotoURL.photo_id == photo.id)
        db.execute(query)

        for one_photo in photos_to_del:
            if one_photo.qr_url:
                result = CloudImage.delete_image(one_photo.qr_url)
                if result:
                    db.rollback()
                    raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=result)

        if is_commit:
            db.commit()

