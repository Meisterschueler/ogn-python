import logging

from ogn.client import AprsClient
from ogn.gateway.process import process_beacon, message_to_beacon
from datetime import datetime
from manager import Manager
from ogn.model import AircraftBeacon, ReceiverBeacon

from ogn.utils import open_file
import os

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
def convert_logfile(path, logfile='main.log', loglevel='INFO'):
    """Convert ogn logfiles to csv logfiles (one for aircraft beacons and one for receiver beacons) <arg: path>. Logfile name: blablabla.txt_YYYY-MM-DD."""

    # Enable logging
    log_handlers = [logging.StreamHandler()]
    if logfile:
        log_handlers.append(logging.FileHandler(logfile))
    logging.basicConfig(format=logging_formatstr, level=loglevel, handlers=log_handlers)

    logger = logging.getLogger(__name__)

    if os.path.isfile(path):
        logger.info("Reading file: {}".format(path))
        convert(path)
        logger.info("Finished")
    elif os.path.isdir(path):
        for filename in os.listdir(path):
            logger.info("Reading file: {}".format(filename))
            convert(filename, path=path)
        logger.info("Finished")
    else:
        print("Not a file nor a path: {}".format(path))

    logging.shutdown()


def convert(sourcefile, path=''):
    import re
    import csv

    match = re.search('^.+\.txt\_(\d{4}\-\d{2}\-\d{2})(\.gz)?$', sourcefile)
    if match:
        reference_date = match.group(1)
    else:
        print("filename '{}' does not match pattern".format(sourcefile))
        return

    fin = open_file(os.path.join(path, sourcefile))

    # get total lines of the input file
    total = 0
    for line in fin:
        total += 1
    fin.seek(0)

    fout_ab = open(os.path.join(path, 'aircraft_beacons.csv_' + reference_date), 'w')
    fout_rb = open(os.path.join(path, 'receiver_beacons.csv_' + reference_date), 'w')

    try:
        reference_date = datetime.strptime(reference_date, "%Y-%m-%d")
    except:
        print('\nError in reference_date argument', reference_date)
        return

    aircraft_beacons = list()
    receiver_beacons = list()

    progress = -1
    num_lines = 0

    wr_ab = csv.writer(fout_ab, delimiter=',')
    wr_ab.writerow(AircraftBeacon.get_csv_columns())

    wr_rb = csv.writer(fout_rb, delimiter=',')
    wr_rb.writerow(ReceiverBeacon.get_csv_columns())

    print('Start importing ogn-logfile')
    for line in fin:
        num_lines += 1
        if int(100 * num_lines / total) != progress:
            progress = round(100 * num_lines / total)
            print("\rReading line {} ({}%)".format(num_lines, progress), end='')
            if len(aircraft_beacons) > 0:
                for beacon in aircraft_beacons:
                    wr_ab.writerow(beacon.get_csv_values())
                aircraft_beacons = list()
            if len(receiver_beacons) > 0:
                for beacon in receiver_beacons:
                    wr_rb.writerow(beacon.get_csv_values())
                receiver_beacons = list()

        beacon = message_to_beacon(line.strip(), reference_date=reference_date)
        if beacon is not None:
            if isinstance(beacon, AircraftBeacon):
                aircraft_beacons.append(beacon)
            elif isinstance(beacon, ReceiverBeacon):
                receiver_beacons.append(beacon)

    if len(aircraft_beacons) > 0:
        for beacon in aircraft_beacons:
            wr_ab.writerow(beacon.get_csv_values())
    if len(receiver_beacons) > 0:
        for beacon in receiver_beacons:
            wr_rb.writerow(beacon.get_csv_values())

    fin.close()
    fout_ab.close()
    fout_rb.close()