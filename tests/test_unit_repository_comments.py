import unittest
from unittest.mock import MagicMock

from sqlalchemy.orm import Session
from fastapi import HTTPException

from src.database.models import User, Comment, Photo
from src.schemas import UserModel, CommentModel, CommentUpdate, CommentDelete
from src.services.roles import UserRole
from src.conf import messages
from src.repository.comments import (
    get_comments,
    create_comment,
    update_comment,
    delete_comment
)


class TestUsers(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.session = MagicMock(spec=Session)
        self.photo = Photo(id=1)
        self.user = User(id=1)
        self.comment = Comment(id=1, text="Comment", user=self.user, user_id = self.user.id, photo=self.photo, photo_id=self.photo.id)

    # get_comments,
    async def test_get_comments(self):
        comments = [Comment(), Comment(), Comment(), Comment()]
        self.session.query().filter().all.return_value = comments
        result = await get_comments(photo_id=self.photo.id, db=self.session)
        self.assertEqual(result, comments)

    async def test_get_comments_notfound(self):
        comments = []
        self.session.query().filter().all.return_value = comments
        result = await get_comments(photo_id=self.photo.id, db=self.session)
        self.assertEqual(result, comments)


    # create_comment,
    async def test_create_comment(self):
        body_ = CommentModel(text=self.comment.text)
        self.session.query().filter().first.return_value = self.photo
        self.session.add.return_value = None
        self.session.commit.return_value = None
        self.session.refresh.return_value = None
        result = await create_comment(photo_id=self.photo.id, body=body_, user=self.user, db=self.session)
        self.assertEqual(result.text, self.comment.text)

    async def test_create_comment_photo_notfound(self):
        body_ = CommentModel(text=self.comment.text)
        self.session.query().filter().first.return_value = None
        with self.assertRaises(HTTPException) as cm:
            result = await create_comment(photo_id=self.photo.id, body=body_, user=self.user, db=self.session)
        cm_exception = cm.exception
        self.assertEqual(cm_exception.status_code, 404)
        self.assertEqual(cm_exception.detail, messages.PHOTO_NOT_FOUND)


    # update_comment,
    async def test_update_comment(self):
        body_ = CommentModel(text=self.comment.text)
        self.session.query().filter().first.return_value = self.comment
        self.session.commit.return_value = None
        result = await update_comment(photo_id=self.photo.id, comment_id=self.comment.id, body=body_, user=self.user, db=self.session)
        self.assertEqual(result.id, self.comment.id)
        self.assertEqual(result.text, self.comment.text)

    async def test_update_comment_notoperation(self):
        body_ = CommentModel(text=self.comment.text)
        self.session.query().filter().first.return_value = self.comment
        user_ = User(id=2)
        with self.assertRaises(HTTPException) as cm:
            result = await update_comment(photo_id=self.photo.id, comment_id=self.comment.id, body=body_, user=user_, db=self.session)
        cm_exception = cm.exception
        self.assertEqual(cm_exception.status_code, 403)
        self.assertEqual(cm_exception.detail, messages.OPERATION_NOT_AVAILABLE)


    # delete_comment
    async def test_delete_comment(self):
        # body_ = CommentDelete(id=self.comment.id)
        self.session.query().filter().first.return_value = self.comment
        self.session.commit.return_value = None
        result = await delete_comment(photo_id=self.photo.id, comment_id=self.comment.id, user=self.user, db=self.session)
        self.assertIsNone(result)

    async def test_delete_comment_notoperation(self):
        # body_ = CommentDelete(id=self.comment.id)
        self.session.query().filter().first.return_value = self.comment
        user_ = User(id=2)
        with self.assertRaises(HTTPException) as cm:
            result = await delete_comment(photo_id=self.photo.id, comment_id=self.comment.id, user=user_, db=self.session)
        cm_exception = cm.exception
        self.assertEqual(cm_exception.status_code, 403)
        self.assertEqual(cm_exception.detail, messages.OPERATION_NOT_AVAILABLE)
