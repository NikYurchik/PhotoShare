from typing import List

from fastapi import APIRouter, Depends, UploadFile, File, Form, Query
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.database.models import User, Role
from src.repository.photos import PhotosRepository
from src.schemas import PhotoResponse, PhotoUpdateModel, PhotoSchema
from src.services.auth import auth_service
from src.services.validators import Validator
from src.services.roles import RoleAccess

allowed_operation = RoleAccess([Role.admin, Role.user])

router = APIRouter(prefix="/photos", tags=["photos"])


# @router.get('/all-photos', response_model=List[PhotoResponse])
@router.get('/all', response_model=List[PhotoResponse])
async def get_all_photos(page: int = 1,
                         per_page: int = 10,
                         db: Session = Depends(get_db)):
    return await PhotosRepository().get_all_photos(page, per_page, db)


@router.get('/user/{user_id}', response_model=List[PhotoResponse])
async def get_photo_by_user(user_id: int,
                            page: int = 1,
                            per_page: int = 10,
                            current_user: User = Depends(auth_service.get_current_user),
                            db: Session = Depends(get_db)):
    return await PhotosRepository().get_photos_by_user(user_id, current_user, page, per_page, db)


@router.get('/search', response_model=List[PhotoResponse])
async def search_photos(
        keyword: str = Query(None, description="Keyword to search in photo descriptions"),
        tag: str = Query(None, description="Filter photos by tag"),
        order_by: str = Query("newest", description="Sort order date(newest, or oldest"),
        db: Session = Depends(get_db)):
    photos = await PhotosRepository().search_photos(keyword, tag, order_by, db)
    return photos


@router.post('/new', status_code=201, response_model=PhotoResponse, dependencies=[Depends(allowed_operation)])
async def upload_photo(photo: UploadFile = File(...),
                       photo_description: str = Form(...),
                       tags: str = Query(None, description="Tags string separated by commas"),
                       current_user: User = Depends(auth_service.get_current_user),
                       db: Session = Depends(get_db)):
    tags_list = await Validator().validate_tags_count(tags)
    print(f"tags: {tags}")
    print(f"tags_list: {tags_list}")
    return await PhotosRepository().upload_new_photo(photo_description, tags_list, photo, current_user, db)


@router.put('/{photo_id}', response_model=PhotoSchema, dependencies=[Depends(allowed_operation)])
async def update_photo_description(photo_id: int,
                                   body: PhotoUpdateModel,
                                   user_id: int = None,
                                   current_user: User = Depends(auth_service.get_current_user),
                                   db: Session = Depends(get_db)):
    return await PhotosRepository().update_photo_description(user_id, photo_id, body, current_user, db)


@router.delete('/{photo_id}', status_code=204, dependencies=[Depends(allowed_operation)])
async def delete_photo(photo_id: int,
                       user_id: int = None,
                       current_user: User = Depends(auth_service.get_current_user),
                       db: Session = Depends(get_db)):
    return await PhotosRepository().delete_photo(user_id, photo_id, current_user, db)


@router.get('/single/{photo_id}', response_model=PhotoResponse, dependencies=[Depends(allowed_operation)])
async def get_photo_by_id(photo_id: int,
                          user_id: int = None,
                          current_user: User = Depends(auth_service.get_current_user),
                          db: Session = Depends(get_db)):
    return await PhotosRepository().get_photo_by_id(photo_id, current_user, db)


