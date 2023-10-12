from fastapi import HTTPException, status
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from src.conf.config import settings


username = settings.postgres_user
password = settings.postgres_password
domain = settings.postgres_db
port = settings.postgres_port
database = settings.postgres_db
URL = settings.sqlalchemy_database_url

engine = create_engine(URL, echo=True)
DBSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)


# Dependency
def get_db():
    """
    The get_db function is a context manager that will automatically close the database connection when it goes out of scope.
        It also handles any exceptions that occur within the with block, rolling back any changes to the database and closing the connection before re-raising them.
    
    :return: A context manager that can be used to get a database connection
    :doc-author: Python-WEB13-project-team-2
    """
    db = DBSession()
    try:
        yield db
    except SQLAlchemyError as err:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))
    finally:
        db.close()
