import socket

from ogn.gateway import ognGateway
from ogn.logger import logger

from manager import Manager
manager = Manager()

DB_URI = 'sqlite:///beacons.db'


@manager.command
def run(aprs_user="anon-dev"):
    """Run the aprs client."""

    if len(aprs_user) < 3 or len(aprs_user) > 9:
        print("aprs_user must be a string of 3-9 characters")
        return

    user_interrupted = False
    gateway = ognGateway()

    print("Connect to DB")
    logger.info('Connect to DB')
    gateway.connect_db()

    while user_interrupted is False:
        logger.info("Connect OGN gateway as {}".format(aprs_user))
        gateway.connect(aprs_user)

        try:
            logger.info('Run gateway')
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
