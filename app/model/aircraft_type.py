import enum


class AircraftType(enum.Enum):
    UNKNOWN = 0
    GLIDER_OR_MOTOR_GLIDER = 1
    TOW_TUG_PLANE = 2
    HELICOPTER_ROTORCRAFT = 3
    PARACHUTE = 4
    DROP_PLANE = 5
    HANG_GLIDER = 6
    PARA_GLIDER = 7
    POWERED_AIRCRAFT = 8
    JET_AIRCRAFT = 9
    FLYING_SAUCER = 10
    BALLOON = 11
    AIRSHIP = 12
    UNMANNED_AERIAL_VEHICLE = 13
    STATIC_OBJECT = 15

    @staticmethod
    def list():
        return list(map(lambda c: c.value, AircraftType))
