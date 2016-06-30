import os

from setuptools import setup

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='core',
    version='0.1',
    packages=[
        'core',
        'core.utils',
        'core.serializer',
    ],
    include_package_data=True,
    description='Deluge Core module',
    long_description=README,
    url='https://github.com/AndrewSamokhvalov/core.git',
    author='Andrey Samokhvalov',
    author_email='andrew.shvv@gmail.com',
    install_requires=[
        'pp-ez',
        'Django==1.9.5',
        'djangorestframework==3.3.3',
        'six'
    ],
    classifiers=[
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.5',
    ],
)
