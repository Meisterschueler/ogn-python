from ogn_python import db

def create_tables(postfix):
    """Create tables for log file import."""

    db.session.execute('DROP TABLE IF EXISTS "aircraft_beacons_{0}"; CREATE TABLE aircraft_beacons_{0} AS TABLE aircraft_beacons WITH NO DATA;'.format(postfix))
    db.session.execute('DROP TABLE IF EXISTS "receiver_beacons_{0}"; CREATE TABLE receiver_beacons_{0} AS TABLE receiver_beacons WITH NO DATA;'.format(postfix))
    db.session.commit()


def create_indices(postfix):
    """Creates indices for aircraft- and receiver-beacons."""

    db.session.execute("""
        CREATE INDEX IF NOT EXISTS ix_aircraft_beacons_{0}_device_id ON "aircraft_beacons_{0}" (device_id NULLS FIRST);
        CREATE INDEX IF NOT EXISTS ix_aircraft_beacons_{0}_receiver_id ON "aircraft_beacons_{0}" (receiver_id NULLS FIRST);
        CREATE INDEX IF NOT EXISTS ix_aircraft_beacons_{0}_timestamp_name_receiver_name ON "aircraft_beacons_{0}" (timestamp, name, receiver_name);
        CREATE INDEX IF NOT EXISTS ix_receiver_beacons_{0}_timestamp_name_receiver_name ON "receiver_beacons_{0}" (timestamp, name, receiver_name);
    """.format(postfix))
    db.session.commit()


def create_indices_bigdata(postfix):
    """Creates indices for aircraft- and receiver-beacons."""

    db.session.execute("""
        CREATE INDEX IF NOT EXISTS ix_aircraft_beacons_{0}_timestamp_name_receiver_name ON "aircraft_beacons_{0}" (timestamp, name, receiver_name);
        CREATE INDEX IF NOT EXISTS ix_receiver_beacons_{0}_timestamp_name_receiver_name ON "receiver_beacons_{0}" (timestamp, name, receiver_name);
    """.format(postfix))
    db.session.commit()


def add_missing_devices(postfix):
    """Add missing devices."""

    db.session.execute("""
        INSERT INTO devices(address)
        SELECT DISTINCT (ab.address)
        FROM "aircraft_beacons_{0}" AS ab
        WHERE ab.address IS NOT NULL AND NOT EXISTS (SELECT 1 FROM devices AS d WHERE d.address = ab.address)
        ORDER BY ab.address;
    """.format(postfix))
    db.session.commit()


def add_missing_receivers(postfix):
    """Add missing receivers."""

    db.session.execute("""
        INSERT INTO receivers(name)
        SELECT DISTINCT (rb.name)
        FROM "receiver_beacons_{0}" AS rb
        WHERE NOT EXISTS (SELECT 1 FROM receivers AS r WHERE r.name = rb.name)
        ORDER BY rb.name;

        INSERT INTO receivers(name)
        SELECT DISTINCT (ab.receiver_name)
        FROM "aircraft_beacons_{0}" AS ab
        WHERE NOT EXISTS (SELECT 1 FROM receivers AS r WHERE r.name = ab.receiver_name)
        ORDER BY ab.receiver_name;
    """.format(postfix))
    db.session.commit()


def update_receiver_location(postfix):
    """Updates the receiver location. We need this because we want the actual location for distance calculations."""

    db.session.execute("""
        UPDATE receivers AS r
        SET
            location = sq.location,
            altitude = sq.altitude
        FROM (
            SELECT DISTINCT ON (rb.receiver_id) rb.receiver_id, rb.location, rb.altitude
            FROM "receiver_beacons_{0}" AS rb
            WHERE rb.location IS NOT NULL
            ORDER BY rb.receiver_id, rb.timestamp
            ) AS sq
        WHERE r.id = sq.receiver_id;
    """.format(postfix))
    db.session.commit()


def update_receiver_beacons(postfix):
    """Updates the foreign keys."""

    db.session.execute("""
        UPDATE receiver_beacons_{0} AS rb
        SET receiver_id = r.id
        FROM receivers AS r
        WHERE rb.receiver_id IS NULL AND rb.name = r.name;
    """.format(postfix))
    db.session.commit()


def update_receiver_beacons_bigdata(postfix):
    """Updates the foreign keys.
       Due to performance reasons we use a new table instead of updating the old."""

    db.session.execute("""
        SELECT
            rb.location, rb.altitude, rb.name, rb.receiver_name, rb.dstcall, rb.timestamp,

            rb.version, rb.platform, rb.cpu_load, rb.free_ram, rb.total_ram, rb.ntp_error, rb.rt_crystal_correction, rb.voltage, rb.amperage,
            rb.cpu_temp, rb.senders_visible, rb.senders_total, rb.rec_input_noise, rb.senders_signal, rb.senders_messages, rb.good_senders_signal,
            rb.good_senders, rb.good_and_bad_senders,

            r.id AS receiver_id
        INTO "receiver_beacons_{0}_temp"
        FROM "receiver_beacons_{0}" AS rb, receivers AS r
        WHERE rb.name = r.name;

        DROP TABLE IF EXISTS "receiver_beacons_{0}";
        ALTER TABLE "receiver_beacons_{0}_temp" RENAME TO "receiver_beacons_{0}";
    """.format(postfix))
    db.session.commit()


