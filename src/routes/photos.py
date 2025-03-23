from typing import List, Optional

from fastapi import APIRouter, Depends, UploadFile, File, Body, Query, HTTPException, status, Request, responses
from fastapi.responses import JSONResponse, HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_

from src.base import app, templates
from src.database.db import get_db
from src.database.models import User, UserRole, Photo, PhotoURL
from src.repository.auth import Auth as repository_auth
from src.repository.photos import PhotosRepository
from src.repository.tags import TagRepository
from src.repository import comments as repository_comments
from src.schemas import (PhotoResponse, PhotoUpdateModel, PhotoNewModel, PhotoExtResponse,
                         PhotoTransformModel, DetailResponse,
                         PhotoQRCodeModel, PhotoURLResponse, PhotoTransQRCodeModel, PhotoSearchModel,
                         PhotoAddTagsModel, CommentModel, CommentResponse, TagDetail)
from src.services.auth import auth_service
from src.services.validators import Validator
from src.services.roles import RoleAccess
from src.services.custom_limiter import RateLimiter
from src.services.custom_json import Jsons
from src.conf import messages

allowed_operation_all = RoleAccess([UserRole.admin, UserRole.moderator, UserRole.user])
# allowed_operation = RoleAccess([UserRole.admin, UserRole.user])

router = APIRouter(prefix="", tags=["photos"])


@router.get('/', response_model=List[PhotoResponse])
async def get_and_search_photos(request: Request,
                                page: int = Query(None, description="Page number"),
                                per_page: int = Query(None, description="Items per page"),
                                user_id: int = Query(None, description="Filter by user"),
                                keyword: str = Query(None, description="Keyword to search in photo descriptions"),
                                tag: str = Query(None, description="Filter photos by tag"),
                                order_by: str = Query("newest", description="Sort order date('newest' or 'oldest'"),
                                db: Session = Depends(get_db)):

    await repository_auth().check_authentication(request=request, db=db)
    # print(request.url)
    # print(f'page = {page}, per_page = {per_page}')
    photos, pages = await PhotosRepository().search_photos(db, page, per_page, user_id, keyword, tag, order_by)
    return photos, pages


@router.get('/photo-add', response_class=HTMLResponse)
# @router.get('/photo-add', response_model=List[TagDetail])
async def new_photo(request: Request, 
                    db: Session = Depends(get_db)):
    
    current_user = await repository_auth().check_authentication(request=request, db=db)
    if current_user:
        tags = await TagRepository().get_tags_all(session=db)
        return templates.TemplateResponse('photo/photo-add.html', {"request": request,
                                                                   "title": messages.CONTACTS_APP, 
                                                                   "user": app.extra["user"],
                                                                   "tags": Jsons.list_tagresponse_to_json(tags)})
    return responses.RedirectResponse("/",
                                      status_code=status.HTTP_302_FOUND)


@router.get('/{photo_id}', response_model=PhotoResponse, response_class=HTMLResponse)
async def get_photo_by_id(request: Request, 
                          photo_id: int,
                          db: Session = Depends(get_db)):
    check_auth = repository_auth()
    current_user = await check_auth.check_authentication(request=request, db=db)

    image = await PhotosRepository().get_photo_by_id(photo_id, db)
    tags = await TagRepository().get_tags_all(session=db)
    transforms = await PhotosRepository().get_transform_photos(photo_id=photo_id, session=db)
    return templates.TemplateResponse('photo/photo.html', {"request": request,
                                                            "title": messages.CONTACTS_APP, 
                                                            "user": app.extra["user"],
                                                            "roles": UserRole,
                                                            "photo": Jsons.photoresponse_to_json(image),
                                                            "tags": Jsons.list_tagresponse_to_json(tags),
                                                            "transforms": Jsons.list_transformphotoresponse_to_json(transforms)})


