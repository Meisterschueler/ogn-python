from .database import manager as database_manager
from .bulkimport import manager as bulkimport_manager
from .igcexport import manager as igcexport_manager
from .showairport import manager as show_airport_manager
from .showreceiver import manager as show_receiver_manager
from .showdevices import manager as show_devices_manager
from .showdeviceinfos import manager as show_deviceinfos_manager
from .logbook import manager as logbook_manager
from ogn.commands.stats import manager as stats_manager 

from manager import Manager

manager = Manager()

manager.merge(database_manager, namespace='db')
manager.merge(bulkimport_manager, namespace='bulkimport')
manager.merge(igcexport_manager, namespace='igcexport')
manager.merge(show_airport_manager, namespace='show.airport')
manager.merge(show_receiver_manager, namespace='show.receiver')
manager.merge(show_devices_manager, namespace='show.devices')
manager.merge(show_deviceinfos_manager, namespace='show.deviceinfos')
manager.merge(logbook_manager, namespace='logbook')
manager.merge(stats_manager, namespace='stats')
