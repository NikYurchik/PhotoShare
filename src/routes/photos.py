from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.orm import Session
from sqlalchemy import and_

from src.database.db import get_db
from src.database.models import User, Photo, PhotoURL, Role
from src.repository import PhotosRepository
from src.services.auth import auth_service
from src.services.roles import RoleAccess
from src.schemas import PhotoResponse, PhotoTransformModel, PhotoQRCodeModel
from src.conf import messages


allowed_operation_all = RoleAccess([Role.admin, Role.moderator, Role.user])
allowed_operation_notuser = RoleAccess([Role.admin, Role.moderator])
allowed_operation_admin = RoleAccess([Role.admin])

router = APIRouter(prefix="/photos", tags=["photos"])


@router.post("/transform/{photo_id}",
             response_model=PhotoResponse,
             description=messages.NO_MORE_THAN_10_REQUESTS_PER_MINUTE,
             dependencies=[Depends(allowed_operation_all), Depends(RateLimiter(times=10, seconds=60))])
async def photo_transform(body: PhotoTransformModel, photo_id: int,
                          user: User = Depends(auth_service.get_current_user), db: Session = Depends(get_db)):

    base_photo = db.query(Photo).filter(Photo.id == photo_id).first()

    if base_photo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.PHOTO_NOT_FOUND)

    if user.roles != Role.admin and base_photo.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=messages.OPERATION_NOT_AVAILABLE)

    if body.transform_photo_id:
        try:
            transform_photo_id = int(body.transform_photo_id)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"Invalid value of the 'transform_photo_id' parameter: "
                                       f"'{body.transform_photo_id}'. It must have a numeric value.")

        photo = db.query(PhotoURL).filter(and_(PhotoURL.photo_id == photo_id,
                                               PhotoURL.id == transform_photo_id)).first()

        if photo is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.PHOTO_NOT_FOUND)
    else:
        photo = base_photo

    return await PhotosRepository().upload_transform_photo(body, base_photo, photo, db)


@router.post("/qrcode/{photo_id}",
             response_model=PhotoResponse,
             description=messages.NO_MORE_THAN_10_REQUESTS_PER_MINUTE,
             dependencies=[Depends(allowed_operation_all), Depends(RateLimiter(times=10, seconds=60))])
async def create_qrcode(body: PhotoQRCodeModel, photo_id: int,
                        user: User = Depends(auth_service.get_current_user), db: Session = Depends(get_db)):

    base_photo = db.query(Photo).filter(Photo.id == photo_id).first()

    if base_photo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.PHOTO_NOT_FOUND)

    if user.roles == Role.user and base_photo.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=messages.OPERATION_NOT_AVAILABLE)

    if body.transform_photo_id:
        try:
            transform_photo_id = int(body.transform_photo_id)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"Invalid value of the 'transform_photo_id' parameter: "
                                       f"'{body.transform_photo_id}'. It must have a numeric value.")

        photo = db.query(PhotoURL).filter(and_(PhotoURL.photo_id == photo_id,
                                               PhotoURL.id == transform_photo_id)).first()

        if photo is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.PHOTO_NOT_FOUND)
    else:
        photo = base_photo

    return await PhotosRepository().update_photo_qr_url(body, photo, db)


@router.delete("/del_tr_photo/{transform_photo_id}",
               description=messages.NO_MORE_THAN_10_REQUESTS_PER_MINUTE,
               dependencies=[Depends(allowed_operation_all), Depends(RateLimiter(times=10, seconds=60))])
async def delete_transform_photo(transform_photo_id: int,
                                 user: User = Depends(auth_service.get_current_user), db: Session = Depends(get_db)):

    photo = db.query(PhotoURL).filter(PhotoURL.id == transform_photo_id).first()

    if photo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.PHOTO_NOT_FOUND)

    base_photo = db.query(Photo).filter(Photo.id == photo.photo_id).first()

    if base_photo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.PHOTO_NOT_FOUND)

    if user.roles == Role.user and base_photo.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=messages.OPERATION_NOT_AVAILABLE)

    return await PhotosRepository().delete_transform_photo(photo, db)

