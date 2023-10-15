from sqlalchemy.orm import Session

from src.database.models import User, Photo, PhotoURL


async def photo_transform(url_changed_photo: str, photo: Photo, db: Session) -> Photo:

    new_photo = PhotoURL(url=url_changed_photo, photo=photo)
    db.add(new_photo)
    db.commit()
    db.refresh(new_photo)

    return new_photo

