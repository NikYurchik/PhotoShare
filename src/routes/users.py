from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Request, Response, responses
# from fastapi_limiter.depends import RateLimiter
from sqlalchemy.orm import Session

from src.base import app, templates
from src.database.db import get_db
from src.database.models import User, UserRole
from src.repository import users as repository_users
from src.repository.auth import Auth as repository_auth
from src.services.auth import auth_service
from src.schemas import UserDbAdmin, UserAdminResponse
from src.services.roles import RoleAccess
from src.conf import messages
from src.services.custom_limiter import RateLimiter
from src.services.custom_json import Jsons

allowed_operation_all = RoleAccess([UserRole.admin, UserRole.moderator, UserRole.user])
allowed_operation_notuser = RoleAccess([UserRole.admin, UserRole.moderator])
allowed_operation_admin = RoleAccess([UserRole.admin])

router = APIRouter(prefix="", tags=["users"])


@router.get("/",
            response_model=List[UserDbAdmin],
            description=messages.NO_MORE_THAN_10_REQUESTS_PER_MINUTE,
            dependencies=[Depends(allowed_operation_notuser), Depends(RateLimiter(times=10, seconds=60))])
async def get_users(request: Request,
                    page: int = Query(1, description="Page number"),
                    per_page: int = Query(10, le=50, description="Items per page"),
                    # limit: int = Query(10, le=50), 
                    # offset: int = 0, 
                    search_mask: str = '',
                    # current_user: User = Depends(auth_service.get_current_user),
                    db: Session = Depends(get_db)):

    current_user = await repository_auth().check_authentication(request=request, db=db)
    if current_user:
        if not search_mask or search_mask == '*':
            # print('Get all users')
            users, pages = await repository_users.get_users(per_page, page, db)
        else:
            # print(f'Search users by mask "{search_mask}"')
            users, pages = await repository_users.get_users_by_mask(per_page, page, search_mask, db)
        return templates.TemplateResponse("users/users.html", {"request": request,
                                                                "title": messages.CONTACTS_APP, 
                                                                "user": app.extra["user"],
                                                                "roles": UserRole,
                                                                "users": Jsons.list_useradminresponse_to_json(users),
                                                                "pages": pages})
    return responses.RedirectResponse("/",
                                      status_code=status.HTTP_302_FOUND)


@router.get("/{user_id}",
            response_model=UserDbAdmin,
            description=messages.NO_MORE_THAN_10_REQUESTS_PER_MINUTE,
            dependencies=[Depends(allowed_operation_notuser), Depends(RateLimiter(times=10, seconds=60))])
async def get_user(request: Request,
                   user_id: int = Path(ge=1),
                #    current_user: User = Depends(auth_service.get_current_user),
                   db: Session = Depends(get_db)):

    current_user = await repository_auth().check_authentication(request=request, db=db)
    if current_user:
        user = await repository_users.get_user_by_id(user_id, db)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.NOT_FOUND)
        return templates.TemplateResponse("users/user.html", {"request": request,
                                                              "title": messages.CONTACTS_APP, 
                                                              "user": app.extra["user"],
                                                              "roles": UserRole,
                                                              "user1": Jsons.useradminresponse_to_json(user)})
    return responses.RedirectResponse("/",
                                      status_code=status.HTTP_302_FOUND)


@router.patch('/{user_id}/toggle_ban',
              response_model=UserAdminResponse,
              description=messages.NO_MORE_THAN_10_REQUESTS_PER_MINUTE,
              dependencies=[Depends(allowed_operation_notuser), Depends(RateLimiter(times=10, seconds=60))])
async def toogle_banned_user(request: Request,
                             user_id: int = Path(ge=1),
                            #  current_user: User = Depends(auth_service.get_current_user),
                             db: Session = Depends(get_db)):
    # print(f">>> toggle_ban user_id: {user_id}")
    current_user = await repository_auth().check_authentication(request=request, db=db)
    if current_user:
        user = await repository_users.get_user_by_id(user_id, db)
        if user is None:
            # print(f">>> toggle_ban user {user_id} is None")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.NOT_FOUND)
        elif user.id == current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=messages.FORBIDDEN)

        user = await repository_users.toggle_banned_user(user_id, db)
        msg = messages.USER_BLOCKED if user.is_banned else messages.USER_UNBLOCKED
        return {"user": Jsons.useradminresponse_to_json(user), "detail": {"success": [{"key": "message", "value": msg},
                                                                                      {"key": "reload", "value": "/"}]}}
    return responses.RedirectResponse("/",
                                      status_code=status.HTTP_302_FOUND)


@router.patch('/{user_id}/set_roles',
              response_model=UserAdminResponse,
              description=messages.NO_MORE_THAN_10_REQUESTS_PER_MINUTE,
              dependencies=[Depends(allowed_operation_notuser), Depends(RateLimiter(times=10, seconds=60))])
async def set_roles_user(request: Request,
                         user_id: int = Path(ge=1),
                         user_roles: str = 'user',
                        #  current_user: User = Depends(auth_service.get_current_user),
                         db: Session = Depends(get_db)):
    # print(f">>> user_id: {user_id}, new_roles: {user_roles}")
    current_user = await repository_auth().check_authentication(request=request, db=db)
    if current_user:
        user = await repository_users.get_user_by_id(user_id, db)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.NOT_FOUND)
        elif user.id == current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=messages.FORBIDDEN)

        user = await repository_users.set_roles_user(user_id, user_roles, db)
        return {"user": Jsons.useradminresponse_to_json(user), "detail": {"success": [{"key": "reload", "value": "/"}]}}

    return responses.RedirectResponse("/",
                                      status_code=status.HTTP_302_FOUND)

