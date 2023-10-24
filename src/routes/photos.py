from typing import List, Optional

from fastapi import APIRouter, Depends, UploadFile, File, Body, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_

from src.database.db import get_db
from src.database.models import User, UserRole, Photo, PhotoURL
from src.repository.photos import PhotosRepository
from src.schemas import PhotoResponse, PhotoUpdateModel, PhotoNewModel, PhotoTransformModel, \
                        PhotoQRCodeModel, PhotoURLResponse, PhotoTransQRCodeModel, PhotoSearchModel, \
                        PhotoAddTagsModel
from src.services.auth import auth_service
from src.services.validators import Validator
from src.services.roles import RoleAccess
from src.services.custom_limiter import RateLimiter
from src.conf import messages

allowed_operation_all = RoleAccess([UserRole.admin, UserRole.moderator, UserRole.user])
# allowed_operation = RoleAccess([UserRole.admin, UserRole.user])

router = APIRouter(prefix="", tags=["photos"])


@router.get('/', response_model=List[PhotoResponse])
async def get_and_search_photos(
        user_id: int = Query(None, description="Filter by user"),
        keyword: str = Query(None, description="Keyword to search in photo descriptions"),
        tag: str = Query(None, description="Filter photos by tag"),
        order_by: str = Query("newest", description="Sort order date(newest, or oldest"),
        # body: PhotoSearchModel,
        db: Session = Depends(get_db)):
    photos = await PhotosRepository().search_photos(db, user_id, keyword, tag, order_by)
    return photos


# @router.get('/', response_model=List[PhotoResponse])
# async def get_all_photos(page: int = 1,
#                          per_page: int = 10,
#                          db: Session = Depends(get_db)):
#     return await PhotosRepository().get_all_photos(page, per_page, db)


# @router.get('/user/{user_id}', response_model=List[PhotoResponse])
# async def get_photo_by_user(user_id: int,
#                             page: int = 1,
#                             per_page: int = 10,
#                             current_user: User = Depends(auth_service.get_current_user),
#                             db: Session = Depends(get_db)):
#     return await PhotosRepository().get_photos_by_user(user_id, current_user, page, per_page, db)


@router.get('/{photo_id}', response_model=PhotoResponse, dependencies=[Depends(allowed_operation_all)])
async def get_photo_by_id(photo_id: int,
                          current_user: User = Depends(auth_service.get_current_user),
                          db: Session = Depends(get_db)):
    return await PhotosRepository().get_photo_by_id(photo_id, current_user, db)


@router.post('/', status_code=201, response_model=PhotoResponse, dependencies=[Depends(allowed_operation_all)])
async def upload_photo(body: PhotoNewModel = Body(...),
                       photo_file: UploadFile = File(...),
                       current_user: User = Depends(auth_service.get_current_user),
                       db: Session = Depends(get_db)):
    tags_list = await Validator().validate_tags_count(body.tag_str, body.tags)

    return await PhotosRepository().upload_new_photo(body.description, tags_list, photo_file, current_user, db)


@router.post('/{photo_id}/add-tags', response_model=PhotoResponse, dependencies=[Depends(allowed_operation_all)])
async def add_tag_to_photo(photo_id: int,
                           body: PhotoAddTagsModel,
                           current_user: User = Depends(auth_service.get_current_user),
                           db: Session = Depends(get_db)):
    tags_list = await Validator().validate_tags_count(body.tag_str, body.tags)
    return await PhotosRepository().add_tag_to_photo(tags_list, photo_id, current_user, db)


@router.post('/{photo_id}/remove-tag', response_model=PhotoResponse, dependencies=[Depends(allowed_operation_all)])
async def add_tag_to_photo(photo_id: int,
                           tag: str,
                           current_user: User = Depends(auth_service.get_current_user),
                           db: Session = Depends(get_db)):
    return await PhotosRepository().remove_tag_from_photo(tag, photo_id, current_user, db)


@router.put('/{photo_id}', response_model=PhotoResponse, dependencies=[Depends(allowed_operation_all)])
async def update_photo_description(photo_id: int,
                                   body: PhotoUpdateModel,
                                   current_user: User = Depends(auth_service.get_current_user),
                                   db: Session = Depends(get_db)):
    return await PhotosRepository().update_photo_description(photo_id, body.description, current_user, db)


