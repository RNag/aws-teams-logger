__all__ = ['as_list',
           'get_formatted_message']

import collections.abc
from typing import Union, List


def as_list(o: Union[str, List[str]], sep=','):
    """
    Return `o` if already a list. If `o` is None or an empty string,
    return an empty list. Otherwise, split the string on `sep` and
    return the list result.

    """
    if not o:
        return []

    if isinstance(o, list):
        return o

    return o.split(sep)


def get_formatted_message(msg, args):
    """
    Gets a message after formatting is applied. Ideally, this would be the arguments
    passed to a logger method, such as `LOG.warning`.

    """
    if (args and len(args) == 1 and isinstance(args[0], collections.abc.Mapping)
            and args[0]):
        args = args[0]
    msg = str(msg)
    if args:
        msg = msg % args
    return msg
