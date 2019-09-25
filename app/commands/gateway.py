import os
import datetime

from flask import current_app
from flask.cli import AppGroup
import click

from ogn.client import AprsClient

from app.gateway.bulkimport import convert, DbFeeder

user_cli = AppGroup("gateway")
user_cli.help = "Connection to APRS servers."


@user_cli.command("run")
def run(aprs_user="anon-dev"):
    """Run the aprs client and feed the DB with incoming data."""

    # User input validation
    if len(aprs_user) < 3 or len(aprs_user) > 9:
        print("aprs_user must be a string of 3-9 characters.")
        return

    current_app.logger.warning("Start ogn gateway")
    client = AprsClient(aprs_user)
    client.connect()

    with DbFeeder(prefix='continuous_import', reference_timestamp=datetime.utcnow, reference_timestamp_autoupdate=True) as feeder:
        try:
            client.run(callback=lambda x: feeder.add(x), autoreconnect=True)
        except KeyboardInterrupt:
            current_app.logger.warning("\nStop ogn gateway")

    client.disconnect()


@user_cli.command("convert")
@click.argument("path")
def file_import(path):
    """Convert APRS logfiles into csv files for fast bulk import."""

    logfiles = []
    for (root, dirs, files) in os.walk(path):
        for file in sorted(files):
            logfiles.append(os.path.join(root, file))

    for logfile in logfiles:
        convert(logfile)
