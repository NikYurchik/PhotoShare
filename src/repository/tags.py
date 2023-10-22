from typing import List

from sqlalchemy import select, insert
from sqlalchemy.orm import Session

from src.database.models import Tag, tag_photo_association as t2p


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


    async def add_tags_to_photo(self, tags: List[str], photo_id: int, session: Session, is_commit: bool=True) -> List[Tag]:
        """
        Add tags to a photo
        Args:
            tags_str (str): A string containing tags separated by commas.
            photo_id: The ID of the photo to which tags will be added.
            session: The database session
        Returns:
            List[Tag]: The list of tags added to the photo
        """
        result = []
        for tag in tags:
            tag_ = await TagRepository().check_tag_exist_or_create(tag, session)    # -> Tag
            query = insert(t2p).values(tag_id=tag_.id, photo_id=photo_id).returning(t2p)
            add_tag_to_db = session.execute(query)
            result.append(tag_)
        if is_commit:
            session.commit()
        return result


    async def get_tags_photo(self, photo_id: int, session: Session) -> List[Tag]:
        tquery = select(Tag).join(t2p).where(Tag.id == t2p.c.tag_id).where(t2p.c.photo_id == photo_id)
        tags = session.execute(tquery).scalars().all()
        return tags 


