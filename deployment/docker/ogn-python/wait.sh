#!/usr/bin/env bash
# wait a bit for db and backend to properly start before running parms
echo Waiting for backend to start...
bash -c 'while !</dev/tcp/$BACKENDHOST/$BACKENDPORT; do sleep 1; done;' 2> /dev/null
$1 $2 $3 $4 $5 $6 $7 $8 $9