# @router.post('/', status_code=201, response_model=PhotoExtResponse, dependencies=[Depends(allowed_operation_all)])
@router.post('/', status_code=201, response_class=HTMLResponse, dependencies=[Depends(allowed_operation_all)])
async def upload_photo(request: Request,
                       body: PhotoNewModel = Body(...),
                       photo_file: UploadFile = File(...),
                       db: Session = Depends(get_db)):
    url_redirect = "/"
    message = ""
    check_auth = repository_auth()
    current_user = await check_auth.check_authentication(request=request, db=db)
    if current_user:
        try:
            tags_list = await Validator().validate_tags_count(body.tag_str, body.tags)
            new_photo = await PhotosRepository().upload_new_photo(body.description, tags_list, photo_file, current_user, db)
            url_redirect = f"/api/photos/{new_photo.id}"
        except HTTPException as err:
            message = err.detail
    else:
        message = check_auth.errors[0]["value"]

    if message:
        if url_redirect[len(url_redirect)-1] != "/":
            url_redirect = f"{url_redirect}/?message={message}" 
        else:
            url_redirect = f"{url_redirect}?message={message}" 
    
    # print(f">>> upload_photo: {url_redirect}")
    return responses.RedirectResponse(url_redirect,
                                      status_code=status.HTTP_302_FOUND)


# @router.post('/{photo_id}/add-tags', response_model=PhotoExtResponse, status_code=200, dependencies=[Depends(allowed_operation_all)])
@router.patch('/{photo_id}/add-tags', response_model=DetailResponse, status_code=200, dependencies=[Depends(allowed_operation_all)])
async def add_tag_to_photo(request: Request,
                           photo_id: int,
                           body: PhotoAddTagsModel,
                           db: Session = Depends(get_db)):
    message = ""
    check_auth = repository_auth()
    current_user = await check_auth.check_authentication(request=request, db=db)
    if current_user:
        try:
            tags_list = await Validator().validate_tags_count(body.tag_str, body.tags)
            photo = await PhotosRepository().add_tag_to_photo(tags_list, photo_id, current_user, db)
            return {"detail": {"success": [{"key": "reload", "value": ""}]}}
        except HTTPException as err:
            return {"detail": {"errors": [{"key": "error-msg", "value": err.detail}]}}
    else:
        message = check_auth.errors[0]["value"]

    return responses.RedirectResponse(f"/api/photos/{photo_id}/?message={message}",
                                      status_code=status.HTTP_302_FOUND)


@router.patch('/{photo_id}/remove-tag', response_model=DetailResponse, status_code=200, dependencies=[Depends(allowed_operation_all)])
async def remove_tag_from_photo(request: Request,
                                photo_id: int,
                                tag: str,
                                db: Session = Depends(get_db)):
    message = ""
    check_auth = repository_auth()
    current_user = await check_auth.check_authentication(request=request, db=db)
    if current_user:
        try:
            photo = await PhotosRepository().remove_tag_from_photo(tag, photo_id, current_user, db)
            return {"detail": {"success": [{"key": "reload", "value": ""}]}}
        except HTTPException as err:
            return {"detail": {"errors": [{"key": "error-msg", "value": err.detail}]}}
    else:
        message = check_auth.errors[0]["value"]

    return responses.RedirectResponse(f"/api/photos/{photo_id}/?message={message}",
                                      status_code=status.HTTP_302_FOUND)


# @router.put('/{photo_id}', response_model=PhotoResponse, dependencies=[Depends(allowed_operation_all)])
@router.put('/{photo_id}', response_model=DetailResponse, dependencies=[Depends(allowed_operation_all)])
async def update_photo_description(request: Request,
                                   photo_id: int,
                                   body: PhotoUpdateModel,
                                   db: Session = Depends(get_db)):
    message = ""
    check_auth = repository_auth()
    current_user = await check_auth.check_authentication(request=request, db=db)
    if current_user:
        try:
            photo = await PhotosRepository().update_photo_description(photo_id, body.description, current_user, db)
            return {"detail": {"success": [{"key": "description", "value": body.description}]}}
            
        except HTTPException as err:
            return {"detail": {"errors": [{"key": "error-msg", "value": err.detail}]}}
    else:
        message = check_auth.errors[0]["value"]

    return responses.RedirectResponse(f"/api/photos/{photo_id}/?message={message}",
                                      status_code=status.HTTP_302_FOUND)


