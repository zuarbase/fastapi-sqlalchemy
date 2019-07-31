""" Model mixins """
import uuid
import enum

import sqlalchemy
from sqlalchemy.ext.declarative import declared_attr

from fastapi_sqlalchemy import tz
from .types import GUID
from .base import Session


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


class ConfirmationMixin:
    """ Mixin to support confirmation for Users """

    email = sqlalchemy.Column(
        sqlalchemy.String(255),
        nullable=False,
        unique=True
    )

    @classmethod
    def get_by_email(
            cls,
            session: Session,
            email: str,
    ):
        """ Lookup a User by name
        """
        return session.query(cls).filter(cls.email == email).first()

    @declared_attr
    def confirmed_at(self):
        """ Email confirmation timestamp """
        column = sqlalchemy.Column(
            sqlalchemy.DateTime(timezone=True),
            nullable=True,
        )
        # pylint: disable=protected-access
        column._creation_order = 9700
        return column

    @property
    def confirmed(self):
        """ Whether or not the email has been confirmed """
        return self.confirmed_at is not None
