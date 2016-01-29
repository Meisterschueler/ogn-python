import os
import importlib
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


os.environ.setdefault('OGN_CONFIG_MODULE', 'config.default')

config = importlib.import_module(os.environ['OGN_CONFIG_MODULE'])
engine = create_engine(config.SQLALCHEMY_DATABASE_URI, echo=False)

Session = sessionmaker(bind=engine)
session = Session()
