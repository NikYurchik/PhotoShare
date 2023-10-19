from typing import List

from fastapi import HTTPException, status

from src.conf import messages
from src.conf.config import MAX_TAGS_COUNT

class Validator:

    async def validate_tags_count(self, tags_str: str) -> List[str]:
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

        if len(tags_list) > MAX_TAGS_COUNT:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=messages.MAXIMUM_TAGS_COUNT)

        return tags_list
