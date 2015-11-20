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
        print("Connect OGN gateway")
        gateway.connect(aprs_user)

        try:
            gateway.run()
        except KeyboardInterrupt:
            print("User interrupted")
            user_interrupted = True
        except BrokenPipeError:
            print("BrokenPipeError")
        except socket.err:
            print("socket error")

        print("Disconnect OGN gateway")
        gateway.disconnect()

    print("\nExit OGN gateway")
