import cloudinary
import cloudinary.uploader
import re
import qrcode
import aiofiles.os

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import delete

from src.database.models import User, Photo, PhotoURL
from src.schemas import PhotoTransformModel, PhotoQRCodeModel
from src.conf.config import settings


class PhotosRepository:
    async def upload_transform_photo(self, body: PhotoTransformModel, base_photo: Photo, photo: PhotoURL,
                                     db: Session) -> Photo:

        cloudinary.config(cloud_name=settings.cloudinary_name,
                          api_key=settings.cloudinary_api_key,
                          api_secret=settings.cloudinary_api_secret,
                          secure=True)

        public_id = re.search(r"/v\d+/(.+)\.\w+$", photo.file_url).group(1)

        url_changed_photo = cloudinary.CloudinaryImage(f"{public_id}").build_url(transformation=[
            {'gravity': body.gravity, 'height': body.height, 'width': body.width, 'crop': body.crop},
            {'radius': body.radius},
            {'effect': body.effect} if body.effect else None,
            {'quality': body.quality},
            {'fetch_format': body.fetch_format if body.fetch_format else re.search(r"\w+$", photo.file_url).group(0)}
        ])

        new_photo = PhotoURL(file_url=url_changed_photo, photo=base_photo)
        db.add(new_photo)
        db.commit()
        db.refresh(new_photo)

        return new_photo

    async def update_photo_qr_url(self, body: PhotoQRCodeModel, photo: Photo | PhotoURL,
                                  db: Session) -> Photo | PhotoURL:

        cloudinary.config(cloud_name=settings.cloudinary_name,
                          api_key=settings.cloudinary_api_key,
                          api_secret=settings.cloudinary_api_secret,
                          secure=True)

        if photo.qr_url:
            return await photo

        qr_name = f"c{photo.id}" if body.transform_photo_id else f"b{photo.id}"
        qr_extension = "png"

        qr_os_folder = "../../temp_qr_photo"
        qr_os_path = f"{qr_os_folder}/{qr_name}.{qr_extension}"

        qr_ci_folder = "PhotoShare/qr"

        if not await aiofiles.os.path.exists(qr_os_folder):
            await aiofiles.os.mkdir(qr_os_folder)

        qr = qrcode.QRCode()
        qr.add_data(photo.file_url)
        qr.make(fit=True)

        img = qr.make_image(fill_color=body.fill_color, back_color=body.back_color)
        img.save(qr_os_path)

        result = cloudinary.uploader.upload(
            qr_os_path,
            folder=qr_ci_folder,
            resource_type="image",
            public_id=f"{qr_name}"
        )

        await aiofiles.os.remove(qr_os_path)

        photo.qr_url = result['url']
        db.commit()

        return photo

    async def delete_transform_photo(self, photo: PhotoURL, db: Session) -> None:

        db.delete(photo)

        cloudinary.config(cloud_name=settings.cloudinary_name,
                          api_key=settings.cloudinary_api_key,
                          api_secret=settings.cloudinary_api_secret,
                          secure=True)

        public_id = re.search(r"/v\d+/(.+)\.\w+$", photo.file_url).group(1)
        result = cloudinary.uploader.destroy(public_id)

        if result.get('result') != 'ok':
            db.rollback()
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=result.get('message'))

        db.commit()

    async def delete_all_transform_photo(self, photo: Photo, db: Session) -> None:

        photos_to_del = db.query(PhotoURL).filter(PhotoURL.photo_id == photo.id).all()

        query = delete(PhotoURL).where(PhotoURL.photo_id == photo.id)
        db.execute(query)

        cloudinary.config(cloud_name=settings.cloudinary_name,
                          api_key=settings.cloudinary_api_key,
                          api_secret=settings.cloudinary_api_secret,
                          secure=True)

        for one_photo in photos_to_del:
            public_id = re.search(r"/v\d+/(.+)\.\w+$", one_photo.file_url).group(1)
            result = cloudinary.uploader.destroy(public_id)

            if result.get('result') != 'ok':
                db.rollback()
                raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=result.get('message'))

        db.commit()

