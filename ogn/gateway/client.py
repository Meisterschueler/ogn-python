import socket
import logging
from time import time

from ogn.gateway import settings
from ogn.commands.dbutils import session
from ogn.aprs_parser import parse_aprs
from ogn.aprs_utils import create_aprs_login
from ogn.exceptions import AprsParseError, OgnParseError

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ogn.model import Base


class ognGateway:
    def __init__(self):
        pass
    def connect_db(self):
        self.session = session
        self.logger = logging.getLogger(__name__)

    def connect(self, aprs_user):
        # create socket, connect to server, login and make a file object associated with the socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        self.sock.connect((settings.APRS_SERVER_HOST, settings.APRS_SERVER_PORT))

        login = create_aprs_login(aprs_user, -1, settings.APRS_APP_NAME, settings.APRS_APP_VER, settings.APRS_FILTER)
        self.sock.send(login.encode())
        self.sock_file = self.sock.makefile('rw')

    def disconnect(self):
        # close everything
        self.sock.shutdown(0)
        self.sock.close()

    def run(self):
        keepalive_time = time()
        while True:
            if time() - keepalive_time > settings.APRS_KEEPALIVE_TIME:
                logger.debug('Sending keepalive')
                self.sock.send("#keepalive".encode())
                keepalive_time = time()

            # Read packet string from socket
            packet_str = self.sock_file.readline().strip()

            # A zero length line should not be return if keepalives are being sent
            # A zero length line will only be returned after ~30m if keepalives are not sent
            if len(packet_str) == 0:
                logger.warning('Read returns zero length string. Failure.  Orderly closeout')
                break

            self.proceed_line(packet_str)

    def proceed_line(self, line):
        try:
            beacon = parse_aprs(line)
            self.logger.debug('Received beacon: {}'.format(beacon))
        except AprsParseError:
            self.logger.error('AprsParseError while parsing line: {}'.format(line), exc_info=True)
            return
        except OgnParseError:
            self.logger.error('OgnParseError while parsing line: {}'.format(line), exc_info=True)
            return

        if beacon is not None:
            self.session.add(beacon)
            self.session.commit()
