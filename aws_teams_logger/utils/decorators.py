"""
Project-specific decorators
"""
import functools
from datetime import timedelta

from .time_util import preferred_clock
from ..log import LOG


def record_time(f=None, log_message: str = None, log_func=print):
    """
    Decorates a function to also log its execution time when it completes.

    `log_message` is a message that can be specified to replace the default
    one, that logs in the format "Successfully ran task {func_name}"

    `log_func` is the function to send the message to, by default it passes
    the message to the 'print' function.

    """
    def decorator(func):

        @functools.wraps(func)
        def new_func(*args, **kwargs):
            start = preferred_clock()

            result = func(*args, **kwargs)

            diff_sec = preferred_clock() - start
            elapsed = timedelta(seconds=diff_sec)

            message = log_message or f'Successfully ran task `{func.__name__.lstrip("_")}`'

            log_func(f'[{elapsed}] {message}')

            return result

        return new_func

    if f:
        return decorator(f)

    return decorator


# Decorator to log the execution time using a `logger` object instead
log_time = functools.partial(record_time, log_func=LOG.info)
