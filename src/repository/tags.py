from sqlalchemy import select, insert
from sqlalchemy.orm import Session

from src.database.models import Tag


class TagRepository:

    async def check_tag_exist_or_create(self, tag_name: str, session: Session) -> Tag:
        """
        Check if a tag with the specified name exists in the database.
        If the tag does not exist, create a new tag with the provided name.

        Args:
            tag_name (str): The name of the tag to check or create.
            session (Session): The database session to use for querying and creating tags.

        Returns:
            Tag: The existing or newly created Tag object.
        """
        query = select(Tag).where(Tag.name == tag_name)
        tag = session.execute(query).scalar_one_or_none()
        if tag:
            return tag
        query_ = insert(Tag).values(name=tag_name).returning(Tag)
        new_tag = session.execute(query_).scalar_one()
        session.commit()
        return new_tag

