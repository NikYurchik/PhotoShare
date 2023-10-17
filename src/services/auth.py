from datetime import datetime, timedelta
from typing import Optional
import pickle

from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy.orm import Session
import redis


from src.database.db import get_db
from src.repository import users as repository_users
from src.conf.config import settings
from src.conf import messages

class Auth:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

    SECRET_KEY = settings.secret_key
    ALGORITHM = settings.algorithm
    r = redis.Redis(host=settings.redis_host, port=settings.redis_port, password=settings.redis_password, db=0)

    def verify_password(self, plain_password, hashed_password):
        """
        The verify_password function takes a plain-text password and the hashed version of that password,
            and returns True if they match, False otherwise. This is used to verify that the user's login
            credentials are correct.
        
        :param self: Represent the instance of the class
        :param plain_password: Check the password entered by the user
        :param hashed_password: Verify the plain_password parameter
        :return: True if the password is correct
        :doc-author: Python-WEB13-project-team-2
        """
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str):
        """
        The get_password_hash function takes a password as input and returns the hash of that password.
            The function uses the pwd_context object to generate a hash from the given password.
        
        :param self: Represent the instance of the class
        :param password: str: Get the password from the user
        :return: A hash of the password
        :doc-author: Python-WEB13-project-team-2
        """
        return self.pwd_context.hash(password)

    # define a function to generate a new access token
    async def create_access_token(self, data: dict, expires_delta: Optional[float] = None):
        """
        The create_access_token function creates a new access token for the user.
        
        :param self: Represent the instance of the class
        :param data: dict: Pass the data that will be encoded in the jwt
        :param expires_delta: Optional[float]: Set the expiration time of the access token
        :return: A jwt token
        :doc-author: Python-WEB13-project-team-2
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + timedelta(seconds=expires_delta)
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"iat": datetime.utcnow(), "exp": expire, "scope": "access_token"})
        encoded_access_token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encoded_access_token

    # define a function to generate a new refresh token
    async def create_refresh_token(self, data: dict, expires_delta: Optional[float] = None):
        """
        The create_refresh_token function creates a refresh token for the user.
            Args:
                - data (dict): A dictionary containing the user's id and username.
                - expires_delta (Optional[float]): The number of seconds until the refresh token expires. Defaults to None, which sets it to 7 days from now.
        
        :param self: Represent the instance of the class
        :param data: dict: Pass in the data that will be encoded into the token
        :param expires_delta: Optional[float]: Set the expiration time of the refresh token
        :doc-author: Python-WEB13-project-team-2
        :doc-author: Trelent
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + timedelta(seconds=expires_delta)
        else:
            expire = datetime.utcnow() + timedelta(days=7)
        to_encode.update({"iat": datetime.utcnow(), "exp": expire, "scope": "refresh_token"})
        encoded_refresh_token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encoded_refresh_token

    async def decode_refresh_token(self, refresh_token: str):
        """
        The decode_refresh_token function takes a refresh token and decodes it.
            - If the scope is 'refresh_token', then we return the email address of the user.
            - Otherwise, we raise an HTTPException with status code 401 (UNAUTHORIZED) and detail message 'Invalid scope for token'.
            - If there was a JWTError, then we also raise an HTTPException with status code 401 (UNAUTHORIZED) and detail message 'Could not validate credentials'.
        
        :param self: Represent the instance of the class
        :param refresh_token: str: Pass the refresh token to the function
        :return: The email of the user
        :doc-author: Python-WEB13-project-team-2
        """
        try:
            payload = jwt.decode(refresh_token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload['scope'] == 'refresh_token':
                email = payload['sub']
                return email
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=messages.INVALID_SCOPE_FOR_TOKEN)
        except JWTError as err:
            print(err)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=messages.COULD_NOT_VALIDATE_CREDENTIALS)

    async def get_current_user(self, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
        """
        The get_current_user function is a dependency that will be used in the UserController class.
            It takes in a token and db session as parameters, and returns the user object associated with
            the email address stored within the JWT token. If no user exists for that email address, or if 
            the JWT token is invalid, an HTTPException will be raised.
        
        :param self: Represent the instance of a class
        :param token: str: Get the token from the request header
        :param db: Session: Get the database session
        :return: A user object
        :doc-author: Python-WEB13-project-team-2
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=messages.COULD_NOT_VALIDATE_CREDENTIALS,
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            # Decode JWT
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload['scope'] == 'access_token':
                email = payload["sub"]
                if email is None:
                    raise credentials_exception
            else:
                raise credentials_exception
        except JWTError as e:
            raise credentials_exception

        user = self.r.get(f"user:{email}")
        if user is None:
            user = await repository_users.get_user_by_email(email, db)
            if user is None:
                raise credentials_exception
            self.r.set(f"user:{email}", pickle.dumps(user))
            self.r.expire(f"user:{email}", 900)
        else:
            user = pickle.loads(user)
        return user


    def create_email_token(self, data: dict):
        """
        The create_email_token function creates a token that is used to verify the user's email address.
            The token contains the following data:
                - iat (issued at): The time when the token was created.
                - exp (expiration): When this token expires, 7 days from now.
                - scope: What this JWT can be used for, in this case it is an email_token which means it can only be used to verify an email address.
        
        :param self: Represent the instance of the class
        :param data: dict: Create a copy of the data dictionary and add it to the token
        :return: A token
        :doc-author: Python-WEB13-project-team-2
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=7)
        to_encode.update({"iat": datetime.utcnow(), "exp": expire, "scope": "email_token"})
        token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return token


    def get_email_from_token(self, token: str):
        """
        The get_email_from_token function takes a token as an argument and returns the email address associated with that token.
            If the scope of the token is not 'email_token', then it raises an HTTPException. If there is a JWTError, then it also raises
            an HTTPException.
        
        :param self: Represent the instance of the class
        :param token: str: Pass in the token that is sent to the user's email
        :return: The email address of the user who is logged in
        :doc-author: Python-WEB13-project-team-2
        """
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload['scope'] == 'email_token':
                email = payload['sub']
                return email
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=messages.INVALID_SCOPE_FOR_TOKEN)
        except JWTError as e:
            print(e)
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail=messages.INVALID_TOKEN_FOR_EMAIL_VERIFICATION)


auth_service = Auth()

