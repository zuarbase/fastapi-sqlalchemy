""" SQLAlchemy helper function """
import uuid
import enum
from collections import Mapping

import sqlalchemy

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
)

from fastapi_sqlalchemy import tz


class Base:
    """ Custom declarative base """

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


BASE = declarative_base(cls=Base)
Session = scoped_session(sessionmaker())


class ModelMapping(dict):
    """ Class to hold model information """

    def __setitem__(self, key, value):
        if key in self:
            raise RuntimeError(
                f"Duplicate '{key}' model found."
                "There may only be one, non-abstract sub-class."
            )
        super().__setitem__(key, value)

    def update(self, other=None, **kwargs):
        if other is not None:
            for key, value in other.items() \
                    if isinstance(other, Mapping) else other:
                self[key] = value
        for key, value in kwargs.items():
            self[key] = value


MODEL_MAPPING = ModelMapping()
