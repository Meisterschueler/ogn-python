import socket
from time import time

from ogn import db_utils
from ogn import settings
from ogn.aprs_parser import *


def proceed():
    # create socket, connect to server, login and make a file object associated with the socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    sock.connect((settings.APRS_SERVER_HOST, settings.APRS_SERVER_PORT))
    login = 'user %s pass %s vers PyGrabber 1.0 %s\n'  % (settings.APRS_USER, settings.APRS_PASSCODE, settings.APRS_FILTER)
    sock.send(login.encode())
    sock_file = sock.makefile('rw')

    keepalive_time = time()

    try:
        while True:
            if time()-keepalive_time > 60:
                sock.send("#keepalive".encode())
                keepalive_time = time()

            # Read packet string from socket
            try:
                packet_str = sock_file.readline().strip()
            except socket.error:
                print('Socket error on readline')
                continue

            # A zero length line should not be return if keepalives are being sent
            # A zero length line will only be returned after ~30m if keepalives are not sent
            if len(packet_str) == 0:
                print('Read returns zero length string. Failure.  Orderly closeout')
                break

            proceed_line(packet_str)
    finally:
        # close everything
        print('Close socket')
        sock.shutdown(0)
        sock.close()


def proceed_line(line):
    try:
        result = parse_aprs(line)
    except Exception as e:
        print('Failed to parse line: %s' % line)
        print('Reason: %s' % e)
        return

    if isinstance(result, Position):
        db_utils.put_position_into_db(result)
    elif isinstance(result, Receiver):
        db_utils.put_receiver_into_db(result)

if __name__ == '__main__':
    while True:
        try:
            print("Start Python_Test")
            proceed()
            print("Python Test Exit")
        except OSError as e:
            print("OSError %s" % e)
