import enum

from sqlalchemy import Column, Integer, String, DateTime, func, event, UniqueConstraint, Boolean, Enum
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql.schema import ForeignKey, Table

Base = declarative_base()

class UserRole(enum.Enum):
    admin: str = 'admin'
    moderator: str = 'moderator'
    user: str = 'user'


class PrimaryKeyABC:
    id = Column(Integer, primary_key=True)

class CreatedABC:
    created_at = Column('created_at', DateTime, default=func.now())

class DateTimeABC(CreatedABC):
    updated_at = Column('updated_at', DateTime, default=func.now(), onupdate=func.now())


class User(Base, PrimaryKeyABC, CreatedABC):
    __tablename__ = "users"
    # id = Column(Integer, primary_key=True)
    username = Column(String(50))
    email = Column(String(250), nullable=False, unique=True)                   
    password = Column(String(255), nullable=False)
    # created_at = Column('created_at', DateTime, default=func.now())
    avatar = Column(String(255), nullable=True)
    refresh_token = Column(String(255), nullable=True)
    confirmed = Column(Boolean, default=False)
    roles = Column('roles', Enum(UserRole), default=UserRole.user)
    is_banned = Column(Boolean, default=False)


class Photo(Base, PrimaryKeyABC, DateTimeABC):
    __tablename__ = "photos"
    # id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    file_url = Column(String, nullable=False, unique=True)
    qr_url = Column(String(255), nullable=True, unique=True)
    description = Column(String, nullable=True)
    # created_at = Column('created_at', DateTime, default=func.now())
    # updated_at = Column('updated_at', DateTime, default=func.now(), onupdate=func.now())
    user = relationship('User', backref='photos')


class Tag(Base, PrimaryKeyABC, CreatedABC):
    __tablename__ = "tags"
    # id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)


tag_photo_association = Table(
    'tag_m2m_photo',
    Base.metadata,
    Column('tag_id', Integer, ForeignKey('tags.id', ondelete='CASCADE')),
    Column('photo_id', Integer, ForeignKey('photos.id', ondelete='CASCADE')),
    UniqueConstraint("tag_id", "photo_id", name="uq_tag_m2m_photo"),
 )

# class Tag2Photo(Base):
#     __tablename__ = "tag_m2m_photo"
#     id = Column(Integer, primary_key=True)
#     tag_id = Column(Integer, ForeignKey('tags.id', ondelete='CASCADE'))
#     photo_id = Column(Integer, ForeignKey('photos.id', ondelete='CASCADE'))
#     tag = relationship('Tag', backref='tags')
#     photo = relationship('Photo', backref='photos')


class PhotoURL(Base, PrimaryKeyABC, DateTimeABC):
    __tablename__ = "photo_urls"
    # id = Column(Integer, primary_key=True)
    file_url = Column(String, nullable=False, unique=True)
    qr_url = Column(String(255), nullable=True, unique=True)
    photo_id = Column(Integer, ForeignKey("photos.id", ondelete='CASCADE'))
    # created_at = Column('created_at', DateTime, default=func.now())
    photo = relationship('Photo', backref='photo_urls')


class Comment(Base, PrimaryKeyABC, DateTimeABC):
    __tablename__ = "comments"
    # id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    photo_id = Column(Integer, ForeignKey('photos.id', ondelete='CASCADE'))
    text = Column(String(500), nullable=False)
    # created_at = Column('created_at', DateTime, default=func.now())
    # updated_at = Column('updated_at', DateTime, default=func.now(), onupdate=func.now())
    photo = relationship('Photo', backref='comments')
    user = relationship('User', backref='comments')
