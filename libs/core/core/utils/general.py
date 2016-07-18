import os
import sys

__author__ = 'andrew.shvv@gmail.com'


def reverse_dict(d):
    return {value: key for key, value in d.items()}


def get_attr_from_module(module_name, attr_name):
    return getattr(sys.modules[module_name], attr_name)


def load_environments(module_name, environments):
    settings_module = sys.modules[module_name]
    for elem in environments:
        name = elem[0]
        env_name = elem[1]

        try:
            required = elem[2]
        except IndexError:
            required = None

        value = os.environ[env_name] if env_name in os.environ else None

        if required and value is None:
            raise NotImplementedError("Specify the '{}' environment variable.".format(env_name))
        else:
            setattr(settings_module, name, value)
