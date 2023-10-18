import os

import unittest
from unittest.mock import MagicMock, patch

from libgravatar import Gravatar
from sqlalchemy.orm import Session
from fastapi import HTTPException, status, UploadFile
from cloudinary import uploader

from src.database.models import User, Photo, Tag
from src.schemas import PhotoUpdateModel
from src.services.roles import Role
from src.repository.photos import PhotosRepository
from src.repository.tags import TagRepository
from src.conf import messages


class TestPhotos(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.session = MagicMock(spec=Session)
        self.uploadfile = MagicMock(spec=UploadFile("fileupload.tst"))
        self.uploader = MagicMock(spec=uploader)
        self.uploader.destroy = MagicMock(spec=uploader.destroy)
        self.user = User(id=1, username="username", email="test@mail.com", roles=Role.admin)
        self.photo = Photo(id=1, file_url="https://gravatar.com/image.png", description="Test image")
        self.url_photo = "https://gravatar.com/image.png"
        self.tags="#tags"


    # get_all_photos
    async def test_get_all_photos(self):
        photos = [Photo(), Photo(), Photo(), Photo()]
        self.session.execute().scalars().all.return_value = photos
        result = await PhotosRepository().get_all_photos(page=1, per_page=10, session=self.session)
        self.assertEqual(result, photos)


    # get_photos_by_user
    async def test_get_photos_by_user(self):
        photos = [Photo(), Photo(), Photo()]
        self.session.execute().scalars().all.return_value = photos
        result = await PhotosRepository().get_photos_by_user(user_id=1, page=1, per_page=10, session=self.session)
        self.assertEqual(result, photos)


    # get_photo_by_id
    async def test_get_photo_by_id(self):
        self.session.execute().scalar_one_or_none.return_value = self.photo
        result = await PhotosRepository().get_photo_by_id(photo_id=self.photo.id, current_user=self.user, session=self.session)
        self.assertEqual(result, self.photo)

    async def test_get_photo_by_id_notfound(self):
        self.session.execute().scalar_one_or_none.return_value = None
        with self.assertRaises(HTTPException) as cm:
            result = await PhotosRepository().get_photo_by_id(photo_id=self.photo.id, current_user=self.user, session=self.session)
        cm_exception = cm.exception
        self.assertEqual(cm_exception.status_code, 404)
        self.assertEqual(cm_exception.detail, messages.PHOTO_NOT_FOUND)


    # delete_photo
    async def test_delete_photo_notfound(self):
        self.session.execute().scalar_one_or_none.return_value = None
        with self.assertRaises(HTTPException) as cm:
            await PhotosRepository().delete_photo(user_id=None, photo_id=999, current_user=self.user, session=self.session)
        cm_exception = cm.exception
        self.assertEqual(cm_exception.status_code, 404)
        self.assertEqual(cm_exception.detail, messages.PHOTO_NOT_FOUND)

    async def test_delete_photo_noadmin(self):
        user = User(id=2, username="username", email="test@mail.com", roles=Role.user)
        with self.assertRaises(HTTPException) as cm:
            await PhotosRepository().delete_photo(user_id=1, photo_id=999, current_user=user, session=self.session)
        cm_exception = cm.exception
        self.assertEqual(cm_exception.status_code, 403)
        self.assertEqual(cm_exception.detail, messages.OPERATION_NOT_AVAILABLE)

    @patch("src.repository.photos.uploader.destroy")
    async def test_delete_photo_badrequest(self, mock_destroy):
        photo = self.photo
        photo.file_url = "https://res.cloudinary.com/dqglsxwms/image/upload/v1697427418/upload/vplnv9bplyylkvyomdgd.jpg"
        self.session.execute().scalar_one_or_none.return_value = photo
        mock_destroy.return_value = {"result": "br", "message": messages.BAD_REQUEST}
        self.session.rollback.return_value = None
        with self.assertRaises(HTTPException) as cm:
            await PhotosRepository().delete_photo(user_id=1, photo_id=1, current_user=self.user, session=self.session)
        cm_exception = cm.exception
        self.assertEqual(cm_exception.status_code, 400)

    @patch("src.repository.photos.uploader.destroy")
    async def test_delete_photo(self, mock_destroy):
        photo = self.photo
        photo.file_url = "https://res.cloudinary.com/dqglsxwms/image/upload/v1697427418/upload/vplnv9bplyylkvyomdgd.jpg"
        self.session.execute().scalar_one_or_none.return_value = photo
        mock_destroy.return_value = {"result": "ok"}
        self.session.commit.return_value = None
        result = await PhotosRepository().delete_photo(user_id=1, photo_id=1, current_user=self.user, session=self.session)
        self.assertIsNone(result)


    # upload_new_photo
    async def test_upload_new_photo_noadmin(self):
        user = User(id=2, username="username", email="test@mail.com", roles=Role.user)
        with self.assertRaises(HTTPException) as cm:
            await PhotosRepository().upload_new_photo(user_id=1, photo_description=self.photo.description, tags=self.tags,
                                                      photo=self.uploadfile, current_user=user, session=self.session)
        cm_exception = cm.exception
        self.assertEqual(cm_exception.status_code, 403)
        self.assertEqual(cm_exception.detail, messages.OPERATION_NOT_AVAILABLE)

    @patch("src.repository.tags.TagRepository.check_tag_exist_or_create")
    @patch("src.repository.photos.uploader.upload")
    async def test_upload_new_photo_badrequest(self, mock_upload, mock_tag):
        mock_upload.return_value = {"secure_url": self.photo.file_url}
        tags = Tag(id=1, name=self.tags)
        mock_tag.return_value = [tags]
        self.session.execute().scalar_one.return_value = self.photo
        self.session.commit.return_value = None
        self.session.execute().return_value = None
        with self.assertRaises(HTTPException) as cm:
            result = await PhotosRepository().upload_new_photo(user_id=None, photo_description=self.photo.description, tags=self.tags,
                                                               photo=self.uploadfile, current_user=self.user, session=self.session)
        cm_exception = cm.exception
        self.assertEqual(cm_exception.status_code, 400)

    @patch("src.repository.tags.TagRepository.check_tag_exist_or_create")
    @patch("src.repository.photos.uploader.upload")
    async def test_upload_new_photo(self, mock_upload, mock_tag):
        mock_upload.return_value = {"secure_url": self.photo.file_url}
        tags = Tag(id=1, name=self.tags)
        mock_tag.return_value = tags
        self.session.execute().scalar_one.return_value = self.photo
        self.session.commit.return_value = None
        self.session.execute().return_value = None
        etalon = {"photo": self.photo, "tags": [tags]}
        result = await PhotosRepository().upload_new_photo(user_id=None, photo_description=self.photo.description, tags=self.tags,
                                                           photo=self.uploadfile, current_user=self.user, session=self.session)
        self.assertEqual(result, etalon)


    # update_photo_description
    async def test_update_photo_description_notfound(self):
        body_ = PhotoUpdateModel(description=self.photo.description)
        self.session.execute().scalar_one_or_none.return_value = None
        with self.assertRaises(HTTPException) as cm:
            await PhotosRepository().update_photo_description(user_id=None, photo_id=999, body=body_, current_user=self.user, session=self.session)
        cm_exception = cm.exception
        self.assertEqual(cm_exception.status_code, 404)
        self.assertEqual(cm_exception.detail, messages.PHOTO_NOT_FOUND)

    async def test_update_photo_description_noadmin(self):
        body_ = PhotoUpdateModel(description=self.photo.description)
        user = User(id=2, username="username", email="test@mail.com", roles=Role.user)
        with self.assertRaises(HTTPException) as cm:
            await PhotosRepository().update_photo_description(user_id=1, photo_id=999, body=body_, current_user=user, session=self.session)
        cm_exception = cm.exception
        self.assertEqual(cm_exception.status_code, 403)
        self.assertEqual(cm_exception.detail, messages.OPERATION_NOT_AVAILABLE)

    async def test_update_photo_description(self):
        body_ = PhotoUpdateModel(description=self.photo.description)
        self.session.execute().scalar_one_or_none.return_value = self.photo
        self.session.commit.return_value = None
        result = await PhotosRepository().update_photo_description(user_id=1, photo_id=self.photo.id, body=body_, current_user=self.user, session=self.session)
        self.assertEqual(result, self.photo)


    # search_photos
    async def test_search_photos(self):
        photos = [Photo(), Photo(), Photo()]
        tags = Tag(id=1, name=self.tags)
        self.session.execute().scalar_one_or_none.return_value = tags
        self.session.execute().scalars().all.return_value = photos
        result = await PhotosRepository().search_photos(keyword="str", tag="#str", order_by="newest", session=self.session)
        self.assertEqual(result, photos)
        result = await PhotosRepository().search_photos(keyword="str", tag="#str", order_by="oldest", session=self.session)
        self.assertEqual(result, photos)


    # check_tag_exist_or_create
    async def test_check_tag_exist_or_create_exists(self):
        tags = Tag(id=1, name=self.tags)
        self.session.execute().scalar_one_or_none.return_value = tags
        self.session.execute().scalar_one.return_value = tags
        result = await TagRepository().check_tag_exist_or_create(tag_name=self.tags, session=self.session)
        self.assertEqual(result, tags)

    async def test_check_tag_exist_or_create_notexists(self):
        tags = Tag(id=1, name=self.tags)
        self.session.execute().scalar_one_or_none.return_value = None
        self.session.execute().scalar_one.return_value = tags
        self.session.commit.return_value = None
        result = await TagRepository().check_tag_exist_or_create(tag_name=self.tags, session=self.session)
        self.assertEqual(result, tags)

