__author__ = 'andrew.shvv@gmail.com'

import base64
import hashlib

import jwt
from django.contrib.auth import get_user_model
from rest_framework_jwt.settings import api_settings

from absortium.constants import USERNAME_LENGTH
from core.utils.logging import getLogger

logger = getLogger(__name__)


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
    logger.debug(payload)

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
        user.save()

    return user.username
