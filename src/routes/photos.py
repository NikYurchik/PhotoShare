import cloudinary
import re
import qrcode

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_

from src.database.db import get_db
from src.database.models import User, Photo, PhotoURL, Role
from src.repository import photos as repository_photo
from src.services.auth import auth_service
from src.schemas import PhotoResponse, PhotoTransformModel
from src.conf.config import settings
from src.conf import messages

router = APIRouter(prefix="/photos", tags=["photos"])


@router.post("/transform/{photo_id})", response_model=PhotoResponse)
async def photo_transform(body: PhotoTransformModel, photo_id: int,
                          user: User = Depends(auth_service.get_current_user), db: Session = Depends(get_db)):

    if user.roles == Role.admin:
        photo = db.query(Photo).filter(Photo.id == photo_id).first()
    else:
        if Photo.user_id == user.id:
            photo = db.query(Photo).filter(and_(Photo.id == photo_id, Photo.user_id == user.id)).first()
        else:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=messages.OPERATION_NOT_AVAILABLE)

    if photo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.PHOTO_NOT_FOUND)

    cloudinary.config(cloud_name=settings.cloudinary_name,
                      api_key=settings.cloudinary_api_key,
                      api_secret=settings.cloudinary_api_secret,
                      secure=True)

    if body.effect is None:
        url_changed_photo = cloudinary.CloudinaryImage(f"{photo.file_url}").build_url(transformation=[
            {'gravity': body.gravity, 'height': body.height, 'width': body.width, 'crop': body.crop},
            {'radius': body.radius},
            {'quality': body.quality},
            {'fetch_format': body.fetch_format if body.fetch_format else re.search("\w+$", photo.file_url).group(0)}
        ])
    else:
        url_changed_photo = cloudinary.CloudinaryImage(f"{photo.file_url}").build_url(transformation=[
            {'gravity': body.gravity, 'height': body.height, 'width': body.width, 'crop': body.crop},
            {'radius': body.radius},
            {'effect': body.effect},
            {'quality': body.quality},
            {'fetch_format': body.fetch_format if body.fetch_format else re.search("\w+$", photo.file_url).group(0)}
        ])

    return await repository_photo.photo_transform(url_changed_photo, photo, db)


# @router.post("/qrcode/{photo_id}/{photo_url_id})", response_model=PhotoResponse)
# async def photo_transform(photo_id: int, photo_url_id: int | None = None,
#                           user: User = Depends(auth_service.get_current_user), db: Session = Depends(get_db)):
#
#     if user.roles == Role.admin:
#         photo = db.query(Photo).filter(Photo.id == photo_id).first()
#     else:
#         if Photo.user_id == user.id:
#             photo = db.query(Photo).filter(and_(Photo.id == photo_id, Photo.user_id == user.id)).first()
#         else:
#             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=messages.OPERATION_NOT_AVAILABLE)
#
#     if photo is None:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.PHOTO_NOT_FOUND)
#
#     if photo_url_id is None:
#         qr_url_photo = photo.file_url
#     else:
#         photo_url = db.query(PhotoURL).filter(and_(PhotoURL.photo_id == photo_id, PhotoURL.id == photo_url_id)).first()
#         qr_url_photo = photo_url.url
#
#     qr = qrcode.QRCode()
#
#     qr.add_data(qr_url_photo)
#
#     img = qr.make_image()
#     # img.save("some_file.png")
#
#     return await repository_photo.qrcode_for_photo(img, photo, db)
