import logging

from ogn.gateway.client import ognGateway
from ogn.commands.dbutils import session

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
    gateway = ognGateway(aprs_user)
    gateway.connect()

    def process_beacon(beacon):
        session.add(beacon)
        session.commit()

    try:
        gateway.run(callback=process_beacon, autoreconnect=True)
    except KeyboardInterrupt:
        print('\nStop ogn gateway')

    gateway.disconnect()
    logging.shutdown()
