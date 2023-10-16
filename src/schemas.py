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


