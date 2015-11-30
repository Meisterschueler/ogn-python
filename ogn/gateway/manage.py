import socket
import logging

from ogn.gateway.client import ognGateway

from manager import Manager
manager = Manager()

DB_URI = 'sqlite:///beacons.db'
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


    user_interrupted = False
    gateway = ognGateway()

    print("Connect to DB")
    gateway.connect_db()

    while user_interrupted is False:
        gateway.connect(aprs_user)
        try:
            gateway.run()
        except KeyboardInterrupt:
            logger.error('User interrupted', exc_info=True)
            user_interrupted = True
        except BrokenPipeError:
            logger.error('BrokenPipeError', exc_info=True)
        except socket.error:
            logger.error('Socket error', exc_info=True)

        try:
            logger.info('Close socket')
            gateway.disconnect()
        except OSError as e:
            print('Socket close error: {}'.format(e.strerror))
            logger.error('Socket close error', exc_info=True)

    print("\nExit OGN gateway")
