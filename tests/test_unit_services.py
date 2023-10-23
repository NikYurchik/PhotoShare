import unittest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

from src.services.validators import Validator
from src.services.email import send_email
from src.conf import messages
from src.conf.config import MAX_TAGS_COUNT, settings


class TestServices(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        pass

    # validate_tags_count
    async def test_validate_tags_count(self):
        tags_str = "#tag1, #tag2"
        tags = ["#tag3", "#tag4"]
        res_tags = ["#tag1", "#tag2", "#tag3", "#tag4"]
        result = await Validator().validate_tags_count(tags_str=tags_str, tags=tags) #-> List[str]:
        self.assertEqual(result.sort(), res_tags.sort())

    async def test_validate_tags_count_many(self):
        tags_str = "#tag, #tagg, #taggg"
        tags = "#tag1", "#tag2", "#tag3"
        with self.assertRaises(HTTPException) as cm:
            await Validator().validate_tags_count(tags_str=tags_str, tags=tags) #-> List[str]:
        cm_exception = cm.exception
        self.assertEqual(cm_exception.status_code, 400)
        self.assertEqual(cm_exception.detail, messages.MAXIMUM_TAGS_COUNT)


    # send_email
    @patch("src.services.email.FastMail.send_message")
    async def test_send_email(self, mock_fm):
        mock_fm.return_value = None
        mf = settings.mail_from
        settings.mail_from = "test@email.com"
        result = await send_email(email="test@email.com", username="test", host="http://email.com")
        settings.mail_from = mf
        self.assertIsNone(result)


