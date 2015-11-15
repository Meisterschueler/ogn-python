from ogn.gateway import ognGateway

DB_URI = 'sqlite:///beacons.db'

from manager import Manager
manager = Manager()

@manager.command
def run(aprs_user="anon-dev"):
    """Run the aprs client."""
    gateway = ognGateway()
    print("Start OGN gateway")
    gateway.connect_db()
    gateway.connect(aprs_user)
    try:
        gateway.run()
    except KeyboardInterrupt:
        pass
    print("\nOGN gateway Exit")
