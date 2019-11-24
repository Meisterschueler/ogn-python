from .beacon import Beacon


class ReceiverBeacon(Beacon):
    __tablename__ = "receiver_beacons"

    # disable irrelevant aprs fields
    relay = None
    track = None
    ground_speed = None

    def __repr__(self):
        return "<ReceiverBeacon %s: %s,%s,%s,%s,%s>" % (
            self.name,
            self.location,
            self.altitude,
            self.dstcall,
            self.receiver_name,
            self.timestamp,
        )

    @classmethod
    def get_columns(self):
        return [
            "location",
            "altitude",
            "name",
            "dstcall",
            "receiver_name",
            "timestamp",
            # 'raw_message',
            # 'reference_timestamp',
        ]

    def get_values(self):
        return [
            self.location_wkt,
            int(self.altitude) if self.altitude else None,
            self.name,
            self.dstcall,
            self.receiver_name,
            self.timestamp,
            # self.raw_message,
            # self.reference_timestamp,
        ]