def update_aircraft_beacons(postfix):
    """Updates the foreign keys and calculates distance/radial and quality and computes the altitude above ground level.
       Elevation data has to be in the table 'elevation' with srid 4326."""

    db.session.execute("""
        UPDATE aircraft_beacons_{0} AS ab
        SET
            device_id = d.id,
            receiver_id = r.id,
            distance = CASE WHEN ab.location IS NOT NULL AND r.location IS NOT NULL THEN CAST(ST_DistanceSphere(ab.location, r.location) AS REAL) ELSE NULL END,
            radial = CASE WHEN ab.location IS NOT NULL AND r.location IS NOT NULL THEN CAST(degrees(ST_Azimuth(ab.location, r.location)) AS SMALLINT) ELSE NULL END,
            quality = CASE WHEN ab.location IS NOT NULL AND r.location IS NOT NULL AND ST_DistanceSphere(ab.location, r.location) > 0 AND ab.signal_quality IS NOT NULL
                        THEN CAST(signal_quality + 20*log(ST_DistanceSphere(ab.location, r.location)/10000) AS REAL)
                        ELSE NULL
            END

        FROM devices AS d, receivers AS r
        WHERE ab.device_id IS NULL and ab.receiver_id IS NULL AND ab.address = d.address AND ab.receiver_name = r.name;
    """.format(postfix))
    db.session.commit()


def update_aircraft_beacons_bigdata(postfix):
    """Updates the foreign keys and calculates distance/radial and quality and computes the altitude above ground level.
       Elevation data has to be in the table 'elevation' with srid 4326.
       Due to performance reasons we use a new table instead of updating the old."""

    db.session.execute("""
        SELECT
            ab.location, ab.altitude, ab.name, ab.dstcall, ab.relay, ab.receiver_name, ab.timestamp, ab.track, ab.ground_speed,

            ab.address_type, ab.aircraft_type, ab.stealth, ab.address, ab.climb_rate, ab.turn_rate, ab.signal_quality, ab.error_count,
            ab.frequency_offset, ab.gps_quality_horizontal, ab.gps_quality_vertical, ab.software_version, ab.hardware_version, ab.real_address, ab.signal_power,

            ab.location_mgrs,
            ab.location_mgrs_short,

            d.id AS device_id,
            r.id AS receiver_id,
            CASE WHEN ab.location IS NOT NULL AND r.location IS NOT NULL THEN CAST(ST_DistanceSphere(ab.location, r.location) AS REAL) ELSE NULL END AS distance,
            CASE WHEN ab.location IS NOT NULL AND r.location IS NOT NULL THEN CAST(degrees(ST_Azimuth(ab.location, r.location)) AS SMALLINT) ELSE NULL END AS radial,
            CASE WHEN ab.location IS NOT NULL AND r.location IS NOT NULL AND ST_DistanceSphere(ab.location, r.location) > 0 AND ab.signal_quality IS NOT NULL
                 THEN CAST(signal_quality + 20*log(ST_DistanceSphere(ab.location, r.location)/10000) AS REAL)
                 ELSE NULL
            END AS quality,
            CAST(ab.altitude - ST_Value(e.rast, ab.location) AS REAL) AS agl

        INTO "aircraft_beacons_{0}_temp"
        FROM "aircraft_beacons_{0}" AS ab, devices AS d, receivers AS r, elevation AS e
        WHERE ab.address = d.address AND receiver_name = r.name AND ST_Intersects(e.rast, ab.location);

        DROP TABLE IF EXISTS "aircraft_beacons_{0}";
        ALTER TABLE "aircraft_beacons_{0}_temp" RENAME TO "aircraft_beacons_{0}";
    """.format(postfix))
    db.session.commit()


def delete_receiver_beacons(postfix):
    """Delete beacons from table."""

    db.session.execute("""
        DELETE FROM receiver_beacons_continuous_import AS rb
        USING (
            SELECT name, receiver_name, timestamp
            FROM receiver_beacons_continuous_import
            WHERE receiver_id IS NOT NULL
        ) AS sq
        WHERE rb.name = sq.name AND rb.receiver_name = sq.receiver_name AND rb.timestamp = sq.timestamp
    """.format(postfix))
    db.session.commit()


def delete_aircraft_beacons(postfix):
    """Delete beacons from table."""

    db.session.execute("""
        DELETE FROM aircraft_beacons_continuous_import AS ab
        USING (
            SELECT name, receiver_name, timestamp
            FROM aircraft_beacons_continuous_import
            WHERE receiver_id IS NOT NULL and device_id IS NOT NULL
        ) AS sq
        WHERE ab.name = sq.name AND ab.receiver_name = sq.receiver_name AND ab.timestamp = sq.timestamp
    """.format(postfix))
    db.session.commit()


