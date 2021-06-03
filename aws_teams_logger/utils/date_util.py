"""
Utilities for interacting with dates and times.
"""
from datetime import datetime, timezone

import pytz

from ..constants import LOCAL_TZ


# UTC timezone (no offset)
UTC = timezone.utc

# Local timezone object
#
# Adding this globally, in case `LOCAL_TZ` is set as an invalid time zone.
local = pytz.timezone(LOCAL_TZ)


def local_now() -> datetime:
    """
    Returns local time now (by default in Eastern Time)
    """
    return datetime.now(local)


def utc_now() -> datetime:
    """
    Return time in UTC
    """
    return datetime.utcnow().replace(tzinfo=UTC)