@router.delete('/{photo_id}', response_model=DetailResponse, status_code=200, dependencies=[Depends(allowed_operation_all)])
async def delete_photo(request: Request,
                       photo_id: int,
                       db: Session = Depends(get_db)):
    message = ""
    check_auth = repository_auth()
    current_user = await check_auth.check_authentication(request=request, db=db)
    if current_user:
        try:
            photo = await PhotosRepository().delete_photo(photo_id, current_user, db)
            return {"detail": {"success": [{"key": "redirect", "value": "/"}]}}
        except HTTPException as err:
            return {"detail": {"errors": [{"key": "error-msg", "value": err.detail}]}}
    else:
        message = check_auth.errors[0]["value"]

    return responses.RedirectResponse(f"/api/photos/{photo_id}/?message={message}",
                                      status_code=status.HTTP_302_FOUND)


# @router.get('/photo-trans', response_model=List[TagDetail])
@router.get('/{photo_id}/transform', response_model=DetailResponse, response_class=HTMLResponse)
async def get_photo_transform( request: Request, 
                               photo_id: int,
                               transform_id: int=None,
                               db: Session = Depends(get_db)):
    
    message = ""
    check_auth = repository_auth()
    current_user = await check_auth.check_authentication(request=request, db=db)
    if current_user:
        try:
            image = await PhotosRepository().get_photo_by_id(photo_id, db)
            transform = await PhotosRepository().get_transform_photo(photo_id=photo_id, transform_id=transform_id, session=db)

            qualifiers = await Jsons.get_qualifiers()

            return templates.TemplateResponse('photo/photo-trans.html', {"request": request,
                                                                        "title": messages.CONTACTS_APP, 
                                                                        "user": app.extra["user"],
                                                                        "photo": Jsons.only_photoresponse_to_json(image["photo"]),
                                                                        "transform": Jsons.transformphotoresponse_to_json(transform),
                                                                        "qualifiers": qualifiers})
        except HTTPException as err:
            return {"detail": {"errors": [{"key": "error-msg", "value": err.detail}]}}
    else:
        message = check_auth.errors[0]["value"]

    return responses.RedirectResponse(f"/api/photos/{photo_id}",
                                      status_code=status.HTTP_302_FOUND)


@router.post("/{photo_id}/transform",
            #  response_model=PhotoURLResponse,
             response_model=DetailResponse, 
             description=messages.NO_MORE_THAN_10_REQUESTS_PER_MINUTE,
             dependencies=[Depends(allowed_operation_all), Depends(RateLimiter(times=10, seconds=60))])
async def photo_transform(request: Request, 
                          body: PhotoTransformModel, 
                          photo_id: int,
                          db: Session = Depends(get_db)):

    message = ""
    check_auth = repository_auth()
    current_user = await check_auth.check_authentication(request=request, db=db)
    if current_user:
        try:
            base_photo = db.query(Photo).filter(Photo.id == photo_id).first()

            if base_photo is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.PHOTO_NOT_FOUND)

            if base_photo.user_id != current_user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=messages.OPERATION_NOT_AVAILABLE)

            photo = await PhotosRepository().upload_transform_photo(body, base_photo, db)
            url = f"{request.url}/?transform_id={photo.id}"
            # print(f">>> photo_transform: redirect {url}")
            return {"detail": {"success": [{"key": "redirect", "value": url}]}}

        except HTTPException as err:
            return {"detail": {"errors": [{"key": "error-msg", "value": err.detail}]}}
    else:
        message = check_auth.errors[0]["value"]

    return responses.RedirectResponse(f"/api/photos/{photo_id}/?message={message}",
                                      status_code=status.HTTP_302_FOUND)


