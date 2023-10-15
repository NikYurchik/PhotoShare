from typing import List

from fastapi import HTTPException, status


class Validator:

    async def validate_tags_count(self, tags_str: List[str]) -> None:
        """
        Validate the number of tags in the provided list
        Args:
            tags_str (List[str]): A list of tags as strings
        Raises:
            HTTPException: If the number of tags exceeds the maximum allowed limit (max_tags_count)
        Returns:
            None
        """
        max_tags_count = 5
        tags = tags_str[0].split(',')

        if len(tags) > max_tags_count:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"You can add a maximum of {max_tags_count} tags."
            )
