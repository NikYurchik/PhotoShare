from typing import Optional
from datetime import datetime, date

from pydantic import BaseModel, Field, EmailStr

from src.database.models import Role


class UserModel(BaseModel):
    username: str = Field(min_length=5, max_length=16)
    email: EmailStr
    password: str = Field(min_length=6, max_length=10)


class UserDb(BaseModel):
    id: int
    username: str
    email: EmailStr
    created_at: Optional[datetime] = datetime.now()
    # created_at: datetime = datetime.now()
    avatar: Optional[str] = None
    # avatar: str = None
    roles: Role

    class Config:
        from_attributes = True


class UserDbAdmin(UserDb):
    confirmed: bool
    is_banned: bool

class UserResponse(BaseModel):
    user: UserDb
    detail: str = "User successfully created"


class TokenModel(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RequestEmail(BaseModel):
    email: EmailStr

