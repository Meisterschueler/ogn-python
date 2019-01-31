from .database import manager as database_manager
from .bulkimport import manager as bulkimport_manager
from .export import manager as export_manager
from .logbook import manager as logbook_manager
from .stats import manager as stats_manager
from .flights import manager as flights_manager

from manager import Manager

manager = Manager()

manager.merge(database_manager, namespace='db')
manager.merge(bulkimport_manager, namespace='bulkimport')
manager.merge(export_manager, namespace='export')
manager.merge(logbook_manager, namespace='logbook')
manager.merge(stats_manager, namespace='stats')
manager.merge(flights_manager, namespace='flights')
