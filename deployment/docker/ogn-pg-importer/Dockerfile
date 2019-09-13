FROM alpine as builder
RUN apk update && apk add wget && rm -rf /var/cache/apk/*
RUN wget --no-check-certificate -O borders.zip http://thematicmapping.org/downloads/TM_WORLD_BORDERS-0.3.zip
RUN unzip borders.zip

# We use the postgis image because it includes shp2pgsql
FROM mdillon/postgis:11
RUN mkdir /extra
WORKDIR /extra
COPY --from=builder /TM_* /extra/
RUN shp2pgsql -s 4326 TM_WORLD_BORDERS-0.3.shp world_borders_temp > world_borders_temp 
COPY deployment/docker/ogn-pg-importer/docker-entrypoint.sh .
ENTRYPOINT [ "./docker-entrypoint.sh" ]