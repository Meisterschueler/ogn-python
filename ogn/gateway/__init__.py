import socket
from time import time

from ogn.gateway import settings
from ogn.commands.dbutils import session
from ogn.aprs_parser import parse_aprs
from ogn.exceptions import AprsParseError, OgnParseError

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ogn.model import Base

MODULE_VERSION = "0.1"


class ognGateway:
    def __init__(self):
        pass

    def connect_db(self):
        self.session = session

    def connect(self, aprs_user):
        if len(aprs_user) < 3 or len(aprs_user) > 9:
            print("aprs_user must be a string of 3-9 characters")
        # create socket, connect to server, login and make a file object associated with the socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        self.sock.connect((settings.APRS_SERVER_HOST, settings.APRS_SERVER_PORT))

        login = 'user %s pass %s vers ogn-gateway-python %s %s\n' % (aprs_user, settings.APRS_PASSCODE, MODULE_VERSION, settings.APRS_FILTER)
        self.sock.send(login.encode())
        self.sock_file = self.sock.makefile('rw')

    def disconnect(self):
        # close everything
        print('Close socket')
        self.sock.shutdown(0)
        self.sock.close()

    def run(self):
        keepalive_time = time()
        while True:
            if time() - keepalive_time > 60:
                self.sock.send("#keepalive".encode())
                keepalive_time = time()

            # Read packet string from socket
            packet_str = self.sock_file.readline().strip()

            # A zero length line should not be return if keepalives are being sent
            # A zero length line will only be returned after ~30m if keepalives are not sent
            if len(packet_str) == 0:
                print('Read returns zero length string. Failure.  Orderly closeout')
                break

            self.proceed_line(packet_str)

    def proceed_line(self, line):
        try:
            beacon = parse_aprs(line)
        except AprsParseError as e:
            print(e.message)
            return
        except OgnParseError as e:
            print(e.message)
            print("APRS line: %s" % line)
            return

        if beacon is not None:
            self.session.add(beacon)
            self.session.commit()
