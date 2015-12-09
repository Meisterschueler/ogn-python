# ogn-python

[![Build Status](https://travis-ci.org/glidernet/ogn-python.svg?branch=master)]
(https://travis-ci.org/glidernet/ogn-python)
[![Coverage Status](https://img.shields.io/coveralls/glidernet/ogn-python.svg)]
(https://coveralls.io/r/glidernet/ogn-python)

A python module for the [Open Glider Network](http://wiki.glidernet.org/).
The submodule 'ogn.gateway' is an aprs client, saving all received beacons
into a database with [SQLAlchemy](http://www.sqlalchemy.org/).
Other submodules process this data.

To schedule tasks like fetching ddb data,
[Celery](http://www.celeryproject.org/) with [Redis](http://www.redis.io/) is used.


## Installation and Setup
1. Install python requirements

    ```
    pip install -r requirements.txt
    ```

2. Install redis for asynchronous tasks ('ogn.collect.\*')

    ```
    apt-get install redis-server
    ```

3. Create database

    ```
    ./manage.py db.init
    alembic stamp head
    ```

## Running the aprs client and task server
This scripts run in the foreground and should be deamonized
(eg. use [supervisord](http://supervisord.org/)).
```
# start aprs client
$ ./manage.py gateway.run

# start task server (make sure redis is up and running)
$ celery -A ogn.collect worker -l info
```

## manage.py - CLI options
```
usage: manage.py [<namespace>.]<command> [<args>]

positional arguments:
  command     the command to run

optional arguments:
  -h, --help  show this help message and exit

available commands:

  [db]
    import_ddb             Import registered devices from the DDB.
    import_file            Import registered devices from local file.
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
    list_all               Show a list of all receivers.
    software_stats         Show some statistics of receiver software.
```

Only the command `logbook.compute` requires a running task server (celery) at the moment.

## TODO
- [x] Write celery backend and add task 'fetchddb'
- [x] Rewrite manage.py with <https://github.com/Birdback/manage.py> or flask-script
- [x] Rename existing cli commands
- [x] Document/Improve cli commands
- [ ] Separate settings from module (currently at ogn/command/dbutils.py)
- [ ] Enable granular data acquisition (eg. store receiver beacons only)
- [x] Future Database-Migrations: Use Alembic?
  - [x] Rename 'Flarm' to 'Device'?
  - [x] Rename self.heared\_aircraft\_IDs (lowercase) in aircraft\_beacon
  - [x] Rename self.heared\_aircraft\_IDs
- [x] Fix command/logbook.py (@Meisterschueler?)
- [ ] Introduce scheduled tasks with 'celery beat' (eg. updateddb)

### Scheduled tasks
- ogn.collect.database
  - import_ddb - Import registered devices from the ddb
  - import_file - Import registered devices from a local file
- ogn.collect.receiver
  - populate - generate Receiver table (not implemented)
- ogn.collect.logbook
  - compute - generate TakeoffLanding table

## How to use virtualenv
```
$ sudo apt-get install python-virtualenv

$ virtualenv env
$ source env/bin/activate
