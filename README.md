# ogn-python

[![Build Status](https://travis-ci.org/Meisterschueler/ogn-python.svg?branch=master)]
(https://travis-ci.org/Meisterschueler/ogn-python)
[![Coverage Status](https://img.shields.io/coveralls/Meisterschueler/ogn-python.svg)]
(https://coveralls.io/r/Meisterschueler/ogn-python)

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
$ apt-get install redis-server
```

3. Create database
```
$ ./manage.py db.init
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
    init                   Initialize the database.
    updateddb              Update the ddb data.

  [gateway]
    run                    Run the aprs client.

  [logbook]
    show                   Show a logbook for <airport_name> located at given position.

  [show.receiver]
    hardware_stats         Show some statistics of receiver hardware.
    list                   Show a list of all receivers.
    software_stats         Show some statistics of receiver sotware.
```

The task server must be running for `db.updateddb`.

## TODO
- [x] Write celery backend and add task 'fetchddb'
- [x] Rewrite manage.py with <https://github.com/Birdback/manage.py> or flask-script
- [x] Rename existing cli commands
- [x] Document/Improve cli commands
- [ ] Separate settings from module (currently at ogn/command/dbutils.py)
- [ ] Enable granular data acquisition (eg. store receiver beacons only)
- [ ] Database: Rename 'Flarm' to 'Device'?
- [ ] Future Database-Migrations: Use Alembric?
- [ ] Fix command/logbook.py (@Meisterschueler?)
- [ ] Introduce scheduled tasks with 'celery beat' (eg. updateddb)

### Scheduled tasks
- ogn.collect.fetchddb (generate Flarm table)
- ogn.collect.receiver (generate Receiver table)
- ogn.collect.logbook  (generate TaoffLanding table)

## How to use virtualenv
```
$ sudo apt-get install python-virtualenv

$ virtualenv env
$ source env/bin/activate
