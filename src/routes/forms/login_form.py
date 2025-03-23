from typing import List, Dict
from typing import Optional

from fastapi.security import OAuth2PasswordRequestForm
from pydantic import EmailStr

from src.schemas import LoginModel
from src.conf import messages

class LoginForm:
    def __init__(self, body: LoginModel):
        self.body: LoginModel = body
        self.errors: List = []
        self.username: Optional[str] = body.username
        self.password: Optional[str] = body.password
        self.user: Optional[Dict] = {"username": body.username, "password": body.password, "is_authenticated": False}

    async def is_valid(self):
        try:
            user = OAuth2PasswordRequestForm(username=self.username, password=self.password)
        except Exception as err:
            errors = str(err).split("\n")
            errors = errors[1::]        # Удаляем 1-ю строку
            for s in errors:
                if not s.startswith(" "):
                    key = s
                else:
                    s = s.strip()
                    if "For further information visit https://" not in s:
                        i = s.find(" [")
                        value = s[0:i].strip()
                    else:
                        self.errors.append({"key": key, "value": value})

        if not self.errors:
            return True
        return False
