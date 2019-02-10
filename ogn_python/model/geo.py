class Location:
    """Represents a location in WGS84"""

    def __init__(self, lon=0, lat=0):
        self.longitude = lon
        self.latitude = lat

    def to_wkt(self):
        return 'SRID=4326;POINT({0} {1})'.format(self.longitude, self.latitude)

    def __str__(self):
        return '{0: 7.4f}, {1:8.4f}'.format(self.latitude, self.longitude)

    def as_dict(self):
        return {'latitude': round(self.latitude, 8), 'longitude': round(self.longitude, 8)}
