from typing import Optional
from datetime import datetime, date
from typing import Optional, List

from pydantic import BaseModel, Field, EmailStr, field_validator, constr

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


class PhotoSchema(BaseModel):
    id: int
    file_url: str
    description: str
    created_at: datetime
    user_id: int


class PhotoUpdateModel(BaseModel):
    description: str


class TagDetail(BaseModel):
    id: int
    name: str


# class PhotoResponse(BaseModel):
#     photo: PhotoSchema
#     tags: List[TagDetail]

class PhotoResponse(PhotoSchema):
    tags: List[TagDetail]


