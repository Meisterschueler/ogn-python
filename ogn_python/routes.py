import datetime

from flask import request, render_template
from sqlalchemy import func, and_, or_

from ogn_python import app
from ogn_python import db

from ogn_python.model import *


@app.route('/')
@app.route('/index.html')
def index():
    return render_template('base.html')


@app.route('/devices.html', methods=['GET', 'POST'])
def devices():
    devices = db.session.query(Device) \
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

    countries_in_receivers = db.session.query(Country.iso2, func.count(Receiver.id).label('receiver_count')) \
        .filter(Country.gid == Receiver.country_id) \
        .group_by(Country.iso2) \
        .order_by(Country.iso2)

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
                           countries=countries_in_receivers,
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

    countries_in_logbook = db.session.query(Country.iso2, func.count(Airport.id).label('airport_count')) \
        .filter(Country.iso2 == Airport.country_code) \
        .group_by(Country.iso2) \
        .order_by(Country.iso2)

    if sel_country:
        airports = db.session.query(Airport, Receiver).outerjoin(Receiver) \
            .filter(and_(or_(Logbook.takeoff_airport_id == Airport.id, Logbook.landing_airport_id == Airport.id), Airport.country_code == sel_country)) \
            .group_by(Airport.id) \
            .order_by(Airport.name)
    else:
        airports = []

    page = request.args.get('page', 1, type=int)

    return render_template('airports.html',
                           sel_country=sel_country,
                           countries=countries_in_logbook,
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

    airport_ids_in_logbook = db.session.query(db.distinct(Logbook.takeoff_airport_id).label('id')) \
        .subquery()

    airports_in_logbook = db.session.query(Airport) \
        .filter(Airport.id == airport_ids_in_logbook.c.id) \
        .subquery()

    country_ids_in_logbook = db.session.query(db.distinct(Country.gid).label('id')) \
        .filter(Country.iso2 == airports_in_logbook.c.country_code) \
        .subquery()

    countries_avail = db.session.query(Country) \
        .filter(Country.gid == country_ids_in_logbook.c.id) \
        .order_by(Country.iso2)

    # Get airport selection list
    if sel_country:
        airports = db.session.query(Airport) \
            .filter(Airport.id == airport_ids_in_logbook.c.id) \
            .filter(Airport.country_code == sel_country) \
            .order_by(Airport.name)
    elif sel_airport:
        airports = db.session.query(Airport) \
            .filter(Airport.id == sel_airport)

        sel_country = airports.one().country_code
    else:
        airports = ['']

    # Get date selection list
    if sel_country and sel_airport:
        dates = db.session.query(db.func.date(Logbook.reftime), db.func.count(Logbook.id)) \
            .filter(db.or_(Logbook.takeoff_airport_id == sel_airport,
                           Logbook.landing_airport_id == sel_airport)) \
            .group_by(db.func.date(Logbook.reftime)) \
            .order_by(db.func.date(Logbook.reftime))
    else:
        dates = ['']

    # Get Logbook
    filters = []
    if sel_country and sel_airport:
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
                           countries=countries_avail,
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