@router.put("/{photo_id}/transform",
            #  response_model=PhotoURLupdateResponse,
             response_model=DetailResponse, 
             description=messages.NO_MORE_THAN_10_REQUESTS_PER_MINUTE,
             dependencies=[Depends(allowed_operation_all), Depends(RateLimiter(times=10, seconds=60))])
async def update_photo_transform(request: Request, 
                                 body: PhotoTransformModel,
                                 photo_id: int,
                                 transform_id: int,
                                 db: Session = Depends(get_db)):

    message = ""
    check_auth = repository_auth()
    current_user = await check_auth.check_authentication(request=request, db=db)
    if current_user:
        try:
            base_photo = db.query(Photo).filter(Photo.id == photo_id).first()

            if base_photo is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.PHOTO_NOT_FOUND)

            if base_photo.user_id != current_user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=messages.OPERATION_NOT_AVAILABLE)

            photourl = db.query(PhotoURL).filter(and_(PhotoURL.photo_id == photo_id, PhotoURL.id == transform_id)).first()
            if not photourl:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.TRANS_PHOTO_NOT_FOUND)

            photo_trans = await PhotosRepository().update_transform_photo(body, base_photo, photourl, db)
            qr_url = photo_trans.qr_url if photo_trans.qr_url else ""
            return {"detail": {"success": [{"key": "file_url", "value": f"{photo_trans.file_url}"},
                                           {"key": "qr_url", "value": f"{qr_url}"}]}}

        except HTTPException as err:
            return {"detail": {"errors": [{"key": "error-msg", "value": err.detail}]}}
    else:
        message = check_auth.errors[0]["value"]

    return responses.RedirectResponse(f"/api/photos/{photo_id}/?message={message}",
                                      status_code=status.HTTP_302_FOUND)


@router.post("/{photo_id}/qrcode",
             response_model=DetailResponse,
             description=messages.NO_MORE_THAN_10_REQUESTS_PER_MINUTE,
             dependencies=[Depends(allowed_operation_all), Depends(RateLimiter(times=10, seconds=60))])
async def create_qrcode(request: Request,
                        body: PhotoQRCodeModel,
                        photo_id: int,
                        db: Session = Depends(get_db)):
    message = ""
    check_auth = repository_auth()
    current_user = await check_auth.check_authentication(request=request, db=db)
    if current_user:
        try:
            base_photo = db.query(Photo).filter(Photo.id == photo_id).first()

            if base_photo is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.PHOTO_NOT_FOUND)

            if current_user.roles == UserRole.user and base_photo.user_id != current_user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=messages.OPERATION_NOT_AVAILABLE)

            photo = await PhotosRepository().update_photo_qr_url(body, base_photo, db)
            # print(f">>> Photo QR-url: {photo.qr_url}")
            # return {"detail": {"success": [{"key": "reload", "value": "/"}]}}
            return {"detail": {"success": [{"key": "qr_url", "value": f"{photo.qr_url}"}]}}

        except HTTPException as err:
            return {"detail": {"errors": [{"key": "error-msg", "value": err.detail}]}}
    else:
        message = check_auth.errors[0]["value"]

    return responses.RedirectResponse(f"/api/photos/{photo_id}/?message={message}",
                                      status_code=status.HTTP_302_FOUND)


@router.post("/{photo_id}/qrcode/{transform_photo_id}",
             response_model=DetailResponse,
             description=messages.NO_MORE_THAN_10_REQUESTS_PER_MINUTE,
             dependencies=[Depends(allowed_operation_all), Depends(RateLimiter(times=10, seconds=60))])
