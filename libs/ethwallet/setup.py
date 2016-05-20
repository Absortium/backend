import os

from setuptools import setup

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='ethwallet',
    version='0.1',
    packages=[
        'ethwallet',
    ],
    include_package_data=True,
    description='Ethereum wallet module',
    long_description=README,
    author='Andrey Samokhvalov',
    author_email='andrew.shvv@gmail.com',
    install_requires=[
        'pp-ez'
    ],
    classifiers=[
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.5',
    ],
)
