import re

import cloudinary
import cloudinary.uploader

from src.conf.config import settings
from src.database.models import User


class CloudImage:

    cloudinary.config(
        cloud_name=settings.cloudinary_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True
    )


    @staticmethod
    def upload_image(photo_file, user: User, folder: str=None) -> str:
        """
        The upload function takes a file and public_id as arguments.
            The function then uploads the file to Cloudinary with the given public_id, overwriting any existing files with that id.
        
        :param file: Specify the file to be uploaded
        :param public_id: str: Specify the public id of the image
        :return: A dictionary with the following keys:
        :doc-author: Python-WEB13-project-team-2
        """
        if not folder:
            folder = user.username
        res = cloudinary.uploader.upload(photo_file, folder=folder)
        return res["secure_url"]


    @staticmethod
    def delete_image(image_url: str):
        pattern = r"/v\d+/(.*?)\."
        match = re.search(pattern, image_url)
        if not match:
            pattern = r"/v\d+/(.*?)$"
            match = re.search(pattern, image_url)
        if match:
            public_id = match.group(1)
            result = cloudinary.uploader.destroy(public_id)
            if result.get('result') == 'ok':
                return ""
            else:
                return result.get('message')
        else:
            return "URL does not contain 'public_id' Cloudinary"


    @staticmethod
    def upload_transform_image(body, photo_file_url) -> str:

        public_id = re.search(r"/v\d+/(.+)\.\w+$", photo_file_url).group(1)

        url_changed_photo = cloudinary.CloudinaryImage(f"{public_id}").build_url(transformation=[
            {'gravity': body.gravity, 'height': body.height, 'width': body.width, 'crop': body.crop},
            {'radius': body.radius},
            {'effect': body.effect} if body.effect else None,
            {'quality': body.quality},
            {'fetch_format': body.fetch_format if body.fetch_format else re.search(r"\w+$", photo_file_url).group(
                0)}
        ])

        return url_changed_photo


    @staticmethod
    def upload_qrcode(qr_os_path, qr_ci_folder, qr_name) -> str:

        result = cloudinary.uploader.upload(
            qr_os_path,
            folder=qr_ci_folder,
            resource_type="image",
            public_id=f"{qr_name}"
        )

        return result['url']

