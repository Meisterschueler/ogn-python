#!/usr/bin/env python

from manager import Manager
from ogn.commands import manager as command_manager
from ogn.gateway.manage import manager as gateway_manager

manager = Manager()
manager.merge(command_manager)
manager.merge(gateway_manager, namespace='gateway')


if __name__ == '__main__':
    manager.main()
