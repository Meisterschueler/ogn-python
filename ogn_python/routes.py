from flask import request, render_template

from ogn_python import app
from ogn_python import db

from ogn_python.model import *


@app.route('/')
@app.route('/index')
def index():
    return render_template('base.html')


@app.route('/devices', methods=['GET', 'POST'])
def devices():
    device_id = request.args.get('id')
    if device_id:
        device = db.session.query(Device) \
            .filter(Device.id == device_id)

        return render_template('device_detail.html', device=device)
    else:
        devices = db.session.query(Device) \
            .limit(100)
        return render_template('devices.html', devices=devices)


@app.route('/receivers')
def receivers():
    receivers = db.session.query(Receiver) \
        .filter(Receiver.country != db.null()) \
        .order_by(Receiver.name)
    return render_template('receivers.html', receivers=receivers)


@app.route('/airports')
def airports():
    page = request.args.get('page', 1, type=int)

    pagination = db.session.query(Airport) \
        .order_by(Airport.name) \
        .paginate(page, 20, False)
    return render_template('airports.html', pagination=pagination)


@app.route('/logbook', methods=['GET', 'POST'])
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
    if sel_date:
        filters.append(db.func.date(Logbook.reftime) == sel_date)

    if sel_country and sel_airport:
        filters.append(db.or_(Logbook.takeoff_airport_id == sel_airport, Logbook.landing_airport_id == sel_airport))

    if sel_device_id:
        filters.append(Logbook.device_id == sel_device_id)

    if len(filters) > 0:
        logbook = db.session.query(Logbook.takeoff_timestamp,
                                   db.func.round(Logbook.takeoff_track/10).label('takeoff_track'),
                                   Logbook.landing_timestamp,
                                   db.func.round(Logbook.landing_track/10).label('landing_track'),
                                   Logbook.max_altitude,
                                   DeviceInfo.aircraft,
                                   DeviceInfo.registration,
                                   DeviceInfo.competition) \
            .filter(*filters) \
            .filter(db.and_(Logbook.device_id == Device.id, Device.address == DeviceInfo.address)) \
            .order_by(Logbook.reftime)
    else:
        logbook = None

    return render_template('logbook.html', sel_country=sel_country, countries=countries_avail, sel_airport=sel_airport, airports=airports, sel_date=sel_date, dates=dates, logbook=logbook)


@app.route('/live')
def live():
    return render_template('ogn_live.jinja')


@app.route('/records')
def records():
    receiverstats = db.session.query(ReceiverStats) \
        .limit(10)

    return render_template('records.html', receiverstats=receiverstats)