import re
from typing import Callable
import pathlib
import logging

import uvicorn
from fastapi import FastAPI, Depends, HTTPException, status, Request, Query
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.log import rootlogger

from src.database.db import get_db
from src.routes import auth, users, myuser, photos
from src.conf.config import BASE_DIR
from src.conf import messages
from src.services.custom_limiter import RateLimiter
from src.services.custom_json import Jsons
from src.base import app, templates, user_agent_ban_list
from src.repository.tags import TagRepository


logging.disable(logging.WARNING)
# logging.disable(logging.INFO)
# rootlogger.setLevel(logging.ERROR)
# logging.logProcesses = False

app.include_router(auth.router, prefix='/api/auth')
app.include_router(users.router, prefix='/api/users')
app.include_router(photos.router, prefix='/api/photos')
app.include_router(myuser.router, prefix='/api/myuser')


BASE_DIR = pathlib.Path(__file__).parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.mount("/htmlcov", StaticFiles(directory=BASE_DIR / "htmlcov"), name="htmlcov")
app.mount("/js", StaticFiles(directory=BASE_DIR / "js"), name="js")
# app.mount("/node_modules ", StaticFiles(directory=BASE_DIR / "node_modules "), name="node_modules ")
app.mount("/images", StaticFiles(directory=BASE_DIR / "images"), name="images")


# @app.middleware('http')
# async def custom_middleware(request: Request, call_next):
#     # print(f'request.base_url: {request.base_url}')
#     base_url = request.base_url
#     if base_url not in origins:
#         return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"detail": messages.NOT_ALLOWED_BASE_URL})
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
async def root( request: Request,
                page: int = Query(None, gt=0, description="Page number"),
                per_page: int = Query(None, ge=10, le=50, description="Items per page"),
                user_id: int = Query(None, description="Filter by user"),
                keyword: str = Query(None, description="Keyword to search in photo descriptions"),
                tag: str = Query(None, description="Filter photos by tag"),
                order_by: str = Query("newest", description="Sort order date('newest' or 'oldest'"),
                db: Session = Depends(get_db)):
    """
    The root function is the entry point for the application.
        - It returns a TemplateResponse object, which renders an HTML template using Jinja2.
        - The template is located in templates/index.html and uses data from the request object to render itself.
    
    :param request: Request: Get the request object
    :return: A templateresponse object, which is a subclass of response
    :doc-author: Python-WEB13-project-team-2
    """
    # print(f"app.extra: {app.extra}")
    images, pages = await photos.get_and_search_photos(request=request, db=db, page=page, per_page=per_page, user_id=user_id, keyword=keyword, tag=tag, order_by=order_by)

    top_tags = await TagRepository().get_tags_max10(session=db)
    top = []
    size = 28
    for tag_ in top_tags:
        # print(f'name: {tag.name}, count: {tag.tag_count}, tag_size: {size}')
        top.append({'tag_name': tag_.name, 'tag_size': f"{size}px"})
        size -= 2
        if len(top) >= 10:
            break

    return templates.TemplateResponse('index.html', {"request": request,
                                                     "title": messages.CONTACTS_APP, 
                                                     "user": app.extra["user"],
                                                     "view_tag": tag,
                                                     "top_tags": top,
                                                     "pages": pages,
                                                     "photos": Jsons.list_photoresponse_to_json(images)})


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
