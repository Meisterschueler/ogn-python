import re

from sqlalchemy import Column, Integer, String, Unicode, Boolean, SmallInteger

from .address_origin import AddressOrigin
from .base import Base


FLARMNET_LINE_LENGTH = 173


class Flarm(Base):
    __tablename__ = 'flarm'

    id = Column(Integer, primary_key=True)
    address_type = None
    address = Column(String(6), index=True)
    name = Column(Unicode)
    airport = Column(String)
    aircraft = Column(String)
    registration = Column(String(7), index=True)
    competition = Column(String(3))
    frequency = Column(String)
    tracked = Column(Boolean)
    identified = Column(Boolean)

    address_origin = Column(SmallInteger)

    def parse_ogn(self, line):
        PATTERN = "\'([FIO])\',\'(.{6})\',\'([^\']+)?\',\'([^\']+)?\',\'([^\']+)?\',\'([YN])\',\'([YN])\'"
        ogn_re = re.compile(PATTERN)

        result = ogn_re.match(line)
        if result is None:
            raise Exception("No valid string: %s" % line)

        self.address_type = result.group(1)
        self.address = result.group(2)
        self.aircraft = result.group(3)
        self.registration = result.group(4)
        self.competition = result.group(5)
        self.tracked = result.group(6) == "Y"
        self.identified = result.group(7) == "Y"

        self.address_origin = AddressOrigin.ogn_ddb

    def parse_flarmnet(self, line):
        rawString = self.hexToString(line)

        self.address_type = None
        self.address = rawString[0:6].strip()
        self.name = rawString[6:27].strip()
        self.airport = rawString[27:48].strip()
        self.aircraft = rawString[48:69].strip()
        self.registration = rawString[69:76].strip()
        self.competition = rawString[76:79].strip()
        self.frequency = rawString[79:89].strip()

        self.address_origin = AddressOrigin.flarmnet

    def hexToString(self, hexString):
        result = ''
        for i in range(0, len(hexString)-1, 2):
            result += chr(int(hexString[i:i+2], 16))

        return(result)

    def __repr__(self):
        return("<Flarm: %s,%s,%s,%s,%s,%s,%s,%s,%s,%s>" % (self.address_type, self.address, self.name, self.airport, self.aircraft, self.registration, self.competition, self.frequency, self.tracked, self.identified))


if __name__ == '__main__':
    import urllib.request
    response = urllib.request.urlopen("http://ddb.glidernet.org/download")
    lines = response.readlines()
    for line in lines:
        if (line.decode()[0] == "#"):
            continue

        flarm = Flarm()
        flarm.parse_ogn(line.decode())
        print(str(flarm))

    response = urllib.request.urlopen("http://flarmnet.org/files/data.fln")
    lines = response.readlines()
    for line in lines:
        if (len(line) != FLARMNET_LINE_LENGTH):
            continue

        flarm = Flarm()
        flarm.parse_flarmnet(line.decode())
        print(str(flarm))
