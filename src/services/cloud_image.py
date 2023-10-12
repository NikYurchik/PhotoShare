import hashlib

import cloudinary
import cloudinary.uploader

from src.conf.config import settings


class CloudImage:
    cloudinary.config(
        cloud_name=settings.cloudinary_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True
    )

    @staticmethod
    def generate_name_avatar(email: str):
        """
        The generate_name_avatar function takes an email address as input and returns a unique name for the avatar image.
            - The function uses the SHA256 hash algorithm to generate a unique string from the email address, then truncates it to 12 characters.
            - This is used as part of the file path where we will store our images.
        
        :param email: str: Specify the type of parameter that is expected to be passed into the function
        :return: A string
        :doc-author: Python-WEB13-project-team-2
        """
        name = hashlib.sha256(email.encode('utf-8')).hexdigest()[:12]
        return f"hw_rest_api/{name}"

    @staticmethod
    def upload(file, public_id: str):
        """
        The upload function takes a file and public_id as arguments.
            The function then uploads the file to Cloudinary with the given public_id, overwriting any existing files with that id.
        
        :param file: Specify the file to be uploaded
        :param public_id: str: Specify the public id of the image
        :return: A dictionary with the following keys:
        :doc-author: Python-WEB13-project-team-2
        """
        r = cloudinary.uploader.upload(file, public_id=public_id, overwrite=True)
        return r

    @staticmethod
    def get_url_for_avatar(public_id, r):
        """
        The get_url_for_avatar function takes a public_id and an optional resource dictionary.
            It returns the URL for the avatar image, which is a 250x250px crop of the original image.
        
        :param public_id: Identify the image to be uploaded
        :param r: Get the version of the image
        :return: A string containing the url of the avatar image
        :doc-author: Python-WEB13-project-team-2
        """
        src_url = cloudinary.CloudinaryImage(public_id) \
            .build_url(width=250, height=250, crop='fill', version=r.get('version'))
        return src_url
    
