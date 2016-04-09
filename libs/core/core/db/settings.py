__author__ = 'andrew.shvv@gmail.com'

USER = 'postgres'
PASSWORD = 'postgres'
HOST = 'postgres'
DB = 'postgres'

POSTGRES_URL = "postgresql://{user}:{password}@{host}/{db}".format(
    user=USER,
    password=PASSWORD,
    host=HOST,
    db=DB
)
