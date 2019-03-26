""" Model mixins """
import uuid
import enum

import sqlalchemy
from sqlalchemy.ext.declarative import declared_attr

from fastapi_sqlalchemy import tz
from .types import GUID


class GuidMixin:
    """ Mixin that add a UUID id column """
    id = sqlalchemy.Column(
        GUID,
        primary_key=True,
        default=uuid.uuid4,
    )


class TimestampMixin:
    """ Mixin to add update_at and created_at columns

    The columns are added at the *end* of the table
    """
    @declared_attr
    def updated_at(self):
        """ Last update timestamp """
        column = sqlalchemy.Column(
            sqlalchemy.DateTime(timezone=True),
            default=tz.utcnow,
            onupdate=tz.utcnow,
            nullable=False,
        )
        # pylint: disable=protected-access
        column._creation_order = 9800
        return column

    @declared_attr
    def created_at(self):
        """ Creation timestamp """
        column = sqlalchemy.Column(
            sqlalchemy.DateTime(timezone=True),
            default=tz.utcnow,
            onupdate=tz.utcnow,
            nullable=False,
        )
        # pylint: disable=protected-access
        column._creation_order = 9900
        return column


class DictMixin:
    """ Mixin to add as_dict() """
    def as_dict(self):
        """ Convert object to dictionary """
        result = {}
        for attr in sqlalchemy.inspect(self).mapper.column_attrs:
            value = getattr(self, attr.key)
            if isinstance(value, (tz.datetime, tz.date)):
                value = value.isoformat()
            elif isinstance(value, uuid.UUID):
                value = str(value)
            elif isinstance(value, enum.Enum):
                value = value.name
            result[attr.key] = value
        return result
