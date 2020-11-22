import os
from datetime import datetime, timezone
import time

from flask import current_app
from flask.cli import AppGroup
import click
from tqdm import tqdm

from ogn.client import AprsClient

from app import redis_client
from app.gateway.beacon_conversion import aprs_string_to_message
from app.gateway.message_handling import receiver_status_message_to_csv_string, receiver_position_message_to_csv_string, sender_position_message_to_csv_string
from app.collect.gateway import transfer_from_redis_to_database

user_cli = AppGroup("gateway")
user_cli.help = "Connection to APRS servers."


@user_cli.command("run")
@click.option("--aprs_filter", default='')
def run(aprs_filter):
    """
    Run the aprs client, parse the incoming data and put it to redis.
    """

    import logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(name)-17s %(levelname)-8s %(message)s')

    current_app.logger.warning("Start ogn gateway")
    client = AprsClient(current_app.config['APRS_USER'], aprs_filter)
    client.connect()

    def insert_into_redis(aprs_string):
        # Convert aprs_string to message dict, add MGRS Position, flatten gps precision, etc. etc. ...
        message = aprs_string_to_message(aprs_string)
        if message is None:
            return

        # separate between tables (receiver/sender) and aprs_type (status/position)
        if message['beacon_type'] in ('aprs_receiver', 'receiver'):
            if message['aprs_type'] == 'status':
                redis_target = 'receiver_status'
                csv_string = receiver_status_message_to_csv_string(message, none_character=r'\N')
            elif message['aprs_type'] == 'position':
                redis_target = 'receiver_position'
                csv_string = receiver_position_message_to_csv_string(message, none_character=r'\N')
            else:
                return
        else:
            if message['aprs_type'] == 'status':
                return  # no interesting data we want to keep
            elif message['aprs_type'] == 'position':
                redis_target = 'sender_position'
                csv_string = sender_position_message_to_csv_string(message, none_character=r'\N')
            else:
                return

        mapping = {csv_string: str(time.time())}

        redis_client.zadd(name=redis_target, mapping=mapping, nx=True)
        insert_into_redis.beacon_counter += 1

        current_minute = datetime.utcnow().minute
        if current_minute != insert_into_redis.last_minute:
            current_app.logger.info(f"{insert_into_redis.beacon_counter:7d}/min")
            insert_into_redis.beacon_counter = 0
        insert_into_redis.last_minute = current_minute

    insert_into_redis.beacon_counter = 0
    insert_into_redis.last_minute = datetime.utcnow().minute

    try:
        client.run(callback=insert_into_redis, autoreconnect=True)
    except KeyboardInterrupt:
        current_app.logger.warning("\nStop ogn gateway")

    client.disconnect()


@user_cli.command("transfer")
def transfer():
    """Transfer data from redis to the database."""

    transfer_from_redis_to_database()


@user_cli.command("printout")
@click.option("--aprs_filter", default='')
def printout(aprs_filter):
    """Run the aprs client and just print out the data stream."""

    current_app.logger.warning("Start ogn gateway")
    client = AprsClient(current_app.config['APRS_USER'], aprs_filter=aprs_filter)
    client.connect()

    try:
        client.run(callback=lambda x: print(f"{datetime.utcnow()}: {x}"), autoreconnect=True)
    except KeyboardInterrupt:
        current_app.logger.warning("\nStop ogn gateway")

    client.disconnect()
