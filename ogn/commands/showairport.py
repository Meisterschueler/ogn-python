from ogn.model import Airport
from ogn.commands.dbutils import session

from manager import Manager
from sqlalchemy import and_, between
manager = Manager()


@manager.arg('country_code', help='filter by country code, eg. "de" for germany')
@manager.command
def list_all(country_code=None):
    """Show a list of all airports."""
    or_args = []
    if country_code is None:
        or_args = [between(Airport.style, 2, 5)]
    else:
        or_args = [and_(between(Airport.style, 2, 5),
                        Airport.country_code == country_code)]
    query = session.query(Airport) \
        .order_by(Airport.name) \
        .filter(*or_args)

    print('--- Airports ---')
    for airport in query.all():
        print(airport.name)