@router.delete('/{photo_id}', status_code=204, dependencies=[Depends(allowed_operation_all)])
async def delete_photo(photo_id: int,
                       current_user: User = Depends(auth_service.get_current_user),
                       db: Session = Depends(get_db)):
    return await PhotosRepository().delete_photo(photo_id, current_user, db)


@router.post("/{photo_id}/transform",
             response_model=PhotoURLResponse,
             description=messages.NO_MORE_THAN_10_REQUESTS_PER_MINUTE,
             dependencies=[Depends(allowed_operation_all), Depends(RateLimiter(times=10, seconds=60))])
async def photo_transform(body: PhotoTransformModel, photo_id: int,
                          user: User = Depends(auth_service.get_current_user), db: Session = Depends(get_db)):

    base_photo = db.query(Photo).filter(Photo.id == photo_id).first()

    if base_photo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.PHOTO_NOT_FOUND)

    if base_photo.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=messages.OPERATION_NOT_AVAILABLE)

    return await PhotosRepository().upload_transform_photo(body, base_photo, db)


@router.post("/{photo_id}/qrcode",
             response_model=PhotoResponse,
             description=messages.NO_MORE_THAN_10_REQUESTS_PER_MINUTE,
             dependencies=[Depends(allowed_operation_all), Depends(RateLimiter(times=10, seconds=60))])
async def create_qrcode(body: PhotoQRCodeModel, photo_id: int,
                        user: User = Depends(auth_service.get_current_user), db: Session = Depends(get_db)):

    base_photo = db.query(Photo).filter(Photo.id == photo_id).first()

    if base_photo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.PHOTO_NOT_FOUND)

    if user.roles == UserRole.user and base_photo.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=messages.OPERATION_NOT_AVAILABLE)

    return await PhotosRepository().update_photo_qr_url(body, base_photo, db)


@router.post("/{photo_id}/qrcode/{transform_photo_id}",
             response_model=PhotoURLResponse,
             description=messages.NO_MORE_THAN_10_REQUESTS_PER_MINUTE,
             dependencies=[Depends(allowed_operation_all), Depends(RateLimiter(times=10, seconds=60))])
async def create_trans_qrcode(body: PhotoQRCodeModel, photo_id: int, transform_photo_id: int,
                              user: User = Depends(auth_service.get_current_user), db: Session = Depends(get_db)):

    base_photo = db.query(Photo).filter(Photo.id == photo_id).first()

    if base_photo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.PHOTO_NOT_FOUND)

    if user.roles == UserRole.user and base_photo.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=messages.OPERATION_NOT_AVAILABLE)

    if transform_photo_id:
        photo = db.query(PhotoURL).filter(and_(PhotoURL.photo_id == photo_id,
                                               PhotoURL.id == transform_photo_id)).first()
        if photo is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.TRANS_PHOTO_NOT_FOUND)
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=messages.TRANS_PHOTO_NOT_SPECIFIED)

    return await PhotosRepository().update_transphoto_qr_url(body, photo, db)


@router.delete("/{photo_id}/{transform_photo_id}",
               status_code=204,
               description=messages.NO_MORE_THAN_10_REQUESTS_PER_MINUTE,
               dependencies=[Depends(allowed_operation_all), Depends(RateLimiter(times=10, seconds=60))])
async def delete_transform_photo(photo_id: int,
                                 transform_photo_id: int,
                                 user: User = Depends(auth_service.get_current_user), db: Session = Depends(get_db)):

    photo = db.query(PhotoURL).filter(and_(Photo.id == photo_id, PhotoURL.id == transform_photo_id)).first()

    if photo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.TRANS_PHOTO_NOT_FOUND)

    base_photo = db.query(Photo).filter(Photo.id == photo.photo_id).first()

    if base_photo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.PHOTO_NOT_FOUND)

    if user.roles == UserRole.user and base_photo.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=messages.OPERATION_NOT_AVAILABLE)

    return await PhotosRepository().delete_transform_photo(photo, db)
