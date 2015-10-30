from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .model import Base, Position, Receiver, Flarm


# prepare db
#engine = create_engine('sqlite:///:memory:', echo=False)
engine = create_engine('sqlite:///ogn.db', echo=False)
#engine = create_engine('postgresql://postgres:secretpass@localhost:5432/ogn')

Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()
