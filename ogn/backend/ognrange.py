import json
from datetime import datetime, timedelta

from sqlalchemy import func, case
from sqlalchemy.sql.expression import label
from ogn.model import Receiver


def alchemyencoder(obj):
    import decimal
    from datetime import datetime
    """JSON encoder function for SQLAlchemy special classes."""
    if isinstance(obj, datetime):
        return obj.strftime('%Y-%m-%d %H:%M')
    elif isinstance(obj, decimal.Decimal):
        return float(obj)


def stations2_filtered_pl(session):
    last_10_minutes = datetime.utcnow() - timedelta(minutes=10)

    query = session.query(
        Receiver.name.label('s'),
        label('lt', func.round(func.ST_Y(Receiver.location_wkt) * 10000) / 10000),
        label('lg', func.round(func.ST_X(Receiver.location_wkt) * 10000) / 10000),
        case([(Receiver.lastseen > last_10_minutes, "U")],
            else_="D").label('u'),
        Receiver.lastseen.label('ut'),
        label('v', Receiver.version + '.' + Receiver.platform)) \
        .order_by(Receiver.lastseen)

    res = session.execute(query)
    stations = json.dumps({'stations': [dict(r) for r in res]}, default=alchemyencoder)

    return stations
