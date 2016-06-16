from ogn.model import Airport
from ogn.commands.dbutils import session

from manager import Manager
manager = Manager()


@manager.command
def list_all():
    """Show a list of all airports."""
    query = session.query(Airport) \
        .order_by(Airport.name)

    print('--- Airports ---')
    for airport in query.all():
        print(airport.name)
