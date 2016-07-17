import hashlib
import os

__author__ = 'andrew.shvv@gmail.com'


def generate_token(length=128):
    return hashlib.sha1(os.urandom(length)).hexdigest()
