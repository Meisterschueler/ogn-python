from flask import current_app
from flask.cli import AppGroup
import click

from ogn.client import AprsClient
from app.gateway.bulkimport import ContinuousDbFeeder

user_cli = AppGroup("gateway")
user_cli.help = "Connection to APRS servers."


@user_cli.command("run")
def run(aprs_user="anon-dev"):
    """Run the aprs client."""

    saver = ContinuousDbFeeder()

    # User input validation
    if len(aprs_user) < 3 or len(aprs_user) > 9:
        print("aprs_user must be a string of 3-9 characters.")
        return

    current_app.logger.warning("Start ogn gateway")
    client = AprsClient(aprs_user)
    client.connect()

    try:
        client.run(callback=saver.add, autoreconnect=True)
    except KeyboardInterrupt:
        current_app.logger.warning("\nStop ogn gateway")

    saver.flush()
    client.disconnect()
