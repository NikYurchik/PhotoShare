from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.database.models import User, Role
from src.repository import users as repository_users
from src.services.auth import auth_service
from src.schemas import UserDb
from src.services.cloud_image import CloudImage
from src.services.roles import RoleAccess

# NULL_DATE = datetime.now().replace(month=1, day=1)

allowed_operation_get = RoleAccess([Role.admin, Role.moderator, Role.user])
allowed_operation_create = RoleAccess([Role.admin, Role.moderator, Role.user])
allowed_operation_update = RoleAccess([Role.admin, Role.moderator])
allowed_operation_remove = RoleAccess([Role.admin])

router = APIRouter(prefix="/myuser", tags=["myuser"])


@router.get("/me/", response_model=UserDb)
async def read_users_me(current_user: User = Depends(auth_service.get_current_user)):
    """
    The read_users_me function returns the current user's information.
        get:
            - tags: [users] # This is a tag that can be used to group operations by resources or any other qualifier.
            - summary: Returns the current user's information.
            - description: Returns the current user's information based on their JWT token in their request header.
            - responses: # The possible responses this operation can return, along with descriptions and examples of each response type (if applicable).
                '200':  # HTTP status code 200 indicates success! In this case, it means we successfully returned a User
    
    :param current_user: User: Get the current user from the database
    :return: The current user object, which is passed as a parameter to the function
    :doc-author: Python-WEB13-project-team-2
    """
    print(f"read_users_me: ")
    return current_user


@router.patch('/avatar', response_model=UserDb)
async def update_avatar_user(file: UploadFile = File(),
                             current_user: User = Depends(auth_service.get_current_user),
                             db: Session = Depends(get_db)):
    """
    The update_avatar_user function updates the avatar of a user.
        Args:
            - file (UploadFile): The image to be uploaded.
            - current_user (User): The user whose avatar is being updated.
            - db (Session): A database session for interacting with the database.
    
    :param file: UploadFile: Get the file from the request
    :param current_user: User: Get the user that is currently logged in
    :param db: Session: Pass the database session to the repository layer
    :return: A user object
    :doc-author: Python-WEB13-project-team-2
    """
    # print(f"content_type: {file.content_type}")
    # print(f"headers: {file.headers}")
    # print(f"filename: {file.filename}")
    # print(f"size: {file.size}")
    # print(f"file: {file.file}")
    public_id = CloudImage.generate_name_avatar(current_user.email)
    r = CloudImage.upload(file.file, public_id)
    src_url = CloudImage.get_url_for_avatar(public_id, r)
    user = await repository_users.update_avatar(current_user, src_url, db)
    return user

