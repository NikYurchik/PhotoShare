from typing import List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from src.database.models import Comment, User, Photo, Role
from src.conf import messages
from src.schemas import CommentModel, CommentUpdate, CommentDelete
from src.repository.photos import get_photo_by_id


async def get_comments(photo_id: int, db: Session) -> List[Comment]:
    """Docstring"""
    comments = db.query(Comment).filter(Comment.photo_id == photo_id).all()

    return comments  # noqa


async def create_comment(photo_id: int, body: CommentModel, user: User, db: Session) -> Comment:
    """Docstring"""
    photo = await get_photo_by_id(photo_id, db)
    comment = Comment(
        text=body.text,
        user=user,
        photo=photo
    )

    db.add(comment)
    db.commit()
    db.refresh(comment)

    return comment


async def update_comment(body: CommentUpdate, user: User, db: Session) -> Comment | None:
    """Docstring"""
    comment = db.query(Comment).filter(Comment.id == body.id).first()

    if comment:
        if user.id == comment.user_id:
            comment.text = body.text
            db.commit()
        else:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=messages.FORBIDDEN)

    return comment


async def delete_comment(body: CommentDelete, db: Session) -> Comment | None:
    """Docstring"""
    comment = db.query(Comment).filter(Comment.id == body.id).first()

    if comment:
        db.delete(comment)
        db.commit()

    return comment
