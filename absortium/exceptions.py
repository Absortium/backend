from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.views import exception_handler

from absortium import constants
from core.utils.logging import getPrettyLogger
from core.utils.general import switch

__author__ = 'andrew.shvv@gmail.com'

logger = getPrettyLogger(__name__)


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        error_id = None

        for case in switch(response.status_code):
            if case(status.HTTP_404_NOT_FOUND):
                error_id = constants.ERROR_NOT_FOUND
                break

            if case(status.HTTP_400_BAD_REQUEST):
                error_id = exc.error_id if hasattr(exc, 'error_id') else constants.ERROR_VALIDATION
                break

            if case(status.HTTP_500_INTERNAL_SERVER_ERROR):
                error_id = constants.ERROR_INTERNAL
                break

            if case(status.HTTP_403_FORBIDDEN):
                error_id = constants.ERROR_PERMISSION_DENIED
                break

            if case(status.HTTP_405_METHOD_NOT_ALLOWED):
                error_id = constants.ERROR_NOT_ALLOWED
                break

        response.data = {
            'detail': response.data['detail'] if 'detail' in response.data else response.data,
            'status_code': response.status_code
        }

        if error_id is not None:
            response.data['error_id'] = error_id

    return response


class NotEnoughMoneyError(ValidationError):
    error_id = constants.ERROR_NOT_ENOUGH_MONEY


class LockFailureError(ValidationError):
    error_id = constants.ERROR_LOCK_FAILURE


class AlreadyExistError(ValidationError):
    error_id = constants.ERROR_ALREADY_EXIST
    status_code = status.HTTP_409_CONFLICT
