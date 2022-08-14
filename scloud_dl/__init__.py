
from dataclasses import dataclass
import logging
from logging import Logger

@dataclass
class Track:
    title: str
    url: str

def initLogging():

    logger: Logger = logging.getLogger() #root logger
    logger.setLevel(logging.INFO)
    
    formatter = logging.Formatter(
        '%(asctime)s: %(processName)s %(threadName)s: %(name)s: %(levelname)s - %(message)s')
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler("logs/sc_dl.log")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    logger.debug('logging initialized')

