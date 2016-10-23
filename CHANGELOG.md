# CHANGELOG

## Unreleased

## 0.3.0 - 2016-10-22
- Changed database for OGN v0.2.5 receiver beacons
- Moved to PostGIS, PostgreSQL is now mandantory
- Changed database schema (added airport, added relations, added `aircraft_type`, removed unused fields)
- Added Airport manager with command line option `db.import_airports`,
  default is WELT2000
- Logbook: instead of lat, lon and name of the airport just pass the name
- Logbook: optional utc offset, optional single day selection
- Logbook: remark if different airport is used for takeoff or landing
- Logbook: several accuracy and speed improvements
- DDB: consider `aircraft_type`
- Moved exceptions from `ogn.exceptions` to `ogn.parser.exceptions`
- Moved parsing from `ogn.model.*` to `ogn.parser`
- Moved the APRS- & OGN-Parser, the APRS-client and the DDB-client to [python-ogn-client](https://github.com/glidernet/python-ogn-client)

## 0.2.1 - 2016-02-17
First and last release via PyPI.
- Added CHANGELOG.

## 0.2
- Changed database schema.
- Changed aprs app name to 'ogn-gateway-python'.
- Moved repository to github-organisation glidernet.
- Added exception handling to the packet parser.
- Added some tests for ogn.gateway.client.
- Added setup.py to build this package.
- Added configuration via python modules.
- Added scheduled tasks with celery.
- Renamed command line option `db.updateddb` to `db.import_ddb`.
- Added command line options `db.drop`, `db.import_file`, `db.upgrade`,
  `logbook.compute` and `show.devices.stats`.

## 0.1
Initial version.
