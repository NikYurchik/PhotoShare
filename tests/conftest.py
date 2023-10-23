from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from src.database.models import Base
from src.database.db import get_db


SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module")
def session():
    # Create the database

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module")
def client(session):
    # Dependency override

    def override_get_db():
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db

    yield TestClient(app)


@pytest.fixture(scope="module")
def user():
    return {"username": "deadpool",
            "email": "deadpool@example.com",
            "password": "123456789",
            "roles": "admin",
            "is_banned": "False"
            }


@pytest.fixture(scope="module")
def photo_request():
    return {"description": "photo_description",
            # "tag_str": "tag1, tag2",
            # "tags": ["tags1", "tags2"]
            "tag_str": "",
            "tags": []
            }


@pytest.fixture(scope="module")
def photo():
    return {
                "photo": {
                    "id": 1,
                    "file_url": "https://res.cloudinary.com/dqglsxwms/image/upload/v1697427418/upload/vplnv9bplyylkvyomdgd.jpg",
                    "qr_url": "http://res.cloudinary.com/dqglsxwms/image/upload/v1697860722/upload/qr/b4.png",
                    "description": "photo_description",
                    "user_id": "1"
                },
                "tags": [
                    {
                        "name": "tags1"
                    },
                    {
                        "name": "tags2"
                    }
                ]
            }

@pytest.fixture(scope="module")
def photos():
    return [
                {
                    "photo": {
                        "user_id": "1",
                        "file_url": "https://res.cloudinary.com/dqglsxwms/image/upload/v1697427418/upload/vplnv9bplyylkvyomdgd.jpg",
                        "description": "Test photo"
                    },
                    "tags": [
                        {
                            "name": "tags1"
                        },
                        {
                            "name": "tags2"
                        }
                    ]
                },
                {
                    "photo": {
                        "user_id": "1",
                        "file_url": "https://res.cloudinary.com/dqglsxwms/image/upload/v1697769558/test1/j6fblr92rgf7oo6foyt9.jpg",
                        "description": "Test photo2"
                        },
                    "tags": [
                        {
                            "name": "tags2"
                        },
                        {
                            "name": "tags3"
                        }
                    ]
                }
            ]

# @pytest.fixture
# def log(request):
#     if not os.path.exists("logs"):
#         os.mkdir("logs")

#     with open(f"logs/{request.node.name}.log", mode="w", encoding="utf-8") as log:
#         yield log
# TestClient.get()
# TestClient.post()
# TestClient.put()
# TestClient.patch()
# TestClient.delete()

