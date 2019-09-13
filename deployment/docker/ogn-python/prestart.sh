#!/usr/bin/env bash
echo Waiting db to start...
bash -c 'while !</dev/tcp/$PGHOST/5432; do sleep 1; done;' 2> /dev/null
flask database init
flask database init_timescaledb
find /cups -name "*.cup" -exec flask database import_airports  {} \;
flask database import_ddb
