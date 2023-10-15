import re
from typing import List, Optional

from fastapi import HTTPException, status, UploadFile
from sqlalchemy import insert, select, update, delete, desc, asc
from cloudinary.uploader import upload, destroy
from sqlalchemy.orm import Session

from src.database.models import Photo, User, tag_photo_association as t2p, Tag, Role, tag_photo_association
from src.repository.tags import TagRepository
from src.schemas import PhotoUpdateModel


class PhotosRepository:

    async def upload_new_photo(self, user_id: int | None, photo_description: str, tags: str,
                               photo: UploadFile, current_user: User, session: Session) -> Photo:
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
        if user_id != current_user.id:
            if not user_id and current_user.roles == Role.admin:
                user_id = current_user.id
            else:
                raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Unauthorized, or user is not admin")
        try:
            uploaded_file = upload(photo.file, folder="upload")
            query = insert(Photo).values(
                description=photo_description,
                file_url=uploaded_file["secure_url"],
                user_id=user_id,
            ).returning(Photo)
            new_photo = session.execute(query).scalar_one()
            tags_list = []
            if tags:
                tags_list = await self.__add_tags_to_photo(tags, new_photo.id, session)
            session.commit()
            return {"photo": new_photo, "tags": tags_list}
        except Exception as e:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def delete_photo(self, user_id: int | None, photo_id: int, current_user: User, session: Session) -> None:
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
        if user_id != current_user.id:
            if not user_id and current_user.roles == Role.admin:
                user_id = current_user.id
            else:
                raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Unauthorized, or user is not admin")
        query = delete(Photo).where(Photo.id == photo_id, Photo.user_id == user_id).returning(Photo)
        photo = session.execute(query).scalar_one_or_none()
        if not photo:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Photo not found")

        photo_url = photo.file_url
        pattern = r"/v\d+/(.*?)\."
        match = re.search(pattern, photo_url)
        public_id = match.group(1)

        result = destroy(public_id)
        if result.get('result') != 'ok':
            return HTTPException(status.HTTP_400_BAD_REQUEST, detail=result.get('message'))
        session.commit()

    async def get_photo_by_id(self, user_id: int | None, photo_id: int,
                              current_user: User, session: Session) -> Optional[Photo]:
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
        if user_id != current_user.id:
            if not user_id and current_user.roles == Role.admin:
                user_id = current_user.id
            else:
                raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Unauthorized, or user is not admin")
        query = select(Photo).where(Photo.id == photo_id, Photo.user_id == user_id)
        photo = session.execute(query).scalar_one_or_none()
        if not photo:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Photo not found")
        return photo

    async def update_photo_description(self, user_id: int | None, photo_id: int, body: PhotoUpdateModel,
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
        if user_id != current_user.id:
            if not user_id and current_user.roles == Role.admin:
                user_id = current_user.id
            else:
                raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Unauthorized, or user is not admin")
        query = (
            update(Photo)
            .where(Photo.id == photo_id, Photo.user_id == user_id)
            .values(**body.model_dump())
            .returning(Photo)
        )
        photo = session.execute(query).scalar_one_or_none()
        if not photo:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Photo not found")
        session.commit()
        return photo

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
        offset = (page - 1) * per_page
        query = select(Photo).order_by(desc(Photo.created_at)).offset(offset).limit(per_page)
        photos = session.execute(query).scalars().all()

        return photos

    async def get_photos_by_user(self, user_id: int | None, page: int, per_page: int, session: Session) -> List[Photo]:
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
        offset = (page - 1) * per_page
        query = select(Photo).where(Photo.user_id == user_id).order_by(desc(Photo.created_at)).offset(offset).limit(
            per_page)
        photos = session.execute(query).scalars().all()
        return photos

    async def __add_tags_to_photo(self, tags_str: List[str], photo_id: int, session: Session) -> List[Tag]:
        """
        Add tags to a photo
        Args:
            tags_str (str): A string containing tags separated by commas.
            photo_id: The ID of the photo to which tags will be added.
            session: The database session
        Returns:
            List[Tag]: The list of tags added to the photo
        """
        result = []
        tags = tags_str[0].split(',')
        for tag in tags:
            tag_ = await TagRepository().check_tag_exist_or_create(tag, session)
            query = insert(t2p).values(tag_id=tag_.id, photo_id=photo_id).returning(t2p)
            add_tag_to_db = session.execute(query)
            result.append(tag_)
        session.commit()
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
        photos_query = select(Photo)

        if keyword:
            keyword_filter = Photo.description.ilike(f"%{keyword}%")
            photos_query = photos_query.where(keyword_filter)

        if tag:
            tag_query = select(Tag).where(Tag.name == tag)
            tag_obj = session.execute(tag_query).scalar_one_or_none()

            if tag_obj:
                tag_filter = tag_photo_association.c.tag_id == tag_obj.id
                photos_query = photos_query.join(tag_photo_association).where(tag_filter)

        if order_by == 'newest':
            photos_query = photos_query.order_by(Photo.created_at.desc())
        elif order_by == 'oldest':
            photos_query = photos_query.order_by(Photo.created_at.asc())

        photos = session.execute(photos_query).scalars().all()

        return photos


