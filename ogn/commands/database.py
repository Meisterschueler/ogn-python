from ogn.model import Base

from manager import Manager
manager = Manager()

from ogn.collect.fetchddb import update_ddb_data


@manager.command
def init():
    """Initialize the database."""
    from ogn.commands.dbutils import engine
    Base.metadata.create_all(engine)
    print("Done.")


@manager.command
def updateddb():
    """Update the ddb data."""
    print("Updating ddb data...")
    result = update_ddb_data.delay()
    counter = result.get()
    print("Imported %i devices." % counter)
