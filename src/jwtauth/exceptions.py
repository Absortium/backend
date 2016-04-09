__author__ = 'andrew.shvv@gmail.com'

from rest_framework.exceptions import APIException
from rest_framework.status import HTTP_400_BAD_REQUEST


class Http400(APIException):
    status_code = HTTP_400_BAD_REQUEST
