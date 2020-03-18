"""header_prefix
This is a helper module to deal with datetime objects across mitto package
corrent way of importing:
>>> from mews import tz

After importing tz, you don't need to import datetime or dateutil.parser
everything is included here.

Uage:
>>> dt1 = tz.utcnow()
>>> dt2 = tz.utcdatetime(2015, 1, 2, 1, 2, 3)
>>> dt2 = dt2.astimezone(tz.LOCAL)
>>> dt2 = dt2.astimezone(tz.UTC)
>>> dt2 += tz.timedelta(minutes=12)
>>> dt3 = tz.parse("2017-01-02 02:22")
>>> date1 = tz.date(2015, 1, 2)
"""
# pylint: disable=unused-import
from datetime import datetime, timedelta, date  # noqa


import dateutil.parser
import pytz
import tzlocal

LOCAL = tzlocal.get_localzone()
UTC = pytz.utc


def as_datetime(value):
    """
    Convert a string value to a datetime object
    """
    if not isinstance(value, datetime):
        value = parse(value)

    if not value.tzinfo:
        value = LOCAL.localize(value)

    return value.astimezone(UTC)


def parse(*args, **kwargs):
    """Shortcut for dateutil.parser.parse with timezone"""
    value = dateutil.parser.parse(*args, **kwargs)
    return as_datetime(value)


def utcnow():
    """return UTC datetime with UTC timezone"""
    return datetime.utcnow().replace(tzinfo=UTC)
