# ogn-python

[![Build Status](https://travis-ci.org/glidernet/ogn-python.svg?branch=master)](https://travis-ci.org/glidernet/ogn-python)
[![Coverage Status](https://img.shields.io/coveralls/glidernet/ogn-python.svg)](https://coveralls.io/r/glidernet/ogn-python)

A database backend for the [Open Glider Network](http://wiki.glidernet.org/).
The ogn-python module saves all received beacons into a database with [SQLAlchemy](http://www.sqlalchemy.org/).
It connects to the OGN aprs servers with [python-ogn-client](https://github.com/glidernet/python-ogn-client).
It requires [redis](http://redis.io), [PostgreSQL](http://www.postgresql.org/), [PostGIS](http://www.postgis.net/) and [TimescaleDB](https://www.timescale.com).

[Examples](https://github.com/glidernet/ogn-python/wiki/Examples)


## Installation and Setup
1. Checkout the repository

    ```
    git clone https://github.com/glidernet/ogn-python.git
    cd ogn-python
    ```

2. Optional: Create and use a virtual environment
    ```
    python3 -m venv my_environment
    source my_environment/bin/activate
    ```

3. Install python requirements

    ```
    pip install -r requirements.txt
    ```

4. Install [PostgreSQL](http://www.postgresql.org/) with [PostGIS](http://www.postgis.net/) and [TimescaleDB](https://www.timescale.com) Extension.
    Create a database (use "ogn" as default, otherwise you have to modify the configuration, see below)

5. Install redis for asynchronous tasks (like database feeding, takeoff/landing-detection, ...)

    ```
    apt-get install redis-server
    ```

6. Set the environment
  Your environment variables must point to the configuration file and to the app path.

    ```
    export OGN_CONFIG_MODULE="config.py"
    export FLASK_APP=ogn_python.py
    ```

7. Create database

    ```
    flask database init
    ```

8. Optional: Import world border dataset (needed if you want to know the country a receiver belongs to, etc.)
    Get the [World Borders Dataset](http://thematicmapping.org/downloads/world_borders.php) and unpack it.
    Then import it into your database (we use "ogn" as database name).
    
    ```
    shp2pgsql -s 4326 TM_WORLD_BORDERS-0.3.shp world_borders_temp | psql -d ogn
    psql -d ogn -c "INSERT INTO countries SELECT * FROM world_borders_temp;"
    psql -d ogn -c "DROP TABLE world_borders_temp;"
    ```
    
9. Get world elevation data (needed for AGL calculation)
	Sources: There are many sources for DEM data. It is important that the spatial reference system (SRID) is the same as the database which is 4326.
	The [GMTED2010 Viewer](https://topotools.cr.usgs.gov/gmted_viewer/viewer.htm) provides data for the world with SRID 4326. Just download the data you need.
    
    
10. Import the GeoTIFF into the elevation table:
    
    ```
    raster2pgsql *.tif -s 4326 -d -M -C -I -F -t 25x25 public.elevation | psql -d ogn
    ```

11. Import Airports (needed for takeoff and landing calculation). A cup file is provided under tests:
	
	```
	flask database import_airports tests/SeeYou.cup 
	```

12. Import DDB (needed for registration signs in the logbook).

	```
	flask database import_ddb
	```

13. Optional: Use supervisord
	You can use [Supervisor](http://supervisord.org/) to control the complete system. In the directory deployment/supervisor
	we have some configuration files to feed the database (ogn-feed), run the celery worker (celeryd), the celery beat
	(celerybeatd), the celery monitor (flower), and the python wsgi server (gunicorn). All files assume that
	we use a virtual environment in "/home/pi/ogn-python/venv". Please edit if necessary.

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
  flask gateway run
  ```

- Start a task server (make sure redis is up and running)

  ```
  celery -A celery_app worker -l info
  ```

- Start the task scheduler (make sure a task server is up and running)

  ```
  celery -A celery_app beat -l info
  ```

### Flask - Command Line Interface
```
Usage: flask [OPTIONS] COMMAND [ARGS]...

  A general utility script for Flask applications.

  Provides commands from Flask, extensions, and the application. Loads the
  application defined in the FLASK_APP environment variable, or from a
  wsgi.py file. Setting the FLASK_ENV environment variable to 'development'
  will enable debug mode.

    $ export FLASK_APP=app.py
    $ export FLASK_ENV=development
    $ flask run

Options:
  --version  Show the flask version
  --help     Show this message and exit.

Commands:
  database  Database creation and handling.
  db        Perform database migrations.
  export    Export data in several file formats.
  flights   Create 2D flight paths from data.
  gateway   Connection to APRS servers.
  logbook   Handling of takeoff/landings and logbook data.
  routes    Show the routes for the app.
  run       Run a development server.
  shell     Run a shell in the app context.
```

Most commands are command groups, so if you execute this command you will get further (sub)commands.

### Available tasks

- `app.tasks.transfer_to_database` - Take sender and receiver messages from redis and put them into the db.
- `app.tasks.update_takeoff_landings` - Compute takeoffs and landings.
- `app.tasks.update_logbook` - Add/update logbook entries.
- `app.tasks.update_logbook_max_altitude` - Add max altitudes in logbook when flight is complete (takeoff and landing).
- `app.tasks.update_statistics` - Calculate several statistics (also the sender/receiver rankings).
- `app.tasks.import_ddb` - Import registered devices from the DDB.

If the task server is up and running, tasks could be started manually. Here we compute takeoffs and landings for the past 90 minutes:

```
python3
>>>from app.tasks import update_takeoff_landings
>>>update_takeoff_landings.delay(last_minutes=90)
```

or directly from command line:

```
celery -A celery_app call import_ddb
```

## Notes for Raspberry Pi
For matplotlib we need several apt packages installed:

```
apt install libatlas3-base libopenjp2-7 libtiff5
```

## License
Licensed under the [AGPLv3](LICENSE).
