import enum

from sqlalchemy import Column, Integer, String, DateTime, func, event, UniqueConstraint, Boolean, Enum
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql.schema import ForeignKey, Table

Base = declarative_base()

tag_photo_association_table = Table(
    'tag_m2m_photo',
    Base.metadata,
    Column('tag_id', Integer, ForeignKey('tags.id')),
    Column('photo_id', Integer, ForeignKey('photos.id'))
)


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
    created_at = Column('created_at', DateTime, default=func.now())
    avatar = Column(String(255), nullable=True)
    refresh_token = Column(String(255), nullable=True)
    confirmed = Column(Boolean, default=False)
    roles = Column('roles', Enum(Role), default=Role.user)
    is_banned = Column(Boolean, default=False)


class Photo(Base):
    __tablename__ = "photos"
    id = Column(Integer, primary_key=True)
    photo_user_id = Column(Integer, ForeignKey('users.id'))
    photo_file_url = Column(String, nullable=False, unique=True)
    photo_description = Column(String, nullable=True)
    created_at = Column('created_at', DateTime, default=func.now())
    updated_at = Column('updated_at', DateTime, default=func.now())
    user = relationship('User', backref='photos')


class Tag(Base):
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True)
    tag_name = Column(String, nullable=False, unique=True)


class PhotoURL(Base):
    __tablename__ = "photo_urls"
    id = Column(Integer, primary_key=True)
    url = Column(String, nullable=False, unique=True)
    url_photo_id = Column(Integer, ForeignKey("photos.id"))
    created_at = Column('created_at', DateTime, default=func.now())
    photo = relationship('Photo', backref='urls')


class Comment(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True)
    comment_user_id = Column(Integer, ForeignKey('users.id'))
    comment_photo_id = Column(Integer, ForeignKey('photos.id'))
    comment_text = Column(String(500), nullable=False)
    created_at = Column('created_at', DateTime, default=func.now())
    updated_at = Column('updated_at', DateTime, default=func.now())
    photo = relationship('Photo', backref='comments')
    user = relationship('User', backref='comments')
