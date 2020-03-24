"""
This is a helper module to deal with datetime and timezones.

For convenience datetime related modules (e.g. dateutil.parser, pytz, etc) are
imported here so they can be accessed using this module.

Usage:
>>> from fastapi_sqlalchemy import tz
>>> dt1 = tz.utcnow()
>>> dt2 = tz.utcdatetime(2015, 1, 2, 1, 2, 3)
>>> dt2 = dt2.astimezone(tz.LOCAL)
>>> dt2 = dt2.astimezone(tz.UTC)
>>> dt2 += tz.timedelta(minutes=12)
>>> dt3 = tz.parse("2017-01-02 02:22")
>>> date1 = tz.date(2015, 1, 2)
"""
import typing

# pylint: disable=unused-import
from datetime import date, datetime, timedelta  # noqa
# pylint: enable=unused-import


import dateutil.parser
import pytz
import tzlocal

LOCAL = tzlocal.get_localzone()
UTC = pytz.utc


def as_datetime(value: typing.Union[str, date, datetime]) -> datetime:
    """Convert a string value to a datetime object."""
    if not isinstance(value, datetime):
        value = parse(value)

    if not value.tzinfo:
        value = LOCAL.localize(value)

    return as_utc(value)


def parse(*args, **kwargs):
    """Shortcut for dateutil.parser.parse with timezone"""
    value = dateutil.parser.parse(*args, **kwargs)
    return as_datetime(value)


def utcnow() -> datetime:
    """return UTC datetime with UTC timezone"""
    return datetime.utcnow().replace(tzinfo=UTC)


def utcdatetime(*args, **kwargs) -> datetime:
    """Same as datetime.datetime() but create UTC aware datetime"""
    return datetime(*args, **kwargs, tzinfo=UTC)


def as_utc(value: typing.Union[datetime, date]):
    """Convert given date or datetime to UTC"""
    return value.astimezone(UTC)