def get_merged_aircraft_beacons_subquery(postfix):
    """Some beacons are split into position and status beacon. With this query we merge them into one beacon."""

    return """
    SELECT
        ST_AsEWKT(MAX(location)) AS location,
        MAX(altitude)  AS altitude,
        name,
        MAX(dstcall) AS dstcall,
        MAX(relay) AS relay,
        receiver_name,
        timestamp,
        MAX(track) AS track,
        MAX(ground_speed) AS ground_speed,

        MAX(address_type) AS address_type,
        MAX(aircraft_type) AS aircraft_type,
        CAST(MAX(CAST(stealth AS int)) AS boolean) AS stealth,
        MAX(address) AS address,
        MAX(climb_rate) AS climb_rate,
        MAX(turn_rate) AS turn_rate,
        MAX(signal_quality) AS signal_quality,
        MAX(error_count) AS error_count,
        MAX(frequency_offset) AS frequency_offset,
        MAX(gps_quality_horizontal) AS gps_quality_horizontal,
        MAX(gps_quality_vertical) AS gps_quality_vertical,
        MAX(software_version) AS software_version,
        MAX(hardware_version) AS hardware_version,
        MAX(real_address) AS real_address,
        MAX(signal_power) AS signal_power,

        CAST(MAX(distance) AS REAL) AS distance,
        CAST(MAX(radial) AS REAL) AS radial,
        CAST(MAX(quality) AS REAL) AS quality,
        CAST(MAX(agl) AS REAL) AS agl,
        MAX(location_mgrs) AS location_mgrs,
        MAX(location_mgrs_short) AS location_mgrs_short,

        MAX(receiver_id) AS receiver_id,
        MAX(device_id) AS device_id
    FROM "aircraft_beacons_{0}" AS ab
    GROUP BY timestamp, name, receiver_name
    ORDER BY timestamp, name, receiver_name
    """.format(postfix)


def get_merged_receiver_beacons_subquery(postfix):
    """Some beacons are split into position and status beacon. With this query we merge them into one beacon."""

    return """
    SELECT
        ST_AsEWKT(MAX(location)) AS location,
        MAX(altitude) AS altitude,
        name,
        receiver_name,
        MAX(dstcall) AS dstcall,
        timestamp,

        MAX(version) AS version,
        MAX(platform) AS platform,
        MAX(cpu_load) AS cpu_load,
        MAX(free_ram) AS free_ram,
        MAX(total_ram) AS total_ram,
        MAX(ntp_error) AS ntp_error,
        MAX(rt_crystal_correction) AS rt_crystal_correction,
        MAX(voltage) AS voltage,
        MAX(amperage) AS amperage,
        MAX(cpu_temp) AS cpu_temp,
        MAX(senders_visible) AS senders_visible,
        MAX(senders_total) AS senders_total,
        MAX(rec_input_noise) AS rec_input_noise,
        MAX(senders_signal) AS senders_signal,
        MAX(senders_messages) AS senders_messages,
        MAX(good_senders_signal) AS good_senders_signal,
        MAX(good_senders) AS good_senders,
        MAX(good_and_bad_senders) AS good_and_bad_senders,

        MAX(receiver_id) AS receiver_id
    FROM "receiver_beacons_{0}" AS rb
    GROUP BY timestamp, name, receiver_name
    ORDER BY timestamp, name, receiver_name
    """.format(postfix)


def transfer_aircraft_beacons(postfix):
    query = """
    INSERT INTO aircraft_beacons(location, altitude, name, dstcall, relay, receiver_name, timestamp, track, ground_speed,
        address_type, aircraft_type, stealth, address, climb_rate, turn_rate, signal_quality, error_count, frequency_offset, gps_quality_horizontal, gps_quality_vertical, software_version, hardware_version, real_address, signal_power,
        distance, radial, quality, agl, location_mgrs, location_mgrs_short,
        receiver_id, device_id)
    SELECT sq.*
    FROM ({}) sq
    WHERE sq.receiver_id IS NOT NULL AND sq.device_id IS NOT NULL
    ON CONFLICT DO NOTHING;
    """.format(get_merged_aircraft_beacons_subquery(postfix))

    db.session.execute(query)
    db.session.commit()


def transfer_receiver_beacons(postfix):
    query = """
    INSERT INTO receiver_beacons(location, altitude, name, receiver_name, dstcall, timestamp,

        version, platform, cpu_load, free_ram, total_ram, ntp_error, rt_crystal_correction, voltage,
        amperage, cpu_temp, senders_visible, senders_total, rec_input_noise, senders_signal,
        senders_messages, good_senders_signal, good_senders, good_and_bad_senders,

        receiver_id)
    SELECT sq.*
    FROM ({}) sq
    WHERE sq.receiver_id IS NOT NULL
    ON CONFLICT DO NOTHING;
    """.format(get_merged_receiver_beacons_subquery(postfix))

    db.session.execute(query)
    db.session.commit()
