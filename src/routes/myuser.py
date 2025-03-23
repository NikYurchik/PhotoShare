from fastapi import APIRouter, Depends, UploadFile, File, Request, Response, status, responses
from sqlalchemy import func
from sqlalchemy.orm import Session

from src.base import app, templates
from src.conf import messages
from src.database.db import get_db
from src.database.models import User, Photo
from src.repository import users as repository_users
from src.repository.auth import Auth as repository_auth
from src.services.auth import auth_service
from src.schemas import UserDb, UserDbResponse, UserResponse
from src.services.cloud_image import CloudImage
from src.services.custom_json import Jsons


router = APIRouter(prefix="", tags=["myuser"])


@router.get("/", response_model=UserDbResponse)
async def read_users_me(request: Request,
                        # current_user: User = Depends(auth_service.get_current_user),
                        db: Session = Depends(get_db)):
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
    current_user = await repository_auth().check_authentication(request=request, db=db)
    if current_user:
        return templates.TemplateResponse("auth/profile.html", {"request": request,
                                                                "title": messages.CONTACTS_APP, 
                                                                "user": app.extra["user"]})
    return responses.RedirectResponse("/",
                                      status_code=status.HTTP_302_FOUND)



@router.patch('/', response_model=UserResponse)
async def update_avatar_user(request: Request,
                             file: UploadFile = File(),
                            #  current_user: User = Depends(auth_service.get_current_user),
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
    current_user = await repository_auth().check_authentication(request=request, db=db)
    if current_user:
        if current_user.avatar:
            # print(f">>> current_user.avatar: {current_user.avatar}")
            result = CloudImage.delete_image(current_user.avatar)
            # if result:
            #     print(f"Update_Avatar_User: {result}")

        src_url = CloudImage.upload_image(photo_file=file.file, user=current_user, folder=f"avatar/{current_user.username}")
        user = await repository_users.update_avatar(current_user, src_url, db)
        app.extra["user"].update({"avatar": src_url})
        # result = await repository_users.get_user_info(user.id, db)
        # return result
        return {"user": app.extra["user"], "detail": {"success": [{"key": "reload", "value": "/"}]}}

    return responses.RedirectResponse("/",
                                      status_code=status.HTTP_302_FOUND)

