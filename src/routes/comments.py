from typing import List

from fastapi import APIRouter, HTTPException, Depends, status
# from fastapi_limiter.depends import RateLimiter
from sqlalchemy.orm import Session

from src.schemas import CommentModel, CommentUpdate, CommentDelete, CommentResponse
from src.conf import messages
from src.repository import comments as repository_comments
from src.database.db import get_db
from src.database.models import User, UserRole
from src.services.auth import auth_service
from src.services.roles import RoleAccess
from src.services.custom_limiter import RateLimiter
from src.routes.photos import router

# router = APIRouter(prefix='/', tags=['comments'])

allowed_operation_nouser = RoleAccess([UserRole.admin, UserRole.moderator])


@router.get('/{photo_id}/comments/', response_model=List[CommentResponse])
async def get_comments(photo_id: int, db: Session = Depends(get_db)):
    comments = await repository_comments.get_comments(photo_id, db)

    # if len(comments) == 0:
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND, detail=messages.NOT_FOUND)

    return comments


@router.post('/{photo_id}/comments/', response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(photo_id: int,
                         body: CommentModel,
                         user: User = Depends(auth_service.get_current_user),
                         db: Session = Depends(get_db)):
    comment = await repository_comments.create_comment(photo_id, body, user, db)

    return comment


@router.put('/{photo_id}/comments/{comment_id}', response_model=CommentResponse,
                dependencies=[Depends(allowed_operation_nouser), Depends(RateLimiter(times=10, seconds=60))])
async def update_comment(photo_id: int,
                         comment_id: int,
                         body: CommentModel,
                         user: User = Depends(auth_service.get_current_user),
                         db: Session = Depends(get_db)):
    comment = await repository_comments.update_comment(photo_id, comment_id, body, user, db)

    # if comment is None:
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.NOT_FOUND)

    return comment


@router.delete('/{photo_id}/comments/{comment_id}', #response_model=CommentResponse,
                status_code=204,
                dependencies=[Depends(allowed_operation_nouser), Depends(RateLimiter(times=10, seconds=60))])
async def delete_comment(photo_id: int,
                         comment_id: int,
                         user: User = Depends(auth_service.get_current_user),
                         db: Session = Depends(get_db)):
    comment = await repository_comments.delete_comment(photo_id, comment_id, user, db)

    # if comment is None:
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.NOT_FOUND)

    return comment