async def create_trans_qrcode(request: Request,
                              body: PhotoQRCodeModel, 
                              photo_id: int, 
                              transform_photo_id: int,
                              db: Session = Depends(get_db)):

    message = ""
    check_auth = repository_auth()
    current_user = await check_auth.check_authentication(request=request, db=db)
    if current_user:
        try:
            base_photo = db.query(Photo).filter(Photo.id == photo_id).first()

            if base_photo is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.PHOTO_NOT_FOUND)

            if current_user.roles == UserRole.user and base_photo.user_id != current_user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=messages.OPERATION_NOT_AVAILABLE)

            if transform_photo_id:
                photo = db.query(PhotoURL).filter(and_(PhotoURL.photo_id == photo_id,
                                                        PhotoURL.id == transform_photo_id)).first()
                if photo is None:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.TRANS_PHOTO_NOT_FOUND)
            else:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=messages.TRANS_PHOTO_NOT_SPECIFIED)

            photo_tr = await PhotosRepository().update_transphoto_qr_url(body, photo, db)
            # print(f">>> Transform QR-url: {photo_tr.qr_url}")
            # return {"detail": {"success": [{"key": "reload", "value": "/"}]}}
            return {"detail": {"success": [{"key": "qr_url", "value": f"{photo_tr.qr_url}"}]}}

        except HTTPException as err:
            return {"detail": {"errors": [{"key": "error-msg", "value": err.detail}]}}
    else:
        message = check_auth.errors[0]["value"]

    return responses.RedirectResponse(f"/api/photos/{photo_id}/?message={message}",
                                      status_code=status.HTTP_302_FOUND)


@router.delete("/{photo_id}/{transform_photo_id}",
               status_code=204,
               description=messages.NO_MORE_THAN_10_REQUESTS_PER_MINUTE,
               dependencies=[Depends(allowed_operation_all), Depends(RateLimiter(times=10, seconds=60))])
async def delete_transform_photo(photo_id: int,
                                 transform_photo_id: int,
                                 user: User = Depends(auth_service.get_current_user), db: Session = Depends(get_db)):

    photo = db.query(PhotoURL).filter(and_(Photo.id == photo_id, PhotoURL.id == transform_photo_id)).first()

    if photo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.TRANS_PHOTO_NOT_FOUND)

    base_photo = db.query(Photo).filter(Photo.id == photo.photo_id).first()

    if base_photo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.PHOTO_NOT_FOUND)

    if user.roles == UserRole.user and base_photo.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=messages.OPERATION_NOT_AVAILABLE)

    return await PhotosRepository().delete_transform_photo(photo, db)


@router.post('/{photo_id}/comments', response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(request: Request,
                         photo_id: int,
                         body: CommentModel,
                         db: Session = Depends(get_db)):
    message = ""
    check_auth = repository_auth()
    current_user = await check_auth.check_authentication(request=request, db=db)
    if current_user:
        try:
            comment = await repository_comments.create_comment(photo_id, body, current_user, db)
            return {"comment": Jsons.commentresponse_to_json(comment),
                    "detail": {"success": [{"key": "reload", "value": "/"}]}}
        except HTTPException as err:
            return {"comment": {},
                    "detail": {"errors": [{"key": "message", "value": err.detail}]}}
    else:
        message = check_auth.errors[0]["value"]

    return responses.RedirectResponse(f"/api/photos/{photo_id}/?message={message}",
                                      status_code=status.HTTP_302_FOUND)


@router.put('/{photo_id}/comments/{comment_id}', response_model=CommentResponse,
                dependencies=[Depends(allowed_operation_all), Depends(RateLimiter(times=10, seconds=60))])
async def update_comment(photo_id: int,
                         comment_id: int,
                         body: CommentModel,
                         user: User = Depends(auth_service.get_current_user),
                         db: Session = Depends(get_db)):
    comment = await repository_comments.update_comment(photo_id, comment_id, body, user, db)
    return comment


@router.delete('/{photo_id}/comments/{comment_id}', #response_model=CommentResponse,
                status_code=204,
                dependencies=[Depends(allowed_operation_all), Depends(RateLimiter(times=10, seconds=60))])
async def delete_comment(photo_id: int,
                         comment_id: int,
                         user: User = Depends(auth_service.get_current_user),
                         db: Session = Depends(get_db)):
    comment = await repository_comments.delete_comment(photo_id, comment_id, user, db)
    return comment
