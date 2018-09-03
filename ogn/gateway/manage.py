import logging

from manager import Manager
from ogn.client import AprsClient
from ogn.gateway.process import  string_to_message
from datetime import datetime
from ogn.gateway.process_tools import DummyMerger, Converter, DummySaver


manager = Manager()

logging_formatstr = '%(asctime)s - %(levelname).4s - %(name)s - %(message)s'
log_levels = ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG']

# Build the processing pipeline
saver = DummySaver()
converter = Converter(callback=saver)
merger = DummyMerger(callback=converter)

def asdf(raw_string):
    message = string_to_message(raw_string, reference_date=datetime.utcnow())
    if message is not None:
        merger.add_message(message)
    else:
        print(message)


@manager.command
def run(aprs_user='anon-dev', logfile='main.log', loglevel='INFO'):
    """Run the aprs client."""

    # User input validation
    if len(aprs_user) < 3 or len(aprs_user) > 9:
        print('aprs_user must be a string of 3-9 characters.')
        return
    if loglevel not in log_levels:
        print('loglevel must be an element of {}.'.format(log_levels))
        return

    # Enable logging
    log_handlers = [logging.StreamHandler()]
    if logfile:
        log_handlers.append(logging.FileHandler(logfile))
    logging.basicConfig(format=logging_formatstr, level=loglevel, handlers=log_handlers)

    print('Start ogn gateway')
    client = AprsClient(aprs_user)
    client.connect()

    try:
        client.run(callback=asdf, autoreconnect=True)
    except KeyboardInterrupt:
        print('\nStop ogn gateway')

    merger.flush()
    client.disconnect()
    logging.shutdown()
