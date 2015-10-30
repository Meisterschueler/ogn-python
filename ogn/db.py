from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ogn.model.base import Base
from ogn.model.position import Position
from ogn.model.receiver import Receiver
from ogn.model.flarm import Flarm


# prepare db
#engine = create_engine('sqlite:///:memory:', echo=False)
engine = create_engine('sqlite:///ogn.db', echo=False)
#engine = create_engine('postgresql://postgres:secretpass@localhost:5432/ogn')

Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()
