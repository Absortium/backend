import inspect
import logging

import pp

__author__ = 'andrew.shvv@gmail.com'


def get_prev_method_name():
    return inspect.stack()[2][3]


def pretty_wrapper(func):
    def decorator(msg, *args, **kwargs):
        pretty_msg = "Func:  %s\n" % get_prev_method_name()

        if type(msg) == str:
            pretty_msg += msg
        else:
            pretty_msg += pp.fmt(msg)
        pretty_msg += "\n+ "+"- " * 30+"+\n"

        func(pretty_msg, *args, **kwargs)

    return decorator


class LogMixin(object):
    def __init__(self):
        super().__init__()

        # create logger
        name = '.'.join([__name__, self.__class__.__name__])
        self.logger = getLogger(name)


def wrap_logger(logger):
    logger.info = pretty_wrapper(logger.info)
    logger.debug = pretty_wrapper(logger.debug)
    logger.warning = pretty_wrapper(logger.warning)
    logger.exception = pretty_wrapper(logger.exception)
    return logger


def getLogger(name, level=logging.DEBUG):
    # create logger
    logger = logging.getLogger(name)
    logger = wrap_logger(logger)

    # create console handler and set level to debug
    ch = logging.StreamHandler()

    # create formatter
    formatter = logging.Formatter('\nLevel: %(levelname)s - %(name)s - %(message)s')

    # add formatter to ch
    ch.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(ch)
    logger.setLevel(level)

    return logger
