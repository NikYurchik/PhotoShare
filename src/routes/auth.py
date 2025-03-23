from fastapi import APIRouter, HTTPException, Depends, status, Security, BackgroundTasks, Request, Response, responses
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials, HTTPBearer
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from src.base import app, templates
from src.database.db import get_db
from src.database.models import User
from src.schemas import UserModel, UserResponse, TokenModel, LoginModel, LoginResponse, RequestEmail, UserDb
from src.repository import users as repository_users
from src.repository.auth import Auth as repository_auth
from src.services.auth import auth_service
from src.services.email import send_email
from src.services.custom_limiter import RateLimiter
from src.services.custom_json import Jsons
from src.conf import messages
from src.routes.forms.signup_form import UserCreateForm
from src.routes.forms.login_form import LoginForm

router = APIRouter(prefix='', tags=["auth"])
security = HTTPBearer()


@router.get("/signup", response_class=HTMLResponse, description="Sign Up", dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def register(request: Request):
    return templates.TemplateResponse("auth/signup.html", {"request": request,
                                                           "title": messages.CONTACTS_APP, 
                                                           "user": app.extra["user"]})


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(body: UserModel,
                 background_tasks: BackgroundTasks, 
                 request: Request, 
                 db: Session = Depends(get_db)):
    """
    The signup function creates a new user in the database.
        - It also sends an email to the user's email address for confirmation.
        - The function returns a JSON object containing the newly created user and a message.
    
    :param body: UserModel: Get the user's email and password
    :param background_tasks: BackgroundTasks: Add a task to the background tasks queue
    :param request: Request: Get the base url of the application
    :param db: Session: Get the database session
    :return: A dictionary with two keys, user and detail
    :doc-author: Python-WEB13-project-team-2
    """
    form = UserCreateForm(body)
    user = UserDb(username=form.username, email=form.email, id=0)
    if not await form.is_valid():
        return {"user": user, "detail": {"errors": form.errors}}
    
    exist_user = await repository_users.get_user_by_email(body.email, db)
    if exist_user:
        return {"user": user, "detail": {"errors": [{"key": "username", "value": messages.ACCOUNT_ALREADY_EXISTS}]}}
    
    body.password = auth_service.get_password_hash(body.password)
    new_user = await repository_users.create_user(body, db)
    background_tasks.add_task(send_email, new_user.email, new_user.username, request.base_url)
    
    return {"user": new_user, "detail": {"success": [{"key": "message", "value": messages.USER_SUCCESSFULLY_CREATED_CHECK_YOUR_EMAIL_FOR_CONFIRMATION},
                                                     {"key": "redirect", "value": "/"}]}}


# @router.post("/login", response_model=TokenModel)
@router.post("/login", response_model=LoginResponse)
async def login_user(request: Request,
                     response: Response, 
                     body: LoginModel, 
                     db: Session = Depends(get_db)):
    """
    The login function is used to authenticate a user.
    
    :param body: OAuth2PasswordRequestForm: Get the username and password from the body of the request
    :param db: Session: Get the database session
    :return: An access token and a refresh token
    :doc-author: Python-WEB13-project-team-2
    """
    # print(f">>> username: {body.username}, password: {body.password}")
    form = LoginForm(body)
    if not await form.is_valid():
        return {"user": form.user, "detail": {"errors": form.errors}}

    user = await repository_users.get_user_by_email(body.username, db)
    if user is None:
        return {"user": form.user, "detail": {"errors": {"key": "message", "value": messages.INVALID_EMAIL}}}
    
    if not user.confirmed:
        return {"user": Jsons.userresponse_to_json(user), "detail": {"errors": {"key": "message", "value": messages.EMAIL_NOT_CONFIRMED}}}
    
    if user.is_banned:
        return {"user": Jsons.userresponse_to_json(user), "detail": {"errors": {"key": "message", "value": messages.YOU_ARE_BANNED}}}
    
    if not auth_service.verify_password(body.password, user.password):
        return {"user": Jsons.userresponse_to_json(user), "detail": {"errors": {"key": "message", "value": messages.INVALID_PASSWORD}}}
    
    # Generate JWT
    access_token = await auth_service.create_access_token(data={"sub": user.email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": user.email})
    await repository_users.update_token(user, refresh_token, db)
    response.set_cookie(key="atuser",value=f"Bearer {access_token}", httponly=True)  #set HttpOnly cookie in response
    response.set_cookie(key="rtuser",value=f"Bearer {refresh_token}", httponly=True)  #set HttpOnly cookie in response

    user = await repository_users.get_user_by_id(user.id, db)
    log_user = Jsons.userresponse_to_json(user=user, auth=True)
    app.extra.update({"user": log_user})

    return {"user": app.extra["user"], "detail": {"success": [{"key": "message", "value": messages.LOGIN_SUCCESSFUL},
                                                              {"key": "access_token", "value": f"Bearer {access_token}"},
                                                              {"key": "refresh_token", "value": f"Bearer {refresh_token}"},
                                                              {"key": "reload", "value": "/"}]}}


@router.post("/logout")
async def logout_user(request: Request,
                      response: Response, 
                      db: Session = Depends(get_db)):
    message = ""
    check_auth = repository_auth()
    current_user = await check_auth.check_authentication(request=request, db=db, is_logout=True)
    if not current_user and len(check_auth.errors) > 0:
        message = check_auth.errors[0]["value"]
        return {"detail": {"errors": [{"key": "error-msg", "value": message}]}}
    else:
        response.delete_cookie(key="atuser")
        response.delete_cookie(key="rtuser")
        return {"detail": {"success": [{"key": "reload", "value": ""}]}}


@router.get('/refresh_token', response_model=TokenModel)
async def refresh_token(request: Request, credentials: HTTPAuthorizationCredentials = Security(security), db: Session = Depends(get_db)):
    """
    The refresh_token function is used to refresh the access token.
        It takes in a refresh token and returns a new access_token, refresh_token, and token type.
    
    
    :param credentials: HTTPAuthorizationCredentials: Get the token from the authorization header
    :param db: Session: Get the database session
    :return: A dictionary with the access_token, refresh_token and token type
    :doc-author: Python-WEB13-project-team-2
    """
    token = credentials.credentials
    email = await auth_service.decode_refresh_token(token)
    user = await repository_users.get_user_by_email(email, db)
    if user.refresh_token != token:
        await repository_users.update_token(user, None, db)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=messages.INVALID_REFRESH_TOKEN)

    access_token = await auth_service.create_access_token(data={"sub": email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": email})
    await repository_users.update_token(user, refresh_token, db)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.get('/confirmed_email/{token}')
async def confirmed_email(request: Request, token: str, db: Session = Depends(get_db)):
    """
    The confirmed_email function is used to confirm a user's email address.
        - It takes the token from the URL and uses it to get the user's email address.
        - Then, it checks if that user exists in our database, and if they do not exist, 
            an error message is returned. If they do exist but their email has already been confirmed,
            another message is returned saying so. Otherwise (if they exist and their email has not yet been confirmed),
            we call repository_users' confirmed_email function with that user's email as a parameter.
    
    :param token: str: Get the token from the url
    :param db: Session: Access the database
    :return: A dict with a message
    :doc-author: Python-WEB13-project-team-2
    """
    response_dict = {"request": request,
                     "title": messages.CONTACTS_APP,
                     "user": app.extra["user"]}
    errors = {}
    try:
        email = auth_service.get_email_from_token(token)
        user = await repository_users.get_user_by_email(email, db)
        if user is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=messages.VERIFICATION_ERROR)
        
        message = messages.EMAIL_CONFIRMED
        if user.confirmed:
            message = messages.YOUR_EMAIL_IS_ALREADY_CONFIRMED
        else:
            await repository_users.confirmed_email(email, db)
        response_dict.update({"message": message})

    except HTTPException as err:
        response_dict.update({"errors": [{"key": "message", "value": err.detail}]})

    return templates.TemplateResponse("auth/email_confirmed.html", response_dict)


@router.post('/request_email')
async def request_email(body: RequestEmail, background_tasks: BackgroundTasks, request: Request,
                        db: Session = Depends(get_db)):
    """
    The request_email function is used to send an email to the user with a link that will allow them
    to confirm their email address. The function takes in a RequestEmail object, which contains the
    user's email address. It then checks if there is already a user with that email address in the database, and if so, whether or not they have confirmed their account yet. If they have not confirmed it yet (or there isn't even an account associated with this email), then we add another task to our background_tasks queue: sending an actual confirmation message via SendGrid.
    
    :param body: RequestEmail: Get the email from the request body
    :param background_tasks: BackgroundTasks: Add a task to the background tasks queue
    :param request: Request: Get the base url of the application
    :param db: Session: Pass the database session to the repository_users
    :return: A message: check your email for confirmation
    :doc-author: Python-WEB13-project-team-2
    """
    user = await repository_users.get_user_by_email(body.email, db)

    if user and user.confirmed:
        return {"message": messages.YOUR_EMAIL_IS_ALREADY_CONFIRMED}
    if user:
        background_tasks.add_task(send_email, user.email, user.username, request.base_url)
    return {"message": messages.CHECK_YOUR_EMAIL_FOR_CONFIRMATION}


