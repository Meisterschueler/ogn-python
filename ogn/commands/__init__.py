from .database import manager as database_manager
from .showairport import manager as show_airport_manager
from .showreceiver import manager as show_receiver_manager
from .showdevices import manager as show_devices_manager
from .logbook import manager as logbook_manager

from manager import Manager

manager = Manager()

manager.merge(database_manager, namespace='db')
manager.merge(show_airport_manager, namespace='show.airport')
manager.merge(show_receiver_manager, namespace='show.receiver')
manager.merge(show_devices_manager, namespace='show.devices')
manager.merge(logbook_manager, namespace='logbook')
