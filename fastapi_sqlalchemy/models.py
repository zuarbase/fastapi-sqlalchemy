""" SQLAlchemy helper function """
import uuid
import enum

import sqlalchemy
from sqlalchemy.inspection import inspect
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
)
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID

from . import tz


class Base:
    """ Custom declarative base """

    def as_dict(self):
        """ Make the protected method public """
        # pylint: disable=no-member
        result = {}
        for key, obj in inspect(self).attrs.items():
            result[key] = obj.value
        return result


BASE = declarative_base(cls=Base)
Session = scoped_session(sessionmaker())


class GUID(TypeDecorator):
    """Platform-independent GUID type.

    Uses PostgreSQL's UUID type, otherwise uses
    CHAR(32), storing as stringified hex values.

    https://docs.sqlalchemy.org/en/latest/core/custom_types.html
    Backend-agnostic GUID Type
    """
    impl = CHAR

    def load_dialect_impl(self, dialect):
        """ see sqlalchemy.types.TypeDecorator.load_dialect_impl """
        if dialect.name == "postgresql":
            return dialect.type_descriptor(UUID())
        else:
            return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        """ see sqlalchemy.types.TypeDecorator.process_bind_param """
        if value is None:
            return value
        elif dialect.name == "postgresql":
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return "%.32x" % uuid.UUID(value).int
            else:
                # hexstring
                return "%.32x" % value.int

    def process_result_value(self, value, dialect):
        """ see sqlalchemy.types.TypeDecorator.process_result_value """
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                value = uuid.UUID(value)
            return value

    def process_literal_param(self, value, dialect):
        """ see sqlalchemy.types.TypeDecorator.process_literal_param """
        raise NotImplementedError()

    def python_type(self):
        """ see sqlalchemy.types.TypeDecorator.process_literal_param """
        raise NotImplementedError()


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
