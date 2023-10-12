from libgravatar import Gravatar
from sqlalchemy.orm import Session

from src.database.models import User
from src.schemas import UserModel


async def get_user_by_email(email: str, db: Session) -> User:
    """
    The get_user_by_email function takes in an email and a database session, then returns the user with that email.
    
    :param email: str: Pass in the email address of the user
    :param db: Session: Pass the database session to the function
    :return: The user object
    :doc-author: Python-WEB13-project-team-2
    """
    return db.query(User).filter(User.email == email).first()


async def create_user(body: UserModel, db: Session) -> User:
    """
    The create_user function creates a new user in the database.
        Args:
            - body (UserModel): The UserModel object containing the data to be inserted into the database.\n
            - db (Session): The SQLAlchemy Session object used to interact with the database.
        Returns:
            - User: A newly created user from the database.
    
    :param body: UserModel: Create a new user based on the usermodel schema
    :param db: Session: Create a new database session
    :return: A user object
    :doc-author: Python-WEB13-project-team-2
    """
    avatar = None
    try:
        g = Gravatar(body.email)
        avatar = g.get_image()
    except Exception as err:
        print(err)
    # new_user = User(**body.dict(), avatar=avatar)
    new_user = User(username=body.username, email=body.email, password=body.password, avatar=avatar)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


async def update_token(user: User, token: str | None, db: Session) -> None:
    """
    The update_token function updates the refresh token for a user.
    
    :param user: User: Identify the user in the database
    :param token: str | None: Specify the type of token
    :param db: Session: Commit the changes to the database
    :return: Nothing, so the return type should be none
    :doc-author: Python-WEB13-project-team-2
    """
    user.refresh_token = token
    db.commit()


async def confirmed_email(email: str, db: Session) -> None:
    """
    The confirmed_email function sets the confirmed field of a user to True.
    
    :param email: str: Get the email of the user
    :param db: Session: Access the database
    :return: None, which is not a valid return type
    :doc-author: Python-WEB13-project-team-2
    """
    user = await get_user_by_email(email, db)
    user.confirmed = True
    db.commit()


async def update_avatar(email, url: str, db: Session) -> User:
    """
    The update_avatar function updates the avatar of a user.
    
    Args:
        - email (str): The email address of the user to update.\n
        - url (str): The URL for the new avatar image.\n
        - db (Session, optional): A database session object to use instead of creating one locally. Defaults to None.  # noQA: E501 line too long
    
    :param email: Get the user from the database
    :param url: str: Specify that the url parameter is a string
    :param db: Session: Pass the database session to the function
    :return: A user object
    :doc-author: Python-WEB13-project-team-2
    """
    user = await get_user_by_email(email, db)
    user.avatar = url
    db.commit()
    return user

