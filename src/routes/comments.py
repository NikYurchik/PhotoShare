from typing import List

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi_limiter.depends import RateLimiter  # add custom limiter
from sqlalchemy.orm import Session

from src.schemas import CommentModel, CommentUpdate, CommentDelete, CommentResponse
from src.conf import messages
from src.repository import comments as repository_comments
from src.database.db import get_db
from src.database.models import User, Role
from src.services.auth import auth_service
from src.services.roles import RoleAccess


router = APIRouter(prefix='/comments', tags=['comments'])

allowed_operation_delete = RoleAccess([Role.admin, Role.moderator])


@router.get('/{photo_id}', response_model=List[CommentResponse])
async def get_comments(photo_id: int, db: Session = Depends(get_db)):
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
    comment = await repository_comments.create_comment(photo_id, body, user, db)

    return comment


@router.put('/', response_model=CommentResponse)
async def update_comment(body: CommentUpdate,
                         user: User = Depends(auth_service.get_current_user),
                         db: Session = Depends(get_db)):
    comment = await repository_comments.update_comment(body, user, db)

    if comment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.NOT_FOUND)

    return comment


@router.delete('/', response_model=CommentResponse, dependencies=[
                                                                Depends(allowed_operation_delete),
                                                                Depends(RateLimiter(times=2, seconds=5))])
async def delete_comment(body: CommentDelete,
                         db: Session = Depends(get_db)):
    comment = await repository_comments.delete_comment(body, db)

    if comment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.NOT_FOUND)

    return comment
