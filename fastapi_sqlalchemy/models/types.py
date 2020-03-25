""" SQLAlchemy types - particularly for columns """
import uuid
import json

from sqlalchemy.ext.mutable import MutableDict

from sqlalchemy.sql import operators
from sqlalchemy.types import String, TypeDecorator, CHAR, TEXT
from sqlalchemy.dialects.postgresql import UUID


class GUID(TypeDecorator):
    """Platform-independent GUID type.

    Uses PostgreSQL's UUID type, otherwise uses
    CHAR(32), storing as stringified hex values.

    https://docs.sqlalchemy.org/en/latest/core/custom_types.html
    Backend-agnostic GUID Type
    """
    impl = CHAR

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(UUID())
        return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return str(value)
        if not isinstance(value, uuid.UUID):
            return "%.32x" % uuid.UUID(value).int
        # hexstring
        return "%.32x" % value.int

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if not isinstance(value, uuid.UUID):
            value = uuid.UUID(value)
        return value

    def process_literal_param(self, value, dialect):
        raise NotImplementedError()

    @property
    def python_type(self):
        raise NotImplementedError()


class JSONEncodedDict(TypeDecorator):
    """Represents an immutable structure as a json-encoded string.
    """

    impl = TEXT

    _OPERATORS_FOR_STR = (
        operators.like_op,
        operators.notlike_op,
    )

    def coerce_compared_value(self, op, value):
        if op in self._OPERATORS_FOR_STR:
            return String()
        return self

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)

        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value

    def process_literal_param(self, value, dialect):
        raise NotImplementedError()

    @property
    def python_type(self):
        raise NotImplementedError()


JSON_TYPE = MutableDict.as_mutable(JSONEncodedDict)
