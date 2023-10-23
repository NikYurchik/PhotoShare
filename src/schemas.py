from typing import Optional
from datetime import datetime, date
from typing import Optional, List, Dict
import json

from pydantic import BaseModel, Field, EmailStr, model_validator, constr

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
    avatar: Optional[str] = None
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
    qr_url:  Optional[str]
    description: Optional[str]
    created_at: datetime
    user_id: int


class PhotoUpdateModel(BaseModel):
    description: str


class PhotoNewModel(BaseModel):
    description: str
    tag_str: Optional[str]
    tags: Optional[List[str]]

    @model_validator(mode='before')
    @classmethod
    def validate_to_json(cls, value):
        if isinstance(value, str):
            return cls(**json.loads(value))
        return value


class PhotoSearchModel(BaseModel):
    keyword: Optional[str] = None
    tag: Optional[str] = None
    order_by: Optional[str] = None


class TagDetail(BaseModel):
    id: int
    name: str


class PhotoAddTagsModel(BaseModel):
    tag_str: Optional[str]
    tags: Optional[List[str]]


class PhotoResponse(BaseModel):
    photo: PhotoSchema
    tags: Optional[List[TagDetail]]

    class Config:
        from_attributes = True


class CommentModel(BaseModel):
    text: str


class CommentUpdate(BaseModel):
    id: int
    text: str


class CommentDelete(BaseModel):
    id: int


class CommentResponse(BaseModel):
    id: int
    text: str

    class Config:
        from_attributes = True


class PhotoURLModel(BaseModel):
    file_url: str
    qr_url: Optional[str]
    photo_id: int
    created_at: datetime


class PhotoURLResponse(PhotoURLModel):
    id: int

    class Config:
        from_attributes = True


class PhotoTransformModel(BaseModel):
    # transform_photo_id: str | None = None
    gravity: str | None = "center"      # условный центр изображения
    height: str | None = "800"          # высота изображения
    width: str | None = "800"           # ширина изображения
    crop: str | None = "fill"           # Режим обрезки
    radius: str | None = "0"            # радиус закругления углов
    effect: str | None = None           # Эффекты и улучшения изображений
    quality: str | None = "auto"        # % потери качества при сжатии
    fetch_format: str | None = None     # Преобразование фото в определенный формат


class PhotoQRCodeModel(BaseModel):
    fill_color: str | None = "black"
    back_color: str | None = "white"


class PhotoTransQRCodeModel(PhotoQRCodeModel):
    transform_photo_id: str | None = None
