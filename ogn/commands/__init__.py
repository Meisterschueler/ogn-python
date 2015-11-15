from .database import manager as database_manager
from .showreceiver import manager as show_receiver_manager
from .logbook import manager as logbook_manager

from manager import Manager

manager = Manager()

manager.merge(database_manager, namespace='db')
manager.merge(show_receiver_manager, namespace='show.receiver')
manager.merge(logbook_manager, namespace='logbook')
