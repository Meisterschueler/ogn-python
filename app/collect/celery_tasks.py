from datetime import datetime

from flask import current_app

from app import create_app
from app import redis_client, celery

from app.gateway.bulkimport import DbFeeder


@celery.task(name="transfer_beacons_to_database")
def transfer_beacons_to_database():
    """Transfer beacons from redis to TimescaleDB."""

    counter = 0
    with DbFeeder() as feeder:
        for key in redis_client.scan_iter(match="ogn-python *"):
            value = redis_client.get(key)
            if value is None:
                redis_client.delete(key)
                continue
            
            reference_timestamp = datetime.strptime(key[11:].decode('utf-8'), "%Y-%m-%d %H:%M:%S.%f")
            aprs_string = value.decode('utf-8')
            redis_client.delete(key)
            
            feeder.add(aprs_string, reference_timestamp=reference_timestamp)
            counter += 1
    
    return f"Beacons transfered from redis to TimescaleDB: {counter}"

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        result = transfer_beacons_to_database.delay()
        print(result)
