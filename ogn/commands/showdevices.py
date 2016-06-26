from ogn.commands.dbutils import session
from ogn.model import Device, AircraftType
from sqlalchemy import func

from manager import Manager
manager = Manager()


@manager.command
def aircraft_type_stats():
    """Show stats about aircraft types used by devices."""
    aircraft_type_query = session.query(Device.aircraft_type,
                                        func.count(Device.id)) \
                                 .group_by(Device.aircraft_type) \
                                 .order_by(func.count(Device.id).desc())
    print("--- Aircraft types ---")
    for [aircraft_type, count] in aircraft_type_query.all():
        at = AircraftType(aircraft_type)
        print("{}: {}".format(at.name(), count))


@manager.command
def stealth_stats():
    """Show stats about stealth flag set by devices."""
    stealth_query = session.query(Device.stealth,
                                  func.count(Device.id)) \
                           .group_by(Device.stealth) \
                           .order_by(func.count(Device.id).desc())
    print("--- Stealth ---")
    for [is_stealth, count] in stealth_query.all():
        print("{}: {}".format(is_stealth, count))


@manager.command
def software_stats():
    """Show stats about software version used by devices."""
    software_query = session.query(Device.software_version,
                                   func.count(Device.id)) \
                            .group_by(Device.software_version) \
                            .order_by(func.count(Device.id).desc())
    print("--- Software version ---")
    for [software_version, count] in software_query.all():
        print("{}: {}".format(software_version, count))


@manager.command
def hardware_stats():
    """Show stats about hardware version used by devices."""
    hardware_query = session.query(Device.hardware_version,
                                   func.count(Device.id)) \
                            .group_by(Device.hardware_version) \
                            .order_by(func.count(Device.id).desc())
    print("\n--- Hardware version ---")
    for [hardware_version, count] in hardware_query.all():
        print("{}: {}".format(hardware_version, count))
