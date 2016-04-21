__author__ = 'andrew.shvv@gmail.com'


def retry(times=1, exceptions=()):
    assert(type(exceptions) == tuple)

    def wrapper(func):
        def decorator(*args, **kwargs):
            t = 0
            while times > t:
                try:
                    return func(*args, **kwargs)
                except exceptions:
                    t += 1

        return decorator

    return wrapper
