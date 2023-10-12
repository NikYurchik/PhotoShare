import enum

from sqlalchemy import Column, Integer, String, DateTime, func, event, UniqueConstraint, Boolean, Enum
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql.schema import ForeignKey

Base = declarative_base()


class Role(enum.Enum):
    admin: str = 'admin'
    moderator: str = 'moderator'
    user: str = 'user'


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50))
    email = Column(String(250), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    created_at = Column('crated_at', DateTime, default=func.now())
    avatar = Column(String(255), nullable=True)
    refresh_token = Column(String(255), nullable=True)
    confirmed = Column(Boolean, default=False)
    roles = Column('roles', Enum(Role), default=Role.user)
    is_banned = Column(Boolean, default=False)


class Photo(Base):
    __tablename__ = "photos"
    id = Column(Integer, primary_key=True)
    photo_user_id = Column(Integer, ForeignKey('users.id'))
    photo_file_path = Column(String, nullable=False, unique=True)
    photo_description = Column(String, nullable=True)
    created_at = Column('created_at', DateTime, default=func.now())
    updated_at = Column('updated_at', DateTime, default=func.now())
    user = relationship('User', backref='photos')


class Tag(Base):
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True)
    tag_name = Column(String, nullable=False, unique=True)


class Photo_m2m_Tags(Base):
    __tablename__ = "photo_m2m_tags"
    photo_id = Column(Integer, ForeignKey('photos.id'))
    tag_id = Column(Integer, ForeignKey('tags.id'))


class PhotoURL(Base):
    __tablename__ = "photo_urls"
    id = Column(Integer, primary_key=True)
    url = Column(String, nullable=False, unique=True)
    url_photo_id = Column(Integer, ForeignKey("photos.id"))
    created_at = Column('created_at', DateTime, default=func.now())


class Comment(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True)
    comment_user_id = Column(Integer, ForeignKey('users.id'))
    comment_photo_id = Column(Integer, ForeignKey('photos.id'))
    comment_text = Column(String(500), nullable=False)
    created_at = Column('created_at', DateTime, default=func.now())
    updated_at = Column('updated_at', DateTime, default=func.now())
