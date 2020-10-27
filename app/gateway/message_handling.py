import os
import time
from io import StringIO

from app import db
from app.model import AircraftType
from app.utils import get_sql_trustworthy

basepath = os.path.dirname(os.path.realpath(__file__))

# define fields we want to proceed
SENDER_POSITION_BEACON_FIELDS = [
    "reference_timestamp",

    "name",
    "dstcall",
    "relay",
    "receiver_name",
    "timestamp",
    "location",
    
    "track",
    "ground_speed",
    "altitude",
    
    "address_type",
    "aircraft_type",
    "stealth",
    "address",
    "climb_rate",
    "turn_rate",
    "signal_quality",
    "error_count",
    "frequency_offset",
    "gps_quality_horizontal",
    "gps_quality_vertical",
    "software_version",
    "hardware_version",
    "real_address",
    "signal_power",
    
    "distance",
    "bearing",
    "normalized_quality",

    "location_mgrs",
    "location_mgrs_short",
    "agl",
]

RECEIVER_POSITION_BEACON_FIELDS = [
    "reference_timestamp",

    "name",
    "dstcall",
    "receiver_name",
    "timestamp",
    "location",

    "altitude",

    "location_mgrs",
    "location_mgrs_short",
    "agl",
]

RECEIVER_STATUS_BEACON_FIELDS = [
    "reference_timestamp",
    
    "name",
    "dstcall",
    "receiver_name",
    "timestamp",

    "version",
    "platform",

    "cpu_temp",
    "rec_input_noise",
]


def sender_position_message_to_csv_string(message, none_character=''):
    """
    Convert sender_position_messages to csv string.

    :param dict message: dict of sender position messages from the parser
    :param str none_character: '' for a file, '\\N' for Postgresql COPY
    """

    csv_string = "{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12},{13},{14},{15},{16},{17},{18},{19},{20},{21},{22},{23},{24},{25},{26},{27},{28},{29},{30}\n".format(
        message['reference_timestamp'],
        
        message['name'],
        message['dstcall'],
        message['relay'] if 'relay' in message and message['relay'] else none_character,
        message['receiver_name'],
        message['timestamp'],
        message['location'],

        message['track'] if 'track' in message and message['track'] else none_character,
        message['ground_speed'] if 'ground_speed' in message and message['ground_speed'] else none_character,
        int(message['altitude']) if message['altitude'] else none_character,
       
        message['address_type'] if 'address_type' in message and message['address_type'] else none_character,   #10
        message['aircraft_type'].name if 'aircraft_type' in message and message['aircraft_type'] else AircraftType.UNKNOWN.name,
        message['stealth'] if 'stealth' in message and message['stealth'] else none_character,
        message['address'] if 'address' in message and message['address'] else none_character,
        message['climb_rate'] if 'climb_rate' in message and message['climb_rate'] else none_character,
        message['turn_rate'] if 'turn_rate' in message and message['turn_rate'] else none_character,
        message['signal_quality'] if 'signal_quality' in message and message['signal_quality'] else none_character,
        message['error_count'] if 'error_count' in message and message['error_count'] else none_character,
        message['frequency_offset'] if 'frequency_offset' in message and message['frequency_offset'] else none_character,
        message['gps_quality_horizontal'] if 'gps_quality_horizontal' in message and message['gps_quality_horizontal'] else none_character,
        message['gps_quality_vertical'] if 'gps_quality_vertical' in message and message['gps_quality_vertical'] else none_character, #20
        message['software_version'] if 'software_version' in message and message['software_version'] else none_character,
        message['hardware_version'] if 'hardware_version' in message and message['hardware_version'] else none_character,
        message['real_address'] if 'real_address' in message and message['real_address'] else none_character,
        message['signal_power'] if 'signal_power' in message and message['signal_power'] else none_character,
        
        message['distance'] if 'distance' in message and message['distance'] else none_character,
        message['bearing'] if 'bearing' in message and message['bearing'] else none_character,
        message['normalized_quality'] if 'normalized_quality' in message and message['normalized_quality'] else none_character,

        message['location_mgrs'],
        message['location_mgrs_short'],
        message['agl'] if 'agl' in message else none_character,
    )
    return csv_string


def receiver_position_message_to_csv_string(message, none_character=''):
    csv_string = "{0},{1},{2},{3},{4},{5},{6},{7},{8},{9}\n".format(
        message['reference_timestamp'],
        
        message['name'],
        message['dstcall'],
        message['receiver_name'],
        message['timestamp'],
        message['location'],

        int(message['altitude']) if message['altitude'] else none_character,

        message['location_mgrs'],
        message['location_mgrs_short'],
        message['agl'] if 'agl' in message else none_character,
    )
    return csv_string


def receiver_status_message_to_csv_string(message, none_character=''):
    csv_string = "{0},{1},{2},{3},{4},{5},{6},{7},{8}\n".format(
        message['reference_timestamp'],

        message['name'],
        message['dstcall'],
        message['receiver_name'],
        message['timestamp'],

        message['version'] if 'version' in message else none_character,
        message['platform'] if 'platform' in message else none_character,

        message['cpu_temp'] if 'cpu_temp' in message else none_character,
        message['rec_input_noise'] if 'rec_input_noise' in message else none_character,

    )
    return csv_string


