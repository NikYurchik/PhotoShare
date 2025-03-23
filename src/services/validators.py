from typing import List

from fastapi import HTTPException, status
import requests

from src.conf import messages
from src.conf.config import MAX_TAGS_COUNT

class Validator:

    async def validate_tags_count(self, tags_str: str, tags: List[str]) -> List[str]:
        """
        Validate the number of tags in the provided list
        Args:
            tags_str (List[str]): A list of tags as strings
        Raises:
            HTTPException: If the number of tags exceeds the maximum allowed limit (max_tags_count)
        Returns:
            None
        """
        tags_list = []

        if tags_str:
            tags_ = tags_str.replace(" ", "").split(",")
            tags_list.extend(tags_)

        if tags:
            tags_list.extend(tags)

        if len(tags_list) > 0:
            tags_list = list(set(tags_list))

        if len(tags_list) > MAX_TAGS_COUNT:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=messages.MAXIMUM_TAGS_COUNT)

        return tags_list


    async def check_transform_url(self, url) -> str:
        result = ""
        try:
            req = requests.head(url, allow_redirects=True)
            if req.status_code != 200:
                result = req.headers.get('x-cld-error')
        except HTTPException as err:
            result = err.detail
        except Exception as err:
            result = err.args
        return result


