import json
from datetime import datetime, timedelta

from sqlalchemy import func, case
from sqlalchemy.sql.expression import label
from ogn_python.model import Receiver, ReceiverCoverage

from ogn_python import db


def alchemyencoder(obj):
    """JSON encoder function for SQLAlchemy special classes."""

    import decimal
    from datetime import datetime
    if isinstance(obj, datetime):
        return obj.strftime('%Y-%m-%d %H:%M')
    elif isinstance(obj, decimal.Decimal):
        return float(obj)


def stations2_filtered_pl(start, end):
    last_10_minutes = datetime.utcnow() - timedelta(minutes=10)

    query = db.session.query(
            Receiver.name.label('s'),
            label('lt', func.round(func.ST_Y(Receiver.location_wkt) * 10000) / 10000),
            label('lg', func.round(func.ST_X(Receiver.location_wkt) * 10000) / 10000),
            case([(Receiver.lastseen > last_10_minutes, "U")],
                else_="D").label('u'),
            Receiver.lastseen.label('ut'),
            label('v', Receiver.version + '.' + Receiver.platform)) \
        .order_by(Receiver.lastseen) \
        .filter(db.or_(db.and_(start < Receiver.firstseen, end > Receiver.firstseen),
                       db.and_(start < Receiver.lastseen, end > Receiver.lastseen)))

    res = db.session.execute(query)
    stations = json.dumps({'stations': [dict(r) for r in res]}, default=alchemyencoder)

    return stations


def max_tile_mgrs_pl(station, start, end, squares):
    query = db.session.query(
            func.right(ReceiverCoverage.location_mgrs_short, 4),
            func.count(ReceiverCoverage.location_mgrs_short)
            ) \
        .filter(db.and_(Receiver.id == ReceiverCoverage.receiver_id, Receiver.name == station)) \
        .filter(ReceiverCoverage.location_mgrs_short.like(squares + '%')) \
        .group_by(func.right(ReceiverCoverage.location_mgrs_short, 4))

    res = {'t': squares,
           'p': ['{}/{}'.format(r[0], r[1]) for r in query.all()]}
    return json.dumps(res)