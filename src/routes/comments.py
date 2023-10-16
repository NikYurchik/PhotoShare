from typing import List

from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.schemas import CommentModel, CommentUpdate, CommentDelete, CommentResponse
from src.conf import messages
from src.repository import comments as repository_comments
from src.database.models import Comment, User, Photo
from src.services.auth import auth_service


router = APIRouter(prefix='/comments', tags=['comments'])


@router.get('/{photo_id}', response_model=List[CommentResponse])
async def get_comments(photo_id: int, db: Session = Depends(get_db)):
    """Docstring"""
    comments = await repository_comments.get_comments(photo_id, db)

    if len(comments) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=messages.NOT_FOUND)

    return comments


@router.post('/{photo_id}', response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(photo_id: int,
                         body: CommentModel,
                         user: User = Depends(auth_service.get_current_user),
                         db: Session = Depends(get_db)):
    """Docstring"""
    comment = await repository_comments.create_comment(photo_id, body, user, db)

    return comment


@router.put('/', response_model=CommentResponse)
async def update_comment(body: CommentUpdate,
                         user: User = Depends(auth_service.get_current_user),
                         db: Session = Depends(get_db)):
    """Docstring"""
    comment = await repository_comments.update_comment(body, user, db)

    if comment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.NOT_FOUND)

    return comment


@router.delete('/', response_model=CommentResponse)
async def delete_comment(body: CommentDelete,
                         user: User = Depends(auth_service.get_current_user),
                         db: Session = Depends(get_db)):
    """Docstring"""
    comment = await repository_comments.delete_comment(body, user, db)

    if comment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.NOT_FOUND)

    return comment
