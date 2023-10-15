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
    created_at: datetime
    avatar: str
    roles: Role

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    user: UserDb
    detail: str = "User successfully created"


class TokenModel(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RequestEmail(BaseModel):
    email: EmailStr


class PhotoModel(BaseModel):
    user_id: int
    file_url: str
    description: str
    created_at: datetime


class PhotoUpdate(BaseModel):
    description: str


class PhotoResponse(PhotoModel):
    id: int
    # user_id: int
    # file_url: str
    # description: str
    # created_at: datetime

    class Config:
        from_attributes = True


class PhotoURLModel(BaseModel):
    url: str
    photo_id: int
    created_at: datetime


class PhotoURLResponse(PhotoURLModel):
    id: int

    class Config:
        from_attributes = True


class PhotoTransformModel(BaseModel):
    gravity: str | None = "center"
    height: str | None = "800"
    width: str | None = "800"
    crop: str | None = "fill"
    radius: str | None = "0"
    effect: str | None = None
    quality: str | None = "auto"
    fetch_format: str | None = None
    # fetch_format: str | None = "png"