def sender_position_csv_strings_to_db(lines):
    timestamp_string = str(time.time()).replace('.', '_')
    tmp_tablename = f'sender_positions_{timestamp_string}'

    connection = db.engine.raw_connection()
    cursor = connection.cursor()

    string_buffer = StringIO()
    string_buffer.writelines(lines)
    string_buffer.seek(0)

    cursor.execute(f"CREATE TEMPORARY TABLE {tmp_tablename} (LIKE sender_positions) ON COMMIT DROP;")
    cursor.copy_from(file=string_buffer, table=tmp_tablename, sep=",", columns=SENDER_POSITION_BEACON_FIELDS)
    
    # Update agl
    cursor.execute(f"""
        UPDATE {tmp_tablename} AS tmp
        SET
            agl = tmp.altitude - ST_Value(e.rast, tmp.location)
        FROM elevation AS e
        WHERE ST_Intersects(tmp.location, e.rast);
    """)

    # Update sender position statistics
    cursor.execute(f"""
        INSERT INTO sender_position_statistics AS sps (date, dstcall, address_type, aircraft_type, stealth, software_version, hardware_version, messages_count)
        SELECT
            tmp.reference_timestamp::DATE AS date,
            tmp.dstcall,
            tmp.address_type,
            tmp.aircraft_type,
            tmp.stealth,
            tmp.software_version,
            tmp.hardware_version,
            COUNT(tmp.*) AS messages_count
        FROM {tmp_tablename} AS tmp
        GROUP BY date, dstcall, address_type, aircraft_type, stealth, software_version, hardware_version
        ON CONFLICT (date, dstcall, address_type, aircraft_type, stealth, software_version, hardware_version) DO UPDATE
        SET
            messages_count = EXCLUDED.messages_count + sps.messages_count;
    """)

    # Update senders
    cursor.execute(f"""
        INSERT INTO senders AS s (firstseen, lastseen, name, aircraft_type, stealth, address, software_version, hardware_version, real_address)
        SELECT DISTINCT ON (tmp.name)
            tmp.reference_timestamp AS firstseen,
            tmp.reference_timestamp AS lastseen,

            tmp.name,

            tmp.aircraft_type,
            tmp.stealth,
            tmp.address,
            tmp.software_version,
            tmp.hardware_version,
            tmp.real_address
        FROM {tmp_tablename} AS tmp
        WHERE tmp.name NOT LIKE 'RND%'
        ON CONFLICT (name) DO UPDATE
        SET
            lastseen = GREATEST(EXCLUDED.lastseen, s.lastseen),
            aircraft_type = EXCLUDED.aircraft_type,
            stealth = EXCLUDED.stealth,
            address = EXCLUDED.address,
            software_version = COALESCE(EXCLUDED.software_version, s.software_version),
            hardware_version = COALESCE(EXCLUDED.hardware_version, s.hardware_version),
            real_address = COALESCE(EXCLUDED.real_address, s.real_address);
    """)

    # Update sender_infos FK -> senders
    cursor.execute(f"""
        UPDATE sender_infos AS si
        SET sender_id = s.id
        FROM senders AS s
        WHERE si.sender_id IS NULL AND s.address = si.address;
    """)

    SQL_TRUSTWORTHY = get_sql_trustworthy(source_table_alias='tmp')

    # Update coverage statistics
    cursor.execute(f"""
        INSERT INTO coverage_statistics AS rs (date, location_mgrs_short, sender_id, receiver_id, is_trustworthy, max_distance, max_normalized_quality, messages_count)
        SELECT
            tmp.reference_timestamp::DATE AS date,
            tmp.location_mgrs_short,
            tmp.sender_id,
            tmp.receiver_id,

            ({SQL_TRUSTWORTHY}) AS is_trustworthy,

            MAX(tmp.distance) AS max_distance,
            MAX(tmp.normalized_quality) AS max_normalized_quality,
            COUNT(tmp.*) AS messages_count
        FROM (SELECT x.*, s.id AS sender_id, r.id AS receiver_id FROM {tmp_tablename} AS x INNER JOIN senders AS s ON x.name = s.name INNER JOIN receivers AS r ON x.receiver_name = r.name) AS tmp
        GROUP BY date, location_mgrs_short, sender_id, receiver_id, is_trustworthy
        ON CONFLICT (date, location_mgrs_short, sender_id, receiver_id, is_trustworthy) DO UPDATE
        SET
            max_distance = GREATEST(EXCLUDED.max_distance, rs.max_distance),
            max_normalized_quality = GREATEST(EXCLUDED.max_normalized_quality, rs.max_normalized_quality),
            messages_count = EXCLUDED.messages_count + rs.messages_count;
    """)

    # Insert all the beacons
    all_fields = ', '.join(SENDER_POSITION_BEACON_FIELDS)
    cursor.execute(f"""
        INSERT INTO sender_positions ({all_fields})
        SELECT {all_fields} FROM {tmp_tablename};
    """)

    connection.commit()

    cursor.close()
    connection.close()


