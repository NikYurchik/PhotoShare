import os

import unittest
from unittest.mock import MagicMock, patch

from libgravatar import Gravatar
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from cloudinary import uploader

from src.database.models import User, Photo
from src.schemas import PhotoSchema
from src.services.roles import Role
from src.repository.photos import PhotosRepository
from src.conf import messages


class TestPhotos(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.session = MagicMock(spec=Session)
        self.uploader = MagicMock(spec=uploader)
        self.uploader.destroy = MagicMock(spec=uploader.destroy)
        self.user = User(id=1, username="username", email="test@mail.com", roles=Role.admin)
        self.photo = Photo(id=1, file_url="https://gravatar.com/image.png", description="Test image")
        self.url_photo = "https://gravatar.com/image.png"

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
