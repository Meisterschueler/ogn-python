from flask.cli import AppGroup
import click

from ogn.client import AprsClient
from ogn_python.gateway.process_tools import DbSaver

from ogn_python import db

user_cli = AppGroup('gateway')
user_cli.help = "Connection to APRS servers."


@user_cli.command('run')
def run(aprs_user='anon-dev'):
    """Run the aprs client."""

    saver = DbSaver(session=db.session)

    # User input validation
    if len(aprs_user) < 3 or len(aprs_user) > 9:
        print('aprs_user must be a string of 3-9 characters.')
        return

    print('Start ogn gateway')
    client = AprsClient(aprs_user)
    client.connect()

    try:
        client.run(callback=saver.add_raw_message, autoreconnect=True)
    except KeyboardInterrupt:
        print('\nStop ogn gateway')

    saver.flush()
    client.disconnect()
