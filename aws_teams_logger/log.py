from logging import getLogger, Formatter, StreamHandler, Logger
from typing import Union

from .constants import LOG_LEVEL


loggers = {}


def setup_logger(name: str, level: Union[str, int],
                 fmt='%(name)s - %(levelname)s - %(message)s') -> Logger:
    """
    Create and return a logger object with a custom formatter.

    :param name: Name of the logger
    :param level: Minimum log level enabled (ex: 'INFO')
    :param fmt: Format to print log messages in

    """
    if name in loggers:
        return loggers[name]

    # create logger
    logger = getLogger(name)
    logger.setLevel(level)
    logger.propagate = False

    # create a console handler
    ch = StreamHandler()
    ch.setLevel(level)

    # create formatter
    formatter = Formatter(fmt)

    # add formatter to ch
    ch.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(ch)
    loggers[name] = logger

    return logger


# setup custom logger
LOG = setup_logger('aws_teams_logger', level=LOG_LEVEL)
