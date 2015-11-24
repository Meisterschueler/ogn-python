from ogn.model import Base

from manager import Manager
manager = Manager()

from ogn.collect.fetchddb import update_ddb_from_ogn, update_ddb_from_file


@manager.command
def init():
    """Initialize the database."""
    from ogn.commands.dbutils import engine
    Base.metadata.create_all(engine)
    print("Done.")


@manager.command
def update_ddb_ogn():
    """Update devices with data from ogn."""
    print("Updating ddb data...")
    result = update_ddb_from_ogn.delay()
    counter = result.get()
    print("Imported %i devices." % counter)


@manager.command
def update_ddb_file():
    """Update devices with data from local file."""
    print("Updating ddb data...")
    result = update_ddb_from_file.delay()
    counter = result.get()
    print("Imported %i devices." % counter)
