from typing import List

from sqlalchemy import and_
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from src.conf import messages
from src.schemas import CommentModel, CommentUpdate, CommentDelete
from src.database.models import Comment, User, Photo, UserRole


async def get_comments(photo_id: int, db: Session) -> List[Comment]:
    """
    Returns all comments associated with that photo.

    Args:
        photo_id (int): The id of the desired photo.
        db (Session): The database session.

    Returns:
        List[Comment]: A list of comments for a given photo_id
    """
    comments = db.query(Comment).filter(Comment.photo_id == photo_id).all()

    return comments  # noqa


async def create_comment(photo_id: int, body: CommentModel, user: User, db: Session) -> Comment:
    """
    Creates a new comment for a given photo.

    Args:
        photo_id (int): The id of the desired photo.
        body (CommentModel): The comment to be created.
        user (User): The user who is creating the comment.
        db (Session): The database session.

    Returns:
        Comment: The newly created comment.
    """
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if not photo:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=messages.PHOTO_NOT_FOUND)
    
    comment = Comment(
        text=body.text,
        user=user,
        photo=photo
    )

    db.add(comment)
    db.commit()
    db.refresh(comment)

    return comment


async def update_comment(photo_id: int, comment_id: int, body: CommentModel, user: User, db: Session) -> Comment | None:
    """
    Updates a comment.

    Args:
        body (CommentUpdate): The comment to be updated.
        user (User): The user who is updating the comment.
        db (Session): The database session.

    Returns:
        Comment | None: The updated comment, or None if the comment does not exist.
    """
    comment = db.query(Comment).filter(and_(Comment.photo_id == photo_id, Comment.id == comment_id)).first()

    if comment:
        if user.id == comment.user_id:
            comment.text = body.text
            db.commit()
        else:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=messages.OPERATION_NOT_AVAILABLE)
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.COMMENT_NOT_FOUND)

    return comment


async def delete_comment(photo_id: int, comment_id: int, user: User, db: Session) -> Comment | None:
    """
    Deletes a comment.

    Args:
        body (CommentDelete): The comment to be deleted.
        db (Session): The database session.

    Returns:
        Comment | None: The deleted comment, or None if the comment does not exist.
    """
    comment = db.query(Comment).filter(and_(Comment.photo_id == photo_id, Comment.id == comment_id)).first()

    if comment:
        if user.id == comment.user_id or user.roles in [UserRole.admin, UserRole.moderator]:
            db.delete(comment)
            db.commit()
        else:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=messages.OPERATION_NOT_AVAILABLE)
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.COMMENT_NOT_FOUND)


