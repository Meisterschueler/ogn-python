# ogn-python

[![Build Status](https://travis-ci.org/glidernet/ogn-python.svg?branch=master)]
(https://travis-ci.org/glidernet/ogn-python)
[![Coverage Status](https://img.shields.io/coveralls/glidernet/ogn-python.svg)]
(https://coveralls.io/r/glidernet/ogn-python)

A python module for the [Open Glider Network](http://wiki.glidernet.org/).
The submodule 'ogn.gateway' is an aprs client which could be invoked via a CLI
or used by other python projects.
The CLI allows to save all received beacons into a
[sqlite](https://www.sqlite.org/)-database with [SQLAlchemy](http://www.sqlalchemy.org/).
An external python project would instantiate ogn.gateway and register a custom callback,
called each time a beacon is received.

[Examples](https://github.com/glidernet/ogn-python/wiki/Examples)


## Usage - python module
Implement your own gateway by using ogn.gateway with a custom callback function.
Each time a beacon is received, this function gets called and
lets you process the incoming data.

Example:
```python
#!/usr/bin/env python3

from ogn.model import AircraftBeacon, ReceiverBeacon
from ogn.gateway.client import ognGateway


def process_beacon(beacon):
    if type(beacon) is AircraftBeacon:
        print('Received aircraft beacon from {}'.format(beacon.name))
    elif type(beacon) is ReceiverBeacon:
        print('Received receiver beacon from {}'.format(beacon.name))


if __name__ == '__main__':
    gateway = ognGateway(aprs_user='N0CALL')
    gateway.connect()

    try:
        gateway.run(callback=process_beacon, autoreconnect=True)
    except KeyboardInterrupt:
        print('\nStop ogn gateway')

    gateway.disconnect()
```


## Usage - CLI
### Installation and Setup
1. Checkout the repository

   ```
   git clone https://github.com/glidernet/ogn-python.git
   ```

2. Install python requirements

    ```
    pip install -r requirements.txt
    ```

3. Install redis for asynchronous tasks (like takeoff/landing-detection)

    ```
    apt-get install redis-server
    ```

4. Create database

    ```
    ./manage.py db.init
    ```

### Running the aprs client and task server
To schedule tasks like takeoff/landing-detection (`logbook.compute`),
[Celery](http://www.celeryproject.org/) with [Redis](http://www.redis.io/) is used.
The following scripts run in the foreground and should be deamonized
(eg. use [supervisord](http://supervisord.org/)).

- start aprs client

  ```
  ./manage.py gateway.run
  ```

- start task server (make sure redis is up and running)

  ```
  celery -A ogn.collect worker -l info
  ```

### manage.py - CLI options
```
usage: manage.py [<namespace>.]<command> [<args>]

positional arguments:
  command     the command to run

optional arguments:
  -h, --help  show this help message and exit

available commands:

  [db]
    drop                   Drop all tables.
    import_ddb             Import registered devices from the DDB.
    import_file            Import registered devices from a local file.
    init                   Initialize the database.

  [gateway]
    run                    Run the aprs client.

  [logbook]
    compute                Compute takeoffs and landings.
    show                   Show a logbook for <airport_name> located at given position.

  [show.devices]
    stats                  Show some stats on registered devices.

  [show.receiver]
    hardware_stats         Show some statistics of receiver hardware.
    list_all               Show a list of all receivers (NOT IMPLEMENTED).
    software_stats         Show some statistics of receiver software.
```

Only the command `logbook.compute` requires a running task server (celery) at the moment.


### Scheduled tasks
- ogn.collect.database
  - `import_ddb` - Import registered devices from the ddb
  - `import_file` - Import registered devices from a local file
- ogn.collect.receiver
  - `populate` - generate Receiver table (NOT IMPLEMENTED)
- ogn.collect.logbook
  - `compute_takeoff_and_landing` - generate TakeoffLanding table


## License
Licensed under the [AGPLv3](LICENSE).
