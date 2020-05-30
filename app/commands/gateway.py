import os
from datetime import datetime, timezone

from flask import current_app
from flask.cli import AppGroup
import click
from tqdm import tqdm

from ogn.client import AprsClient

from app import redis_client
from app.gateway.bulkimport import convert, calculate

user_cli = AppGroup("gateway")
user_cli.help = "Connection to APRS servers."


@user_cli.command("run")
def run(aprs_user="anon-dev"):
    """Run the aprs client and feed the redis db with incoming data."""

    # User input validation
    if len(aprs_user) < 3 or len(aprs_user) > 9:
        print("aprs_user must be a string of 3-9 characters.")
        return

    current_app.logger.warning("Start ogn gateway")
    client = AprsClient(aprs_user)
    client.connect()

    def insert_into_redis(aprs_string):
        redis_client.set(f"ogn-python {datetime.utcnow()}", aprs_string.strip(), ex=100)
        insert_into_redis.beacon_counter += 1
        
        delta = (datetime.utcnow() - insert_into_redis.last_update).total_seconds()
        if delta >= 60.0:
            print(f"{insert_into_redis.beacon_counter/delta:05.1f}/s")
            insert_into_redis.last_update = datetime.utcnow()
            insert_into_redis.beacon_counter = 0
    
    insert_into_redis.beacon_counter = 0
    insert_into_redis.last_update = datetime.utcnow()

    try:
        client.run(callback=insert_into_redis, autoreconnect=True)
    except KeyboardInterrupt:
        current_app.logger.warning("\nStop ogn gateway")

    client.disconnect()

@user_cli.command("printout")
def printout():
    """Run the aprs client and just print out the data stream."""
    
    current_app.logger.warning("Start ogn gateway")
    client = AprsClient("anon-dev")
    client.connect()

    try:
        client.run(callback=lambda x: print(f"{datetime.utcnow()}: {x}"), autoreconnect=True)
    except KeyboardInterrupt:
        current_app.logger.warning("\nStop ogn gateway")

    client.disconnect()

@user_cli.command("convert")
@click.argument("path")
def file_import(path):
    """Convert APRS logfiles into csv files for fast bulk import."""

    for (root, dirs, files) in os.walk(path):
        for file in sorted(files):
            print(file)
            convert(os.path.join(root, file))


@user_cli.command("calculate")
@click.argument("path")
def file_calculate(path):
    """Import csv files, calculate geographic features (distance, radial, agl, ...) and make data distinct."""

    file_tuples = []
    for (root, dirs, files) in os.walk(path):
        for file in sorted(files):
            if file.startswith('aircraft_beacons') and file.endswith('.csv.gz'):
                ab_filename = os.path.join(root, file)
                rb_filename = os.path.join(root, 'receiver' + file[8:])
                target_filename = os.path.join(root, file + '2')
                if os.path.isfile(target_filename):
                    print("Outputfile {} already exists. Skipping".format(target_filename))
                else:
                    file_tuples.append((ab_filename, rb_filename, target_filename))

    pbar = tqdm(file_tuples)
    for file_tuple in pbar:
        pbar.set_description("Converting {}".format(file_tuple[0]))
        calculate(file_tuple[0], file_tuple[1], file_tuple[2])
