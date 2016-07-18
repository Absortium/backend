__author__ = 'andrew.shvv@gmail.com'

import base64
import hashlib

import jwt
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from rest_framework_jwt.settings import api_settings

from absortium.constants import USERNAME_LENGTH
from core.utils.logging import getPrettyLogger

logger = getPrettyLogger(__name__)


def jwt_decode_handler(token):
    options = {
        'verify_exp': api_settings.JWT_VERIFY_EXPIRATION,
    }

    payload = jwt.decode(
        token,
        base64.b64decode(api_settings.JWT_SECRET_KEY.replace("_", "/").replace("-", "+")),
        api_settings.JWT_VERIFY,
        options=options,
        leeway=api_settings.JWT_LEEWAY,
        audience=api_settings.JWT_AUDIENCE,
        issuer=api_settings.JWT_ISSUER,
        algorithms=[api_settings.JWT_ALGORITHM])

    return payload


def jwt_get_username_from_payload(payload):
    sub = payload.get('sub')
    if not sub:
        return None

    username = hashlib.sha1(sub.encode()).hexdigest()[:USERNAME_LENGTH]
    User = get_user_model()

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        email = payload.get('email')
        if not email:
            return None

        user = User(username=username,
                    email=email)

        try:
            user.save()
        except IntegrityError:
            """
                IntegrityError might happen if two parallel request trying to do something in
                system and user not registered yet. So, they check - "Are user is registered?" and got DoesNotExist
                then they are simulteniosly trying to create it. Than one of the process get IntegrityError postgres
                "username is already exist".

            """
            user = User.objects.get(username=username)

    return user.username
