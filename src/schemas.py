from typing import Optional
from datetime import datetime, date
from typing import Optional, List, Dict
import json

from pydantic import BaseModel, Field, EmailStr, model_validator, constr

from src.database.models import UserRole


class UserModel(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    password2: Optional[str] = None


class UserModelFix(BaseModel):
    username: str = Field(min_length=4, max_length=16)
    email: EmailStr
    password: str = Field(min_length=6, max_length=12)
    password2: str = Field(min_length=6, max_length=12)


class LoginModel(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None


class LoginResponse(LoginModel):
    is_authenticated: Optional[bool] = False
    detail: Optional[Dict] = {"message": "Login successful"}


class UserDb(BaseModel):
    id: Optional[int]
    username: Optional[str]
    email: Optional[EmailStr]
    created_at: Optional[datetime] = datetime.now()
    avatar: Optional[str] = None
    roles: UserRole = UserRole.user
    is_authenticated: Optional[bool] = False

    class Config:
        from_attributes = True


class UserDbResponse(UserDb):
    photo_count: Optional[int] = 0


class UserDbAdmin(UserDbResponse):
    confirmed: bool
    is_banned: bool


class UserResponse(BaseModel):
    user: UserDbResponse
    detail: Optional[Dict] = {"message": "User successfully created/changed"}


class UserAdminResponse(BaseModel):
    user: UserDbAdmin
    detail: Optional[Dict] = {"message": "User successfully changed"}


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
    username: str


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


class TagsModel(BaseModel):
    tags: Optional[List[TagDetail]]


class PhotoAddTagsModel(BaseModel):
    tag_str: Optional[str]
    tags: Optional[List[str]]

    @model_validator(mode='before')
    @classmethod
    def validate_to_json(cls, value):
        # print(f">>> value: {value}")
        if isinstance(value, str):
            return cls(**json.loads(value))
        return value


class CommentModel(BaseModel):
    text: str


class CommentUpdate(BaseModel):
    id: int
    text: str


class CommentDelete(BaseModel):
    id: int


class CommentDB(BaseModel):
    id: int
    text: str
    user_id: int
    username: str

    class Config:
        from_attributes = True


class CommentResponse(BaseModel):
    comment: CommentDB
    detail: Optional[Dict] = {"reload": ""}


class PhotoURLModel(BaseModel):
    file_url: str
    qr_url: Optional[str]
    params: Optional[str]          # Dictionary of Params
    photo_id: int
    created_at: datetime


class PhotoURLResponse(PhotoURLModel):
    id: int

    class Config:
        from_attributes = True


class PhotoTransformModel(BaseModel):
    height: Optional[str] | None = None         # высота изображения
    width: Optional[str] | None = None          # ширина изображения
    crop: Optional[str] | None = None           # Режим обрезки
    gravity: Optional[str] | None = None        # условный центр изображения
    radius: Optional[str] | None = None         # радиус закругления углов
    fetch_format: Optional[str] | None = None   # Преобразование фото в определенный формат
    effect: Optional[str] | None = None         # Эффекты и улучшения изображений
    quality: Optional[str] | None = None        # % потери качества при сжатии
    angle: Optional[str] | None = None          # угол поворота

    @model_validator(mode='before')
    @classmethod
    def validate_to_json(cls, value):
        # print(f">>> value: {value}")
        if isinstance(value, str):
            return cls(**json.loads(value))
        return value


class PhotoQRCodeModel(BaseModel):
    fill_color: str | None = "black"
    back_color: str | None = "white"


class PhotoTransQRCodeModel(PhotoQRCodeModel):
    transform_photo_id: str | None = None


class PhotoResponse(BaseModel):
    photo: PhotoSchema
    tags: Optional[List[TagDetail]]
    comments: Optional[List[CommentDB]]

    class Config:
        from_attributes = True


class PhotoExtResponse(BaseModel):
    photo: Optional[PhotoResponse] | None = None
    detail: Optional[Dict] = {"message": "Photo successfully create"}


# class SuccessResponse(BaseModel):
#     success:  Optional[List[Dict]]

# class ErrorsResponse(BaseModel):
#     errors:  Optional[List[Dict]]

class DetailResponse(BaseModel):
    detail: Optional[Dict] = {"success": [{"key": "string", "value": "string"}], "errors": [{"key": "string", "value": "string"}]}

class PhotoURLupdateResponse(PhotoURLResponse):
    detail: Optional[Dict] = {"success": [{"key": "string", "value": "string"}], "errors": [{"key": "string", "value": "string"}]}
