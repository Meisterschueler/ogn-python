import logging

from ogn.client import AprsClient
from ogn.gateway.process import process_beacon, message_to_beacon
from ogn.commands.dbutils import session
from datetime import datetime
from manager import Manager

manager = Manager()

logging_formatstr = '%(asctime)s - %(levelname).4s - %(name)s - %(message)s'
log_levels = ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG']


@manager.command
def run(aprs_user='anon-dev', logfile='main.log', loglevel='INFO'):
    """Run the aprs client."""

    # User input validation
    if len(aprs_user) < 3 or len(aprs_user) > 9:
        print('aprs_user must be a string of 3-9 characters.')
        return
    if loglevel not in log_levels:
        print('loglevel must be an element of {}.'.format(log_levels))
        return

    # Enable logging
    log_handlers = [logging.StreamHandler()]
    if logfile:
        log_handlers.append(logging.FileHandler(logfile))
    logging.basicConfig(format=logging_formatstr, level=loglevel, handlers=log_handlers)

    print('Start ogn gateway')
    client = AprsClient(aprs_user)
    client.connect()

    try:
        client.run(callback=process_beacon, autoreconnect=True)
    except KeyboardInterrupt:
        print('\nStop ogn gateway')

    client.disconnect()
    logging.shutdown()


@manager.command
def import_logfile(ogn_logfile, reference_date, logfile='main.log', loglevel='INFO'):
    """Import OGN-data from ogn-log-files <arg: ogn-logfile, reference_date>. Reference date must be given in YYYY-MM-DD."""

    # Check if filename exists
    try:
        f = open(ogn_logfile, 'r')
    except:
        print('\nError reading ogn-logfile:', ogn_logfile)
        return

    try:
        reference_date = datetime.strptime(reference_date, "%Y-%m-%d")
    except:
        print('\nError in reference_date argument', reference_date)
        return

    # Enable logging
    log_handlers = [logging.StreamHandler()]
    if logfile:
        log_handlers.append(logging.FileHandler(logfile))
    logging.basicConfig(format=logging_formatstr, level=loglevel, handlers=log_handlers)

    beacons = list()

    print('Start importing ogn-logfile')
    for line in f:
        beacon = message_to_beacon(line, reference_date=reference_date)
        if beacon is not None:
            beacons.append(beacon)

    session.bulk_save_objects(beacons)

    f.close()
    logging.shutdown()
