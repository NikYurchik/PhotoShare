import re
import qrcode
import aiofiles.os
from typing import List, Optional

from fastapi import HTTPException, status, UploadFile
from sqlalchemy import insert, select, update, delete, desc, asc
from sqlalchemy.orm import Session
from cloudinary import uploader

from src.database.models import Role, Photo, User, PhotoURL, tag_photo_association as t2p, Tag
from src.repository.tags import TagRepository
from src.schemas import PhotoUpdateModel, PhotoTransformModel, PhotoQRCodeModel
from src.conf import messages
from src.services.cloud_image import CloudImage


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
            return {"photo": new_photo, "tags": tags_list}

        except Exception as e:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))


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
        if not photo:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail=messages.PHOTO_NOT_FOUND)
        elif photo.user_id != current_user.id and current_user.roles != Role.admin:
            session.rollback()
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail=messages.OPERATION_NOT_AVAILABLE)

        result = CloudImage.delete_image(photo.file_url)
        if result:
            session.rollback()
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=result)
        session.commit()


    async def get_photo_by_id(self, photo_id: int, current_user: User, session: Session) -> Optional[Photo]:
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
        query = select(Photo).where(Photo.id == photo_id)
        photo = session.execute(query).scalar_one_or_none()
        if not photo:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail=messages.PHOTO_NOT_FOUND)
        tags = await TagRepository().get_tags_photo(photo_id, session)
        return {"photo": photo, "tags": tags}


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
        elif photo.user_id != current_user.id and current_user.roles != Role.admin:
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
        query = select(Photo).order_by(desc(Photo.created_at)).offset(offset).limit(per_page)
        photos = session.execute(query).scalars().all()
        for photo in photos:
            tags = tags = await TagRepository().get_tags_photo(photo.id, session)
            result.append({"photo": photo, "tags": tags})
        # print(result)
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
        query = select(Photo).where(Photo.user_id == user_id).order_by(desc(Photo.created_at)).offset(offset).limit(per_page)
        photos = session.execute(query).scalars().all()
        for photo in photos:
            tags = tags = await TagRepository().get_tags_photo(photo.id, session)
            result.append({"photo": photo, "tags": tags})
        # print(result)
        return result


    async def search_photos(self, keyword: str, tag: str, order_by: str, session: Session):
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
        # print(f"keyword: {keyword}")
        # print(f"tag: {tag}")
        # print(f"order_by: {order_by}")
        photos_query = select(Photo)

        if keyword:
            keyword_filter = Photo.description.ilike(f"%{keyword}%")
            photos_query = photos_query.where(keyword_filter)

        if tag:
            tag_query = select(Tag).where(Tag.name == tag)
            tag_obj = session.execute(tag_query).scalar_one_or_none()

            if tag_obj:
                tag_filter = t2p.c.tag_id == tag_obj.id
                photos_query = photos_query.join(t2p).where(tag_filter)
                # photos_query = photos_query.join(Tag2Photo).where(Tag2Photo.tag_id == tag_obj.id)

        if order_by == 'newest':
            photos_query = photos_query.order_by(Photo.created_at.desc())
        elif order_by == 'oldest':
            photos_query = photos_query.order_by(Photo.created_at.asc())

        result = []
        photos = session.execute(photos_query).scalars().all()
        for photo in photos:
            tags = await TagRepository().get_tags_photo(photo.id, session)
            result.append({"photo": photo, "tags": tags})

        return result
        # return photos


    async def upload_transform_photo(self, body: PhotoTransformModel, photo: Photo,
                                     db: Session) -> Photo:

        url_changed_photo = CloudImage.upload_transform_image(body, photo.file_url)

        photourl = db.query(PhotoURL).filter(PhotoURL.file_url == url_changed_photo).first()
        if photourl:
            return photourl
        
        try:
            new_photo = PhotoURL(file_url=url_changed_photo, photo=photo)
            db.add(new_photo)
            db.commit()
            db.refresh(new_photo)
        except Exception as err:
            s = str(err)
            s = s[0:s.index("\n")]
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=s)
        
        return new_photo


    async def update_qr_url(self, body: PhotoQRCodeModel, photo: Photo | PhotoURL, is_transform: bool=False) -> str:
        qr_name = f"c{photo.id}" if is_transform else f"b{photo.id}"
        qr_extension = "png"

        qr_os_folder = "../../temp_qr_photo"
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

        tags = await TagRepository().get_tags_photo(photo.id, db)
        return {"photo": photo, "tags": tags}
        # return photo


    async def update_transphoto_qr_url(self, body: PhotoQRCodeModel, photo: Photo | PhotoURL,
                                  db: Session) -> Photo | PhotoURL:
        if not photo.qr_url:
            photo_qr_url = await self.update_qr_url(body, photo, True)
            photo.qr_url = photo_qr_url
            db.commit()
        return photo


    async def delete_transform_photo(self, photo: PhotoURL, db: Session) -> None:

        db.delete(photo)

        result = CloudImage.delete_image(photo.file_url)
        if result:
            db.rollback()
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=result)

        db.commit()


    async def delete_all_transform_photo(self, photo: Photo, db: Session) -> None:

        photos_to_del = db.query(PhotoURL).filter(PhotoURL.photo_id == photo.id).all()

        query = delete(PhotoURL).where(PhotoURL.photo_id == photo.id)
        db.execute(query)

        for one_photo in photos_to_del:
            result = CloudImage.delete_image(one_photo.file_url)

            if result:
                db.rollback()
                raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=result)

        db.commit()

