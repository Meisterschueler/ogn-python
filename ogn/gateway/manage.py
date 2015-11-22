import socket

from ogn.gateway import ognGateway

DB_URI = 'sqlite:///beacons.db'

from manager import Manager
manager = Manager()


@manager.command
def run(aprs_user="anon-dev"):
    """Run the aprs client."""
    user_interrupted = False
    gateway = ognGateway()

    print("Connect to DB")
    gateway.connect_db()

    while user_interrupted is False:
        print("Connect OGN gateway as {}".format(aprs_user))
        gateway.connect(aprs_user)
        socket_open = True

        try:
            gateway.run()
        except KeyboardInterrupt:
            print("User interrupted")
            user_interrupted = True
        except BrokenPipeError:
            print("BrokenPipeError")
        except socket.error:
            print("socket error")
            socket_open = False

        if socket_open:
            gateway.disconnect()

    print("\nExit OGN gateway")
