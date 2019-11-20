import coloredlogs, logging

_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# logging.basicConfig(format=_FORMAT)

def getLogger(name):
    '''Custom logger.'''

    logger = logging.getLogger(name)
    # logger.setLevel(logging.DEBUG)
    coloredlogs.install(level='DEBUG', logger=logger, fmt=_FORMAT)

    return logger
