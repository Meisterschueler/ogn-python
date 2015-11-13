from datetime import datetime, timedelta

from flask import Flask, render_template
from flask.ext.script import Manager
from flask.ext.bootstrap import Bootstrap
from flask.ext.sqlalchemy import SQLAlchemy
from flask_nav import Nav
from flask_nav.elements import Navbar, View

import json

from ogn.model.address_origin import AddressOrigin
from ogn.model.flarm import Flarm

from ogn.db import session

from sqlalchemy import func, desc, and_
from sqlalchemy.sql.expression import label
from ogn.model.receiver_beacon import ReceiverBeacon
from ogn.model.receiver_device import ReceiverDevice
from ogn.model.aircraft_beacon import AircraftBeacon
from flask.json import jsonify

app = Flask(__name__)
manager = Manager(app)
bootstrap = Bootstrap(app)
nav = Nav()
nav.init_app(app)


mynavbar = Navbar(
    'Open Glider Network',
    View('Home', 'index'),
    View('Live', 'live'),
    View('Flarms', 'flarms'),
    View('Receivers', 'receivers'),
    View('Statistics', 'statistics'),
)


nav.register_element('top', mynavbar)


@app.route("/")
def index():
    return render_template('index.html')


@app.route('/live')
def live():
    return render_template('live.html')

@app.route('/aircraft_beacons')
def aircraft_beacons():
    sq_last = session.query(AircraftBeacon.address, func.max(AircraftBeacon.timestamp).label('lastseen')) \
        .filter(AircraftBeacon.timestamp > '2015-11-13 15:00:00') \
        .group_by(AircraftBeacon.address) \
        .subquery()

    aircraft_beacons_query = session.query(AircraftBeacon.address, AircraftBeacon.latitude, AircraftBeacon.longitude, Flarm.registration, Flarm.aircraft) \
        .outerjoin(Flarm, AircraftBeacon.address == Flarm.address) \
        .filter(and_(AircraftBeacon.address == sq_last.c.address, AircraftBeacon.timestamp == sq_last.c.lastseen))

    result = {}
    for [address, latitude, longitude, registration, aircraft] in aircraft_beacons_query.all():
        result[address] = {'lat': latitude, 'lng': longitude, 'registration': registration, 'aircraft': aircraft}
    return(json.dumps({'aircraft_beacons': result}))

    #return(json.dumps(aircraft_beacons_query.all(), ensure_ascii=False))


@app.route('/flarms')
def flarms():
    flarm_query = session.query(Flarm.address, Flarm.aircraft, Flarm.registration, Flarm.competition).\
        filter(Flarm.address_origin == AddressOrigin.userdefined).\
        order_by(Flarm.address).all()
    return render_template('flarms.html', flarms=flarm_query)


@app.route('/receivers')
def receivers():
    back_24h = datetime.utcnow() - timedelta(days=1)
    receiver_messages_per_24h = 24*60 / 5

    sq_r_beacons = session.query(ReceiverBeacon.name, func.count(ReceiverBeacon.name).label('messages_count')).\
        filter(ReceiverBeacon.timestamp > back_24h).\
        group_by(ReceiverBeacon.name).\
        subquery()

    sq_a_beacons = session.query(AircraftBeacon.receiver_name, func.count(AircraftBeacon.receiver_name).label('beacons_count')).\
        filter(AircraftBeacon.timestamp > back_24h).\
        group_by(AircraftBeacon.receiver_name).\
        subquery()

    receiver_query = session.query(ReceiverDevice.country_code, ReceiverDevice.name, ReceiverDevice.lastseen, label('availability', 100*sq_r_beacons.c.messages_count/receiver_messages_per_24h), ReceiverDevice.version, ReceiverDevice.platform, sq_a_beacons.c.beacons_count).\
        filter(ReceiverDevice.name == sq_r_beacons.c.name).\
        filter(ReceiverDevice.name == sq_a_beacons.c.receiver_name).\
        order_by(desc(sq_a_beacons.c.beacons_count)).all()

    return render_template('receivers.html', receivers=receiver_query)


@app.route('/statistics')
def statistics():
    return render_template('index.html')


if __name__ == "__main__":
    app.run(debug=True)
    #with app.app_context():
    #    aircraft_beacons()
