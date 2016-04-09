from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base

from .settings import POSTGRES_URL

Base = declarative_base()


class Message(Base):
    __tablename__ = 'Messages'

    def to_dict(self):
        d = {}
        for c in self.__table__.columns:
            key = c.name
            value = getattr(self, c.name)

            if type(value) == datetime:
                value = value.strftime("%Y-%m-%d %H:%M")

            d.update({key: value})
        return d

    # Here we define columns for the table person
    # Notice that each column is also a normal Python instance attribute.
    id = Column(Integer, primary_key=True)
    text = Column(String(255))
    username = Column(String(40))
    type = Column(String(40))
    reputation = Column(Integer)
    time = Column(DateTime, default=func.now())


# Create an engine that stores data in the local directory's
# sqlalchemy_example.db file.
engine = create_engine(POSTGRES_URL)

# Create all tables in the engine. This is equivalent to "Create Table"
# statements in raw SQL.
Base.metadata.create_all(engine)
