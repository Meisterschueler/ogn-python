import datetime

from flask import request, render_template
from sqlalchemy import func, and_, or_

from ogn_python import app
from ogn_python import db
from ogn_python import cache

from ogn_python.model import *


@cache.cached(key_prefix='countries_in_receivers')
def get_countries_in_receivers():
    query = db.session.query(Country) \
        .filter(Country.gid == Receiver.country_id) \
        .order_by(Country.iso2) \
        .distinct()

    return [country for country in query.all()]


@cache.cached(key_prefix='countries_in_logbook')
def get_countries_in_logbook():
    query = db.session.query(Country) \
        .filter(Country.iso2 == Airport.country_code) \
        .order_by(Country.iso2) \
        .distinct()

    return [country for country in query.all()]


def get_airports_in_country(sel_country):
    query = db.session.query(Airport) \
        .filter(Airport.country_code == sel_country) \
        .filter(Logbook.takeoff_airport_id == Airport.id) \
        .order_by(Airport.name) \
        .distinct()

    return [airport for airport in query.all()]


def get_dates_for_airport(sel_airport):
    query = db.session.query(func.date(Logbook.reftime), func.count(Logbook.id).label('logbook_count')) \
        .filter(Airport.id == sel_airport) \
        .filter(or_(Airport.id == Logbook.takeoff_airport_id, Airport.id == Logbook.landing_airport_id)) \
        .group_by(func.date(Logbook.reftime)) \
        .order_by(func.date(Logbook.reftime).desc())

    return [{'date': date, 'logbook_count': logbook_count} for (date, logbook_count) in query.all()]


@app.route('/')
@app.route('/index.html')
def index():
    return render_template('base.html')


@app.route('/devices.html', methods=['GET', 'POST'])
def devices():
    devices = db.session.query(Device) \
        .order_by(Device.address) \
        .limit(100)
    return render_template('devices.html', devices=devices)


@app.route('/device_detail.html', methods=['GET', 'POST'])
def device_detail():
    device_id = request.args.get('id')
    device = db.session.query(Device) \
        .filter(Device.id == device_id) \
        .one()

    return render_template('device_detail.html',
                           title='Device',
                           device=device)


@app.route('/receivers.html')
def receivers():
    sel_country = request.args.get('country')

    countries = get_countries_in_receivers()

    # Get receiver selection list
    if sel_country:
        receivers = db.session.query(Receiver) \
            .filter(and_(Receiver.country_id == Country.gid, Country.iso2 == sel_country)) \
            .order_by(Receiver.name)
    else:
        receivers = db.session.query(Receiver) \
            .order_by(Receiver.name)

    return render_template('receivers.html',
                           title='Receivers',
                           sel_country=sel_country,
                           countries=countries,
                           receivers=receivers)


@app.route('/receiver_detail.html')
def receiver_detail():
    sel_receiver_id = request.args.get('receiver_id')

    receiver = db.session.query(Receiver) \
        .filter(Receiver.id == sel_receiver_id) \
        .one()

    airport = db.session.query(Airport) \
        .filter(and_(Receiver.id == sel_receiver_id, 
                     func.st_contains(func.st_buffer(Receiver.location_wkt, 0.5), Airport.location_wkt),
                     func.st_distance_sphere(Airport.location_wkt, Receiver.location_wkt) < 1000)) \
        .filter(Airport.style.in_((2,4,5))) \

    return render_template('receiver_detail.html',
                           title='Receiver Detail',
                           receiver=receiver,
                           airport=airport.first())


@app.route('/airports.html', methods=['GET', 'POST'])
def airports():
    sel_country = request.args.get('country')

    countries = get_countries_in_logbook()

    if sel_country:
        airports = db.session.query(Airport) \
            .filter(Airport.country_code == sel_country) \
            .order_by(Airport.name)
    else:
        airports = []

    page = request.args.get('page', 1, type=int)

    return render_template('airports.html',
                           sel_country=sel_country,
                           countries=countries,
                           airports=airports)


@app.route('/airport_detail.html')
def airport_detail():
    sel_airport = request.args.get('airport')

    airport = db.session.query(Airport) \
        .filter(Airport.id == sel_airport)

    devices = db.session.query(Device).join(Logbook) \
        .filter(Logbook.takeoff_airport_id == sel_airport) \
        .order_by(Device.address)

    return render_template('airport_detail.html',
                           title='Airport Detail',
                           airport=airport.one(),
                           devices=devices)


@app.route('/logbook.html', methods=['GET', 'POST'])
def logbook():
    sel_country = request.args.get('country')
    sel_airport = request.args.get('airport')
    sel_date = request.args.get('date')

    sel_device_id = request.args.get('device_id')

    countries = get_countries_in_logbook()

    if sel_country:
        airports = get_airports_in_country(sel_country)
    else:
        airports = []

    if sel_airport:
        sel_airport = int(sel_airport)
        if sel_airport not in [airport.id for airport in airports]:
            sel_airport = None
            sel_date = None
        dates = get_dates_for_airport(sel_airport)
    else:
        dates = []

    if sel_date:
        sel_date = datetime.datetime.strptime(sel_date, '%Y-%m-%d').date()
        if sel_date not in [entry['date'] for entry in dates]:
            sel_date = dates[0]['date']
    elif len(dates) > 0:
        sel_date = dates[0]['date']

    # Get Logbook
    filters = []
    if sel_airport:
        filters.append(db.or_(Logbook.takeoff_airport_id == sel_airport, Logbook.landing_airport_id == sel_airport))

    if sel_date:
        filters.append(db.func.date(Logbook.reftime) == sel_date)

    if sel_device_id:
        filters.append(Logbook.device_id == sel_device_id)

    if len(filters) > 0:
        logbook = db.session.query(Logbook) \
            .filter(*filters) \
            .order_by(Logbook.reftime)
    else:
        logbook = None

    return render_template('logbook.html',
                           title='Logbook',
                           sel_country=sel_country,
                           countries=countries,
                           sel_airport=sel_airport,
                           airports=airports,
                           sel_date=sel_date,
                           dates=dates,
                           logbook=logbook)


@app.route('/statistics.html')
def statistics():

    today = datetime.date.today()
    today = datetime.date(2018, 7, 31)

    receiverstats = db.session.query(ReceiverStats) \
        .filter(ReceiverStats.date == today)

    return render_template('statistics.html',
                           title='Receiver Statistics',
                           receiverstats=receiverstats)

# Backend routes for other sites


@app.route('/live.html')
def live():
    return render_template('ogn_live.jinja')