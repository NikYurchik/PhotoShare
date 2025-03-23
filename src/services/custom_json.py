import os
import json
from typing import List, Dict
from datetime import datetime, timezone

from src.base import app
# from src.database.models import User
from src.schemas import (UserDbResponse, UserDbAdmin, UserRole, 
                         PhotoResponse, CommentResponse, TagDetail, PhotoSchema, 
                         PhotoURLResponse, PhotoTransformModel)


class Jsons:

    @staticmethod
    def roleresponse_to_json(role: UserRole):
        idx = 0
        for rol in UserRole:
            if role == rol:
                return {"key": f"{idx}", "value": str(rol).split(".")[1]}
            idx += 1
        return {}
    

    @staticmethod
    def list_roleresponse_to_json(roles: UserRole):
        res = []
        idx = 0
        for role in roles:
            res.append({"key": f"{idx}", "value": str(role).split(".")[1]})
            idx += 1
        return res
    

    @staticmethod
    def userresponse_to_json(user: UserDbResponse, auth: bool=False):
        res_photo = {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "created_at": user.created_at,
                        "avatar": user.avatar,
                        "roles": user.roles,
                        # "photo_count": user.photo_count,
                        "is_authenticated": auth
                    }
        try:
            res_photo.update({"photo_count": user.photo_count})
        except:
            res_photo.update({"photo_count": 0})
        return res_photo


    @staticmethod
    def useradminresponse_to_json(user: UserDbAdmin):
        res = Jsons.userresponse_to_json(user)
        res.update({"confirmed": user.confirmed, "is_banned": user.is_banned})
        return res


    @staticmethod
    def list_useradminresponse_to_json(users: List[UserDbAdmin]):
        res = []
        for user in users:
            res.append(Jsons.useradminresponse_to_json(user))
        return res


    @staticmethod
    def only_photoresponse_to_json(photo: PhotoSchema):
        res_photo = {
                        "id": photo.id,
                        "file_url": photo.file_url,
                        "qr_url": photo.qr_url,
                        "description": photo.description,
                        "created_at": photo.created_at.strftime("%Y-%m-%d %H:%M:%S.%f"), #"2023-10-22T04:04:09.329393"
                        "user_id": photo.user_id,
                    }
        try:
            res_photo.update({"username": photo.username})
        except:
            pass

        return res_photo


    @staticmethod
    def photoresponse_to_json(photo: PhotoResponse):
        ph = photo["photo"]
        res_photo = {"photo": Jsons.only_photoresponse_to_json(ph)
                    }

        res_tags = []
        for tag in photo["tags"]:
            res_tags.append({"id": tag.id, "name": tag.name})
        res_photo.update({"tags": res_tags})

        res_comm = []
        for comm in photo["comments"]:
            res_comm.append(Jsons.commentresponse_to_json(comm))
        res_photo.update({"comments": res_comm})

        return res_photo


    @staticmethod
    def transformphotoresponse_to_json(transformphoto: PhotoURLResponse):
        if transformphoto:
            res = {"id": transformphoto.id,
                    "file_url": transformphoto.file_url,
                    "qr_url": transformphoto.qr_url,
                    "photo_id": transformphoto.photo_id,
                    "created_at": transformphoto.created_at.strftime("%Y-%m-%d %H:%M:%S.%f"),
                    "params": transformphoto.params
                    }
        else:
            res = {"id": "", "file_url": "", "qr_url": "", "photo_id": "", "created_at": ""}
        return res


    @staticmethod
    def list_transformphotoresponse_to_json(transformphotos: List[PhotoURLResponse]):
        res = []
        for tph in transformphotos:
            res.append(Jsons.transformphotoresponse_to_json(tph))
        return res


    @staticmethod
    def list_photoresponse_to_json(photos: List[PhotoResponse]):
        res = []
        for ph in photos:
            res.append(Jsons.photoresponse_to_json(ph))
        return res


    @staticmethod
    def commentresponse_to_json(comment: CommentResponse):
        return {"id": comment.id, "text": comment.text, "user_id":comment.user_id, "username": comment.username}


    @staticmethod
    def tagresponse_to_json(tag: TagDetail):
        return {"id": tag.id, "name": tag.name}


    @staticmethod
    def list_tagresponse_to_json(tags: List[TagDetail]):
        res = []
        for tag in tags:
            res.append(Jsons.tagresponse_to_json(tag))
        return res


    @staticmethod
    async def get_qualifiers():
        file = 'src/transformation.json'
        qualifiers = app.extra["qualifiers"]
        ts = app.extra["qualifiers_ts"]
        modified = os.path.getmtime(file)

        if not qualifiers or not ts or ts < modified:
            with open(file, 'r') as fh:
            # with open('src/transform.json', 'r') as fh:
                res = json.load(fh)

            qualifiers = res["qualifiers"]
            app.extra.update({"qualifiers": qualifiers})
            app.extra.update({"qualifiers_ts": modified})

        return qualifiers


    @staticmethod
    async def get_transform_params(body: PhotoTransformModel):
        res = {
            "height": body.height,              # высота изображения
            "width": body.width,                # ширина изображения
            "crop": body.crop,                  # Режим обрезки
            "gravity": body.gravity,            # условный центр изображения
            "radius": body.radius,              # радиус закругления углов
            "fetch_format": body.fetch_format,  # Преобразование фото в определенный формат
            "effect": body.effect,              # Эффекты и улучшения изображений
            "quality": body.quality,            # % потери качества при сжатии
            "angle": body.angle                 # угол поворота
        }
        return res
