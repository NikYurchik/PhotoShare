import re
# import ipaddress
from typing import Callable
import pathlib

import redis.asyncio as redis # noqa
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from fastapi.middleware.cors import CORSMiddleware

from src.database.db import get_db
from src.routes import auth, users, myuser, photos, comments
# from src.repository.users import check_user_admin
from src.conf.config import settings
from src.conf import messages

app = FastAPI()


@app.on_event("startup")
async def startup():
    """
    The startup function is called when the application starts up.
        It's a good place to initialize things that are needed by your app, like database connections or caches.
    
    :return: A redis connection pool
    """
    # await check_user_admin()
    r = await redis.Redis(host=settings.redis_host, port=settings.redis_port, password=settings.redis_password, db=0)
    await FastAPILimiter.init(r)


origins = [ 
    "http://localhost:8000/",
    "http://127.0.0.1:8000/",
    "http://0.0.0.0:8000/"
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router, prefix='/api')
app.include_router(users.router, prefix='/api')
app.include_router(photos.router, prefix='/api')
app.include_router(myuser.router, prefix='/api')
app.include_router(comments.router, prefix='/api')

templates = Jinja2Templates(directory='templates')
BASE_DIR = pathlib.Path(__file__).parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.mount("/htmlcov", StaticFiles(directory=BASE_DIR / "htmlcov"), name="htmlcov")


# ALLOWED_IPS = [
#     ipaddress.ip_address('0.0.0.0'),
#     ipaddress.ip_address("127.0.0.1"),
#     ipaddress.ip_address("108.63.249.204")
#     ]

user_agent_ban_list = [r"Python-urllib"]
# user_agent_ban_list = [r"Gecko", r"Python-urllib"]


# @app.middleware('http')
# async def custom_middleware(request: Request, call_next):
#     # print(f'request.base_url: {request.base_url}')
#     base_url = request.base_url
#     if base_url not in origins:
#         return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"detail": messages.NOT_ALLOWED_BASE_URL})
#     response = await call_next(request)
#     return response


# @app.middleware("http")
# async def limit_access_by_ip(request: Request, call_next: Callable):
#     """
#     The limit_access_by_ip function is a middleware function that limits access to the API by IP address.
#         It checks if the request's client host IP address is in ALLOWED_IPS, and if not, returns a 403 Forbidden response.
    
#     :param request: Request: Get the ip address of the client that is making a request
#     :param call_next: Callable: Call the next function in the pipeline
#     :return: A jsonresponse object, which contains the http status code and a message
    # :doc-author: Python-WEB13-project-team-2
#     """
#     try:
#         ip = ipaddress.ip_address(request.client.host)
#         if ip not in ALLOWED_IPS:
#             return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"detail": messages.NOT_ALLOWED_IP_ADDRESS})
#     except Exception as err:
#         print(f"ip_address error: {err}")
#     response = await call_next(request)
#     return response


@app.middleware("http")
async def user_agent_ban_middleware(request: Request, call_next: Callable):
    """
    The user_agent_ban_middleware function is a middleware function that checks the user-agent header of an incoming request.
        If the user-agent matches any of the patterns in `user_agent_ban_list`, then it returns a 403 Forbidden response.
        Otherwise, it calls call_next and returns its result.
    
    :param request: Request: Access the request object
    :param call_next: Callable: Pass the request to the next middleware in line
    :return: A jsonresponse object if the user agent matches a pattern in the user_agent_ban_list
    :doc-author: Python-WEB13-project-team-2
    """
    user_agent = request.headers.get("user-agent")
    # print(f'user_agent: {user_agent}')
    for ban_pattern in user_agent_ban_list:
        if re.search(ban_pattern, user_agent):
            return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"detail": messages.YOU_ARE_BANNED})
    response = await call_next(request)
    return response


@app.get("/", response_class=HTMLResponse, description="Main Page", dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def root(request: Request):
    """
    The root function is the entry point for the application.
        - It returns a TemplateResponse object, which renders an HTML template using Jinja2.
        - The template is located in templates/index.html and uses data from the request object to render itself.
    
    :param request: Request: Get the request object
    :return: A templateresponse object, which is a subclass of response
    :doc-author: Python-WEB13-project-team-2
    """
    return templates.TemplateResponse('index.html', {"request": request, "title": messages.CONTACTS_APP})


@app.get("/api/healthchecker")
def healthchecker(db: Session = Depends(get_db)):
    """
    The healthchecker function is used to check the health of the database.
        It will return a 200 status code if it can successfully connect to the database, and a 500 status code otherwise.
    
    :param db: Session: Pass the database session to the function
    :return: A dictionary with a message
    :doc-author: Python-WEB13-project-team-2
    """
    try:
        # Make request
        result = db.execute(text("SELECT 1")).fetchone()
        if result is None:
            raise HTTPException(status_code=500, detail=messages.DATABASE_IS_NOT_CONFIGURED_CORRECTLY)
        return {"message": messages.WELCOME_TO_FASTAPI}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=messages.ERROR_CONNECTING_TO_THE_DATABASE)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
