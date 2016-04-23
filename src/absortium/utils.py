__author__ = 'andrew.shvv@gmail.com'

from core.utils.logging import getPrettyLogger

logger = getPrettyLogger(__name__)

def retry(exceptions=(), times=1):
    assert(type(exceptions) == tuple)

    logger.debug(exceptions)

    def wrapper(func):
        def decorator(*args, **kwargs):
            t = 0
            while times > t:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    logger.debug(str(e))
                    t += 1


        return decorator

    return wrapper
