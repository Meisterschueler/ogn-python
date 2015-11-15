from ogn.model import Base

from manager import Manager
manager = Manager()

from ogn.collect.fetchddb import update_ddb_data

@manager.command
def init():
    """Initialize the database."""
    from dbutils import engine
    Base.metadata.create_all(engine)
    print("Done.")
