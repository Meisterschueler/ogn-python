# ogn-python

[![Build Status](https://travis-ci.org/glidernet/ogn-python.svg?branch=master)]
(https://travis-ci.org/glidernet/ogn-python)
[![Coverage Status](https://img.shields.io/coveralls/glidernet/ogn-python.svg)]
(https://coveralls.io/r/glidernet/ogn-python)
[![PyPi Version](https://img.shields.io/pypi/v/ogn-python.svg)]
(https://pypi.python.org/pypi/ogn-python)

A database backend for the [Open Glider Network](http://wiki.glidernet.org/).
The ogn-python module saves all received beacons into a database with [SQLAlchemy](http://www.sqlalchemy.org/).
It connects to the OGN aprs servers with [python-ogn-client](https://github.com/glidernet/python-ogn-client).
It requires [PostgreSQL](http://www.postgresql.org/) and [PostGIS](http://www.postgis.net/).

[Examples](https://github.com/glidernet/ogn-python/wiki/Examples)


## Installation and Setup
1. Checkout the repository

   ```
   git clone https://github.com/glidernet/ogn-python.git
   ```

2. Install python requirements

    ```
    pip install -r requirements.txt
    ```
3. Install [PostgreSQL](http://www.postgresql.org/) with [PostGIS](http://www.postgis.net/) Extension.
   Create a database (use "ogn" as default, otherwise you have to modify the configuration, see below)


4. Optional: Install redis for asynchronous tasks (like takeoff/landing-detection)

    ```
    apt-get install redis-server
    ```

5. Create database

    ```
    ./manage.py db.init
    ```

There is also a [Vagrant](https://www.vagrantup.com/) environment for the development of ogn-python.
You can create and start this virtual machine with `vagrant up` and login with `vagrant ssh`.
The code of ogn-python will be available in the shared folder `/vagrant`.

## Usage
### Running the aprs client and task server
To schedule tasks like takeoff/landing-detection (`logbook.compute`),
[Celery](http://www.celeryproject.org/) with [Redis](http://www.redis.io/) is used.
The following scripts run in the foreground and should be deamonized
(eg. use [supervisord](http://supervisord.org/)).

- Start the aprs client

  ```
  ./manage.py gateway.run
  ```

- Start a task server (make sure redis is up and running)

  ```
  celery -A ogn.collect worker -l info
  ```

- Start the task scheduler (make sure a task server is up and running)

  ```
  celery -A ogn.collect beat -l info
  ```


To load a custom configuration, create a file `myconfig.py` (see [config/default.py](config/default.py))
and set the environment variable `OGN_CONFIG_MODULE` accordingly.

```
touch myconfig.py
export OGN_CONFIG_MODULE="myconfig"
./manage.py gateway.run
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
    import_airports        Import airports from a ".cup" file
    import_ddb             Import registered devices from the DDB.
    import_file            Import registered devices from a local file.
    init                   Initialize the database.
    upgrade                Upgrade database to the latest version.

  [gateway]
    run                    Run the aprs client.

  [logbook]
    compute_logbook        Compute logbook.
    compute_takeoff_landingCompute takeoffs and landings.
    show                   Show a logbook for <airport_name>.

  [show.airport]
    list_all               Show a list of all airports.

  [show.deviceinfos]
    stats                  Show some stats on registered devices.

  [show.devices]
    aircraft_type_stats    Show stats about aircraft types used by devices.
    hardware_stats         Show stats about hardware version used by devices.
    software_stats         Show stats about software version used by devices.
    stealth_stats          Show stats about stealth flag set by devices.

  [show.receiver]
    hardware_stats         Show some statistics of receiver hardware.
    list_all               Show a list of all receivers.
    software_stats         Show some statistics of receiver software.
```

Only the command `logbook.compute` requires a running task server (celery) at the moment.


### Available tasks

- `ogn.collect.database.import_ddb` - Import registered devices from the ddb
- `ogn.collect.database.import_file` - Import registered devices from a local file
- `ogn.collect.receiver.update_receivers` - Populate/update receiver table
- `ogn.collect.logbook.compute_takeoff_and_landing` - Generate TakeoffLanding table

If the task server is up and running, tasks could be started manually.

```
python3
>>>from ogn.collect.database import import_ddb
>>>import_ddb.delay()
```

## License
Licensed under the [AGPLv3](LICENSE).
