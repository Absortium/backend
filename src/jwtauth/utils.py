__author__ = 'andrew.shvv@gmail.com'

import time

from rest_framework_jwt.utils import jwt_payload_handler


def wrapped_jwt_payload_handler(user):
    """
        Wrap original 'jwt_payload_handler' in order to convert expiration time to unix style format.
    """

    payload = jwt_payload_handler(user)
    payload['exp'] = int(time.mktime(payload['exp'].timetuple()))
    return payload
