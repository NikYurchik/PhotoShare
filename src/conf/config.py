from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    postgres_db: str = 'example'
    postgres_user: str = 'db_user'
    postgres_password: str = 'db_password'
    postgres_host: str = 'localhost'
    postgres_port: int = '5432'
    sqlalchemy_database_url: str = 'postgresql+psycopg2://user:password@localhost:5432/example'
    secret_key: str = 'secret_key'
    algorithm: str = 'HSxxx'
    mail_username: str = 'example@meta.ua'
    mail_password: str = 'metaPassword'
    mail_from: str = 'example@meta.ua'
    mail_port: int = 465
    mail_server: str = 'smtp.meta.ua'
    redis_host: str = 'localhost'
    redis_port: int = 6379
    redis_password: None = None
    cloudinary_name: str = 'example'
    cloudinary_api_key: str = 'api_key'
    cloudinary_api_secret: str = 'api_secret'

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
