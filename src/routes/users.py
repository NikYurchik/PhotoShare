from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
# from fastapi_limiter.depends import RateLimiter
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.database.models import User, Role
from src.repository import users as repository_users
from src.services.auth import auth_service
from src.schemas import UserDbAdmin
from src.services.roles import RoleAccess
from src.conf import messages
from src.services.custom_limiter import RateLimiter


allowed_operation_all = RoleAccess([Role.admin, Role.moderator, Role.user])
allowed_operation_notuser = RoleAccess([Role.admin, Role.moderator])
allowed_operation_admin = RoleAccess([Role.admin])

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/",
            response_model=List[UserDbAdmin],
            description=messages.NO_MORE_THAN_10_REQUESTS_PER_MINUTE,
            dependencies=[Depends(allowed_operation_notuser), Depends(RateLimiter(times=10, seconds=60))])
async def get_users(limit: int = Query(10, le=50), offset: int = 0, search_mask: str = '', db: Session = Depends(get_db),
                    current_user: User = Depends(auth_service.get_current_user)):
    if not search_mask or search_mask == '*':
        # print('Get all users')
        users = await repository_users.get_users(limit, offset, db)
    else:
        # print(f'Search users by mask "{search_mask}"')
        users = await repository_users.get_users_by_mask(limit, offset, search_mask, db)
    return users


@router.get("/{user_id}",
            response_model=UserDbAdmin,
            description=messages.NO_MORE_THAN_10_REQUESTS_PER_MINUTE,
            dependencies=[Depends(allowed_operation_notuser), Depends(RateLimiter(times=10, seconds=60))])
async def get_user(user_id: int = Path(ge=1), db: Session = Depends(get_db),
                   current_user: User = Depends(auth_service.get_current_user)):
    user = await repository_users.get_user_by_id(user_id, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.NOT_FOUND)
    return user


@router.patch('/toggle_ban/{user_id}',
              response_model=UserDbAdmin,
              description=messages.NO_MORE_THAN_10_REQUESTS_PER_MINUTE,
              dependencies=[Depends(allowed_operation_notuser), Depends(RateLimiter(times=10, seconds=60))])
async def toogle_banned_user(user_id: int = Path(ge=1),
                             current_user: User = Depends(auth_service.get_current_user),
                             db: Session = Depends(get_db)):
    # print(f"toggle_ban user_id: {user_id}")
    user = await repository_users.toggle_banned_user(user_id, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.NOT_FOUND)
    elif user.id == current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=messages.FORBIDDEN)
    return user


@router.patch('/set_roles/{user_id}',
              response_model=UserDbAdmin,
              description=messages.NO_MORE_THAN_10_REQUESTS_PER_MINUTE,
              dependencies=[Depends(allowed_operation_admin), Depends(RateLimiter(times=10, seconds=60))])
async def set_roles_user(user_id: int = Path(ge=1),
                         user_roles: str = 'user',
                         current_user: User = Depends(auth_service.get_current_user),
                         db: Session = Depends(get_db)):
    # print(f"toggle_ban user_id: {user_id}")
    user = await repository_users.set_roles_user(user_id, user_roles, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.NOT_FOUND)
    elif user.id == current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=messages.FORBIDDEN)
    return user

