import unittest
from unittest.mock import MagicMock

from libgravatar import Gravatar
from sqlalchemy.orm import Session

from src.database.models import User
from src.schemas import UserModel
from src.services.roles import Role
from src.repository.users import (
    get_users,
    get_users_by_mask,
    get_user_by_id,
    toggle_banned_user,
    set_roles_user,
    get_user_by_email,
    create_user,
    update_token,
    confirmed_email,
    update_avatar
)


class TestUsers(unittest.IsolatedAsyncioTestCase):

    # @classmethod
    # def setUpClass(cls) -> None:
    #     if not os.path.exists("logs"):
    #         os.mkdir("logs")
    #     return super().setUpClass()

    def setUp(self):
        self.session = MagicMock(spec=Session)
        self.gravatar = MagicMock(spec=Gravatar)
        self.gravatar.get_image = MagicMock(spec=Gravatar.get_image)
        self.user = User(id=1)
        self.email = "test@mail.com"
        self.url_avatar = "https://gravatar.com/image.png"
        self.username = "username"
        self.password="qwerty1234"

    # def tearDown(self) -> None:
    #     self.logs.close()
    #     return super().tearDown()


    # get_users,
    async def test_get_users(self):
        users = [User(), User(), User(), User()]
        self.session.query().limit().offset().all.return_value = users
        result = await get_users(offset=0, limit=10, db=self.session)
        self.assertEqual(result, users)

    # get_users_by_mask,
    async def test_get_users_by_mask_found(self):
        users = [User(), User(), User()]
        self.session.query().filter().limit().offset().all.return_value = users
        result = await get_users_by_mask(offset=0, limit=10, search_mask='search_mask', db=self.session)
        self.assertEqual(result, users)

    async def test_get_users_by_mask_notfound(self):
        users = []
        self.session.query().filter().limit().offset().all.return_value = users
        result = await get_users_by_mask(offset=0, limit=10, search_mask='search_mask', db=self.session)
        self.assertEqual(result, users)

    # get_user_by_id,
    async def test_get_user_by_id_found(self):
        user = User()
        self.session.query().filter().first.return_value = user
        result = await get_user_by_id(user_id=1, db=self.session)
        self.assertEqual(result, user)

    async def test_get_user_by_id_notfound(self):
        user = None
        self.session.query().filter().first.return_value = user
        result = await get_user_by_id(user_id=1, db=self.session)
        self.assertEqual(result, user)

    # toggle_banned_user,
    async def test_toggle_banned_user(self):
        user0 = User(username=self.username, email=self.email, password=self.password, is_banned=False)
        user = User(username=self.username, email=self.email, password=self.password, is_banned=False)
        self.session.query().filter().first.return_value = user
        result = await toggle_banned_user(user_id=1, db=self.session)
        self.assertEqual(result.id, user.id)
        self.assertEqual(result.email, user.email)
        self.assertEqual(result.roles, user.roles)
        self.assertNotEqual(result.is_banned, user0.is_banned)


    # set_roles_user
    async def test_set_roles_user(self):
        user0 = User(username=self.username, email=self.email, password=self.password, roles=Role.admin)
        user = User(username=self.username, email=self.email, password=self.password, roles=Role.admin)
        self.session.query().filter().first.return_value = user
        result = await set_roles_user(user_id=1, role=Role.moderator, db=self.session)
        self.assertEqual(result.id, user.id)
        self.assertEqual(result.email, user.email)
        self.assertNotEqual(result.roles, user0.roles)


    async def test_get_user_by_email_found(self):
        user = User()
        self.session.query().filter().first.return_value = user
        result = await get_user_by_email(email=self.email, db=self.session)
        self.assertEqual(result, user)

    async def test_get_user_by_email_notfound(self):
        user = None
        self.session.query().filter().first.return_value = user
        result = await get_user_by_email(email=self.email, db=self.session)
        self.assertEqual(result, user)


    async def test_create_user(self):
        body = UserModel(username=self.username, email=self.email, password=self.password)
        self.gravatar.return_value = self.url_avatar
        self.gravatar.get_image.return_value = self.url_avatar
        result = await create_user(body=body, db=self.session)
        self.assertEqual(result.username, body.username)
        self.assertEqual(result.email, body.email)
        self.assertEqual(result.password, body.password)
        self.assertTrue(hasattr(result, "id"))


    async def test_update_token(self):
        user = User(username=self.username, email=self.email, password=self.password, avatar=self.url_avatar)
        token = "zxcvbnm,./"
        self.session.commit.return_value = None
        await update_token(user=user, token=token, db=self.session)
        self.assertEqual(user.refresh_token, token)


    async def test_confirmed_email(self):
        user = User(username=self.username, email=self.email, password=self.password, avatar=self.url_avatar)
        confirmed = True
        self.session.query().filter().first.return_value = user
        self.session.commit.return_value = None
        await confirmed_email(email=user.email, db=self.session)
        self.assertEqual(user.confirmed, confirmed)

    async def test_update_avatar(self):
        user = User(username=self.username, email=self.email, password=self.password)
        self.session.query().filter().first.return_value = user
        self.session.commit.return_value = None
        result = await update_avatar(user=user, url=self.url_avatar, db=self.session)
        self.assertEqual(result.avatar, self.url_avatar)
