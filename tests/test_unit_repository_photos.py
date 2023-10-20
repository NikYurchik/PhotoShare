from typing import List

import unittest
from unittest.mock import MagicMock, patch

from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile
from cloudinary import uploader

from src.database.models import User, Photo, Tag
from src.schemas import PhotoUpdateModel, PhotoResponse
from src.services.roles import Role
from src.repository.photos import PhotosRepository
from src.repository.tags import TagRepository
from src.conf import messages


class TestPhotos(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.session = MagicMock(spec=Session)
        self.uploadfile = MagicMock(spec=UploadFile("fileupload.tst"))
        # self.add_tags = MagicMock(spec=TagRepository.add_tags_to_photo, return_value=self.tags)

        # self.uploader = MagicMock(spec=uploader)
        # self.uploader.destroy = MagicMock(spec=uploader.destroy)
        
        self.user = User(id=1, username="username", email="test@mail.com", roles=Role.admin)

        self.url_photo = "https://gravatar.com/image.png"
        self.description = "Test image"
        self.photo = Photo(id=1, user_id=1, file_url=self.url_photo, description=self.description)
        self.photo2 = Photo(id=2, user_id=2, file_url=self.url_photo+"2", description=self.description+"2")
        self.photos = [self.photo, self.photo2]
        self.tag_name="tag"
        self.tag = Tag(id=1, name=self.tag_name)
        self.tag2 = Tag(id=2, name=self.tag_name+"2")
        self.tags = [self.tag, self.tag2]
        self.result_photo = {"photo": self.photo, "tags": self.tags}
        self.result_photos = [{"photo": self.photo, "tags": self.tags}, {"photo": self.photo2, "tags": self.tags}]


    # get_photo_by_id
    async def test_get_photo_by_id(self):
        self.session.execute().scalar_one_or_none.return_value = self.photo
        self.session.execute().scalars().all.return_value = self.tags
        result = await PhotosRepository().get_photo_by_id(photo_id=self.photo.id, current_user=self.user, session=self.session)
        # print(self.photo)
        # print(self.result_photo)
        # print(result)
        self.assertEqual(result, self.result_photo)


    async def test_get_photo_by_id_notfound(self):
        self.session.execute().scalar_one_or_none.return_value = None
        self.session.execute().scalars().all.return_value = self.tags
        with self.assertRaises(HTTPException) as cm:
            result = await PhotosRepository().get_photo_by_id(photo_id=self.photo.id, current_user=self.user, session=self.session)
        cm_exception = cm.exception
        self.assertEqual(cm_exception.status_code, 404)
        self.assertEqual(cm_exception.detail, messages.PHOTO_NOT_FOUND)


    # get_all_photos
    @patch("src.repository.tags.TagRepository.get_tags_photo")
    async def test_get_all_photos(self, mock_tags):
        mock_tags.return_value = self.tags
        self.session.execute().scalars().all.return_value = self.photos
        result = await PhotosRepository().get_all_photos(page=1, per_page=10, session=self.session)
        # print(self.photo)
        # print(self.photos)
        # print(self.result_photos)
        # print(result)
        self.assertEqual(result, self.result_photos)


    # get_photos_by_user
    @patch("src.repository.tags.TagRepository.get_tags_photo")
    async def test_get_photos_by_user(self, mock_tags):
        mock_tags.return_value = self.tags
        self.session.execute().scalars().all.return_value = self.photos
        result = await PhotosRepository().get_photos_by_user(user_id=1, current_user=self.user, page=1, per_page=10, session=self.session)
        self.assertEqual(result, self.result_photos)


    # search_photos
    @patch("src.repository.tags.TagRepository.get_tags_photo")
    async def test_search_photos(self, mock_tags):
        mock_tags.return_value = self.tags
        self.session.execute().scalar_one_or_none.return_value = self.tag
        self.session.execute().scalars().all.return_value = self.photos
        result = await PhotosRepository().search_photos(keyword="str", tag="#str", order_by="newest", session=self.session)
        self.assertEqual(result, self.result_photos)
        result = await PhotosRepository().search_photos(keyword="str", tag="#str", order_by="oldest", session=self.session)
        self.assertEqual(result, self.result_photos)


    # delete_photo
    async def test_delete_photo_notfound(self):
        self.session.execute().scalar_one_or_none.return_value = None
        with self.assertRaises(HTTPException) as cm:
            await PhotosRepository().delete_photo(photo_id=999, current_user=self.user, session=self.session)
        cm_exception = cm.exception
        self.assertEqual(cm_exception.status_code, 404)
        self.assertEqual(cm_exception.detail, messages.PHOTO_NOT_FOUND)

    async def test_delete_photo_noadmin(self):
        user = User(id=2, username="username", email="test@mail.com", roles=Role.user)
        with self.assertRaises(HTTPException) as cm:
            await PhotosRepository().delete_photo(photo_id=1, current_user=user, session=self.session)
        cm_exception = cm.exception
        self.assertEqual(cm_exception.status_code, 403)
        self.assertEqual(cm_exception.detail, messages.OPERATION_NOT_AVAILABLE)

    @patch("src.services.cloud_image.CloudImage.delete_image")
    async def test_delete_photo_badrequest(self, mock_destroy):
        photo = self.photo
        photo.file_url = "https://res.cloudinary.com/dqglsxwms/image/upload/v1697427418/upload/vplnv9bplyylkvyomdgd.jpg"
        self.session.execute().scalar_one_or_none.return_value = photo
        mock_destroy.return_value = messages.BAD_REQUEST
        self.session.rollback.return_value = None
        with self.assertRaises(HTTPException) as cm:
            await PhotosRepository().delete_photo(photo_id=1, current_user=self.user, session=self.session)
        cm_exception = cm.exception
        self.assertEqual(cm_exception.status_code, 400)

    @patch("src.services.cloud_image.CloudImage.delete_image")
    async def test_delete_photo(self, mock_delete):
        photo = self.photo
        photo.file_url = "https://res.cloudinary.com/dqglsxwms/image/upload/v1697427418/upload/vplnv9bplyylkvyomdgd.jpg"
        self.session.execute().scalar_one_or_none.return_value = photo
        mock_delete.return_value = ""
        self.session.commit.return_value = None
        result = await PhotosRepository().delete_photo(photo_id=1, current_user=self.user, session=self.session)
        self.assertIsNone(result)


    @patch("src.repository.tags.TagRepository.check_tag_exist_or_create")
    @patch("src.services.cloud_image.CloudImage.upload_image")
    async def test_upload_new_photo_badrequest(self, mock_upload, mock_tag):
        mock_upload.return_value = self.photo.file_url
        mock_tag.return_value = self.tags
        self.session.execute().scalar_one.return_value = self.photo
        self.session.commit.return_value = None
        self.session.execute().return_value = None
        with self.assertRaises(HTTPException) as cm:
            result = await PhotosRepository().upload_new_photo(photo_description=self.photo.description, tags=self.tags,
                                                               photo_file=self.uploadfile, current_user=self.user, session=self.session)
        cm_exception = cm.exception
        self.assertEqual(cm_exception.status_code, 400)

    @patch("src.repository.tags.TagRepository.check_tag_exist_or_create")
    @patch("src.services.cloud_image.CloudImage.upload_image")
    async def test_upload_new_photo(self, mock_upload, mock_tag):
        mock_upload.return_value = self.photo.file_url
        mock_tag.return_value = self.tag
        self.session.execute().scalar_one.return_value = self.photo
        self.session.commit.return_value = None
        self.session.execute().return_value = None
        result = await PhotosRepository().upload_new_photo(photo_description=self.photo.description, tags=self.tags,
                                                           photo_file=self.uploadfile, current_user=self.user, session=self.session)
        self.assertEqual(result.get('photo'), self.result_photo.get('photo'))
        self.assertEqual(result.get('tags')[0], self.result_photo.get('tags')[0])
        self.assertEqual(result.get('tags')[1], self.result_photo.get('tags')[0])


    # update_photo_description
    async def test_update_photo_description_notfound(self):
        description = self.photo.description
        self.session.execute().scalar_one_or_none.return_value = None
        with self.assertRaises(HTTPException) as cm:
            await PhotosRepository().update_photo_description(photo_id=999, description=description, current_user=self.user, session=self.session)
        cm_exception = cm.exception
        self.assertEqual(cm_exception.status_code, 404)
        self.assertEqual(cm_exception.detail, messages.PHOTO_NOT_FOUND)

    async def test_update_photo_description_noadmin(self):
        description = self.photo.description
        user = User(id=2, username="username", email="test@mail.com", roles=Role.user)
        with self.assertRaises(HTTPException) as cm:
            await PhotosRepository().update_photo_description(photo_id=1, description=description, current_user=user, session=self.session)
        cm_exception = cm.exception
        self.assertEqual(cm_exception.status_code, 403)
        self.assertEqual(cm_exception.detail, messages.OPERATION_NOT_AVAILABLE)

    @patch("src.repository.tags.TagRepository.get_tags_photo")
    async def test_update_photo_description(self, mock_tags):
        description = self.photo.description
        self.session.execute().scalar_one_or_none.return_value = self.photo
        self.session.commit.return_value = None
        mock_tags.return_value = self.tags
        result = await PhotosRepository().update_photo_description(photo_id=self.photo.id, description=description, current_user=self.user, session=self.session)
        self.assertEqual(result, self.result_photo)


    # check_tag_exist_or_create
    async def test_check_tag_exist_or_create_exists(self):
        self.session.execute().scalar_one_or_none.return_value = self.tag
        self.session.execute().scalar_one.return_value = self.tag
        result = await TagRepository().check_tag_exist_or_create(tag_name=self.tag.name, session=self.session)
        self.assertEqual(result, self.tag)

    async def test_check_tag_exist_or_create_notexists(self):
        self.session.execute().scalar_one_or_none.return_value = None
        self.session.execute().scalar_one.return_value = self.tag
        self.session.commit.return_value = None
        result = await TagRepository().check_tag_exist_or_create(tag_name=self.tag.name, session=self.session)
        self.assertEqual(result, self.tag)


    # add_tags_to_photo
    @patch("src.repository.tags.TagRepository.check_tag_exist_or_create")
    async def test_add_tags_to_photo(self, mock_tag):
        mock_tag.return_value = self.tag
        self.session.execute().return_value = None
        result = await TagRepository().add_tags_to_photo(tags=[self.tag.name], photo_id=1, session=self.session)
        self.assertEqual(result, [self.tag])

    # get_tags_photo
    async def test_get_tags_photo(self):
        self.session.execute().scalars().all.return_value = self.tags
        result = await TagRepository().get_tags_photo(photo_id=1, session=self.session)
        self.assertEqual(result, self.tags)
