import logging

logger = logging.getLogger('main')
logger.setLevel(logging.DEBUG)

filehandler = logging.FileHandler('main.log')
filehandler.setLevel(logging.DEBUG)

consolehandler = logging.StreamHandler()
consolehandler.setLevel(logging.INFO)

formatter = logging.Formatter("%(asctime)s - %(levelname).4s - %(name)s - %(message)s")
filehandler.setFormatter(formatter)
consolehandler.setFormatter(formatter)

logger.addHandler(filehandler)
logger.addHandler(consolehandler)
