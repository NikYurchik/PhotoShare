from typing import List

from fastapi import HTTPException, Depends, Request
from fastapi.security.utils import get_authorization_scheme_param
from sqlalchemy.orm import Session

from src.base import app
from src.database.models import User
from src.repository import users as repository_users
from src.services.auth import auth_service
from src.services.custom_json import Jsons

class Auth:
    def __init__(self):
        self.errors: List = []

    async def check_authentication(self, request: Request, db: Session, is_logout: bool=False) -> User | None:
        self.errors = []
        # print(f">>> check_authentication: cookies={request.cookies}")
        token = request.cookies.get("atuser")
        # print(f">>> check_authentication: access_token={token}")
        scheme, param = get_authorization_scheme_param(token)  # scheme will hold "Bearer" and param will hold actual token value
        # print(f">>> check_authentication: scheme={scheme}, param={param}")
        current_user = None
        try:
            current_user = await auth_service.get_current_user(token=param, db=db)
            # print(f">>> check_authentication: current_user.id={current_user}")
            if not is_logout:
                log_user = Jsons.userresponse_to_json(user=current_user, auth=True)
                # print(f">>> check_authentication: current_user={log_user}")
                app.extra.update({"user": log_user})
                return current_user
        
        except HTTPException as err:
            if not is_logout:
                # print(f">>> check_authentication: HTTPException = {err.detail}")
                self.errors.append({"key": "message", "value": err.detail})

            user = app.extra["user"]
            email = user.get("email")
            if email:
                try:
                    current_user = await repository_users.get_user_by_email(email, db)
                    # print(f">>> check_authentication: get_user_by_email = {current_user}")
                except Exception as e:
                    # print(f">>> check_authentication: Exception = {e}")
                    pass

        if current_user:
            current_user.refresh_token = None
            db.commit
            # print(f">>> check_authentication: refresh_token = None")
        
        app.extra.pop("user")
        app.extra.update({"user": {"is_authenticated": False}})
        # app.extra["user"].update({"is_authenticated": False})
        # print(f">>> check_authentication: is_authenticated = False")

        return None
