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
