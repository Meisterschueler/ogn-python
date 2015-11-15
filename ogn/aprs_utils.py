from datetime import datetime, timedelta
import math


kmh2kts = 0.539957
feet2m = 0.3048
ms2fpm = 196.85

kts2kmh = 1 / kmh2kts
m2feet = 1 / feet2m
fpm2ms = 1 / ms2fpm


def dmsToDeg(dms):
    absDms = abs(dms)
    d = math.floor(absDms)
    m = (absDms - d) * 100 / 60
    return d + m


def createTimestamp(hhmmss, reference):
    hh = int(hhmmss[0:2])
    mm = int(hhmmss[2:4])
    ss = int(hhmmss[4:6])

    if reference is None:
        reference = datetime.utcnow()
        return datetime(reference.year, reference.month, reference.day, hh, mm, ss)

    if (reference.hour == 23) & (hh == 0):
        reference = reference + timedelta(days=1)
    elif (reference.hour == 0) & (hh == 23):
        reference = reference - timedelta(days=1)
    elif abs(reference.hour - hh) > 1:
        raise Exception("Time difference is too big. Reference time:%s - timestamp:%s" % (reference, hhmmss))
    return datetime(reference.year, reference.month, reference.day, hh, mm, ss)
