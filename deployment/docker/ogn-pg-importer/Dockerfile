FROM debian:bullseye-slim AS builder

RUN apt update && \
    apt install -y --no-install-recommends \
    wget unzip postgis

RUN wget --no-check-certificate -O borders.zip http://thematicmapping.org/downloads/TM_WORLD_BORDERS-0.3.zip && \
    unzip borders.zip -d /extra

WORKDIR /extra

RUN shp2pgsql -s 4326 TM_WORLD_BORDERS-0.3.shp world_borders_temp > world_borders_temp
COPY deployment/docker/ogn-pg-importer/docker-entrypoint.sh .
ENTRYPOINT [ "./docker-entrypoint.sh" ]
