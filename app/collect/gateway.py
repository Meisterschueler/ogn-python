from datetime import datetime
from flask import current_app

from app import redis_client
from app.gateway.message_handling import sender_position_csv_strings_to_db, receiver_position_csv_strings_to_db, receiver_status_csv_strings_to_db

def transfer_from_redis_to_database():
    unmapping = lambda s: s[0].decode('utf-8')

    receiver_status_data = list(map(unmapping, redis_client.zpopmin('receiver_status', 100000)))
    receiver_position_data = list(map(unmapping, redis_client.zpopmin('receiver_position', 100000)))
    sender_status_data = list(map(unmapping, redis_client.zpopmin('sender_status', 100000)))
    sender_position_data = list(map(unmapping, redis_client.zpopmin('sender_position', 100000)))

    receiver_status_csv_strings_to_db(lines=receiver_status_data)
    receiver_position_csv_strings_to_db(lines=receiver_position_data)
    sender_position_csv_strings_to_db(lines=sender_position_data)

    current_app.logger.debug(f"transfer_from_redis_to_database: rx_stat: {len(receiver_status_data):6d}\trx_pos: {len(receiver_position_data):6d}\ttx_stat: {len(sender_status_data):6d}\ttx_pos: {len(sender_position_data):6d}")

    finish_message = f"Database: {len(receiver_status_data)+len(receiver_position_data)+len(sender_status_data)+len(sender_position_data)} inserted"
    return finish_message
