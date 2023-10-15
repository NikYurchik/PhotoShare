import cloudinary
import re

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import and_

from src.database.db import get_db
from src.database.models import Photo, User
from src.repository import photos as repository_photo
from src.services.auth import auth_service
from src.schemas import PhotoResponse, PhotoTransformModel
from src.conf.config import settings

router = APIRouter(prefix="/photos", tags=["photos"])


@router.post("/transform/{photo_id})", response_model=PhotoResponse)
async def photo_transform(body: PhotoTransformModel, photo_id: int,
                          user: User = Depends(auth_service.get_current_user), db: Session = Depends(get_db)):

    photo = db.query(Photo).filter(and_(Photo.id == photo_id, Photo.user_id == user.id)).first()

    cloudinary.config(cloud_name=settings.cloudinary_name,
                      api_key=settings.cloudinary_api_key,
                      api_secret=settings.cloudinary_api_secret,
                      secure=True)

    if body.effect is None:
        url_changed_photo = cloudinary.CloudinaryImage(f"{photo.file_url}").build_url(transformation=[
            {'gravity': body.gravity, 'height': int(body.height), 'width': int(body.width), 'crop': body.crop},
            {'radius': int(body.radius)},
            {'quality': body.quality},
            {'fetch_format': body.fetch_format if body.fetch_format else re.search("\w+$", photo.file_url).group(0)}
        ])
    else:
        url_changed_photo = cloudinary.CloudinaryImage(f"{photo.file_url}").build_url(transformation=[
            {'gravity': body.gravity, 'height': int(body.height), 'width': int(body.width), 'crop': body.crop},
            {'radius': int(body.radius)},
            {'effect': body.effect},
            {'quality': body.quality},
            {'fetch_format': body.fetch_format if body.fetch_format else re.search("\w+$", photo.file_url).group(0)}
        ])

    changed_photo = await repository_photo.photo_transform(url_changed_photo, photo, db)

    return changed_photo

