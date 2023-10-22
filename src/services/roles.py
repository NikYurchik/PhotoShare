from typing import List

from fastapi import Depends, HTTPException, status, Request

from src.database.models import User, Role
from src.services.auth import auth_service
from src.conf import messages


class RoleAccess:
    def __init__(self, allowed_roles: List[Role]):
        self.allowed_roles = allowed_roles

    async def __call__(self, request: Request, current_user: User = Depends(auth_service.get_current_user)):
        # print(request.method, request.url)
        # print(f'User role {current_user.roles}')
        # print(f'Allowed roles: {self.allowed_roles}')
        if current_user.roles not in self.allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=messages.OPERATION_NOT_AVAILABLE)


# У відповідних модулях папки routes:
#
# from src.services.roles import RoleAccess
#
# allowed_operation_get = RoleAccess([Role.admin, Role.moderator, Role.user])
# allowed_operation_create = RoleAccess([Role.admin, Role.moderator, Role.user])
# allowed_operation_update = RoleAccess([Role.admin, Role.moderator])
# allowed_operation_remove = RoleAccess([Role.admin])
#
#
# @router.get("/", response_model=List[CatResponse],
#             dependencies=[Depends(allowed_operation_get), Depends(RateLimiter(times=2, seconds=5))])