def receiver_position_csv_strings_to_db(lines):
    timestamp_string = str(time.time()).replace('.', '_')
    tmp_tablename = f'receiver_positions_{timestamp_string}'

    connection = db.engine.raw_connection()
    cursor = connection.cursor()

    string_buffer = StringIO()
    string_buffer.writelines(lines)
    string_buffer.seek(0)

    cursor.execute(f"CREATE TEMPORARY TABLE {tmp_tablename} (LIKE receiver_positions) ON COMMIT DROP;")
    cursor.copy_from(file=string_buffer, table=tmp_tablename, sep=",", columns=RECEIVER_POSITION_BEACON_FIELDS)

    # Update agl
    cursor.execute(f"""
        UPDATE {tmp_tablename} AS tmp
        SET
            agl = tmp.altitude - ST_Value(e.rast, tmp.location)
        FROM elevation AS e
        WHERE ST_Intersects(tmp.location, e.rast);
    """)

    # Update receivers
    cursor.execute(f"""
        INSERT INTO receivers AS r (firstseen, lastseen, name, timestamp, location, altitude, agl)
        SELECT DISTINCT ON (tmp.name)
            tmp.reference_timestamp AS firstseen,
            tmp.reference_timestamp AS lastseen,

            tmp.name,
            tmp.timestamp,
            tmp.location,
            
            tmp.altitude,

            tmp.agl
        FROM {tmp_tablename} AS tmp,
        (
            SELECT
                tmp.name,
                MAX(timestamp) AS timestamp
            FROM {tmp_tablename} AS tmp
            GROUP BY tmp.name
        ) AS sq
        WHERE tmp.name = sq.name AND tmp.timestamp = sq.timestamp AND tmp.name NOT LIKE 'RND%'
        ON CONFLICT (name) DO UPDATE
        SET
            lastseen = EXCLUDED.lastseen,
            timestamp = EXCLUDED.timestamp,
            location = EXCLUDED.location,
            altitude = EXCLUDED.altitude,

            agl = EXCLUDED.agl;
    """)

    # Update receiver country and nearest airport
    cursor.execute(f"""
        UPDATE receivers AS r
        SET 
            country_id = c.gid,
            airport_id = (
                SELECT id
                FROM airports AS a
                WHERE
                    ST_Contains(a.border, r.location)
                    AND a.style IN (2,4,5)
                ORDER BY ST_DistanceSphere(a.location, r.location)
                LIMIT 1
            )
        FROM countries AS c
        WHERE r.country_id IS NULL AND ST_Within(r.location, c.geom);
    """)

    # Insert all the beacons
    all_fields = ', '.join(RECEIVER_POSITION_BEACON_FIELDS)
    cursor.execute(f"""
        INSERT INTO receiver_positions ({all_fields})
        SELECT {all_fields} FROM {tmp_tablename};
    """)

    connection.commit()

    cursor.close()
    connection.close()


def receiver_status_csv_strings_to_db(lines):
    timestamp_string = str(time.time()).replace('.', '_')
    tmp_tablename = f'receiver_status_{timestamp_string}'

    connection = db.engine.raw_connection()
    cursor = connection.cursor()

    string_buffer = StringIO()
    string_buffer.writelines(lines)
    string_buffer.seek(0)

    cursor.execute(f"CREATE TEMPORARY TABLE {tmp_tablename} (LIKE receiver_statuses) ON COMMIT DROP;")
    cursor.copy_from(file=string_buffer, table=tmp_tablename, sep=",", columns=RECEIVER_STATUS_BEACON_FIELDS)

    # Update receivers
    cursor.execute(f"""
        INSERT INTO receivers AS r (firstseen, lastseen, name, timestamp, version, platform, cpu_temp, rec_input_noise)
        SELECT DISTINCT ON (tmp.name)
            tmp.reference_timestamp AS firstseen,
            tmp.reference_timestamp AS lastseen,

            tmp.name,
            tmp.timestamp,
            
            tmp.version,
            tmp.platform,

            tmp.cpu_temp,
            tmp.rec_input_noise
        FROM {tmp_tablename} AS tmp,
        (
            SELECT
                tmp.name,
                MAX(timestamp) AS timestamp
            FROM {tmp_tablename} AS tmp
            GROUP BY tmp.name
        ) AS sq
        WHERE tmp.name = sq.name AND tmp.timestamp = sq.timestamp
        ON CONFLICT (name) DO UPDATE
        SET
            lastseen = EXCLUDED.lastseen,
            timestamp = EXCLUDED.timestamp,
            version = EXCLUDED.version,
            platform = EXCLUDED.platform,
            cpu_temp = EXCLUDED.cpu_temp,
            rec_input_noise = EXCLUDED.rec_input_noise;
    """)

    # Insert all the beacons
    all_fields = ', '.join(RECEIVER_STATUS_BEACON_FIELDS)
    cursor.execute(f"""
        INSERT INTO receiver_statuses ({all_fields})
        SELECT {all_fields} FROM {tmp_tablename};
    """)

    connection.commit()

    cursor.close()
    connection.close()
