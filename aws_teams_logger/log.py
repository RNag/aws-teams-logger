import functools
import logging
import logging.config
import os
from logging import getLogger, Logger, LoggerAdapter

from .constants import LOG_CFG


# Contains the original logger methods, by default for the `logging` module
#
# Note: don't directly modify this object
_ORIGINAL_LOG_METHODS = {}


def setup_logging():
    """
    Allow for easy insight into SDK behavior.
    """
    if LOG_CFG is not None:
        if os.path.exists(LOG_CFG):
            import json
            with open(LOG_CFG, 'rt') as config_file:
                config = json.load(config_file)
            logging.config.dictConfig(config)
        else:
            level_name = logging._nameToLevel.get(LOG_CFG.upper())
            if level_name:
                logging.basicConfig(level=level_name)
    # we will do most of the logging here, so turn down the requests and botocore libraries
    for lib in 'requests', 'urllib3', 'botocore':
        logging.getLogger(lib).setLevel(logging.WARNING)


def original_logger(name: str):
    """
    Wraps a call to ``logging.getLogger`` to return the original (un-decorated)
    :class:`Logger` object, which should not log any messages to MS Teams or
    Outlook.

    :param name: Name of the logger to retrieve
    :return: the :class:`Logger` object with the un-decorated log methods
    :rtype: OriginalLogAdapter
    """
    logger = getLogger(name)
    return OriginalLogAdapter(logger)


def original_log_method(logger_cls=Logger, log_func_name='_log'):
    """
    Get the original (e.g. un-decorated) log method
    """
    key = f'{logger_cls.__name__}.{log_func_name}'

    if key not in _ORIGINAL_LOG_METHODS:
        # Cache the original log method
        log_method = getattr(logger_cls, log_func_name)
        _ORIGINAL_LOG_METHODS[key] = log_method

    return _ORIGINAL_LOG_METHODS[key]


class OriginalLogAdapter(LoggerAdapter):

    def __init__(self, logger, extra=None):
        super().__init__(logger, extra or {})

    def log(self, level, msg, *args, **kwargs):
        if self.isEnabledFor(level):
            self._orig_log(level, msg, args, **kwargs)

    @property
    def _orig_log(self):
        """
        Returns the original :meth:`Logger._log` method for this :attr:`logger`.

        The method resolution is needed at run-time (i.e. when a message is
        logged) in case the :meth:`Logger._log` method is decorated after the
        :class:`OriginalLogAdapter` object is instantiated.

        :rtype: typing.Callable
        """
        return functools.partial(original_log_method(), self.logger)


# Setup logger for the library
LOG = original_logger('aws_teams_logger')
