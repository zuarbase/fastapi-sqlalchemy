""" Association table(s) """
import uuid

import sqlalchemy

from fastapi_sqlalchemy import tz

from .base import BASE
from .types import GUID


def create_group_membership_table(
        table_name: str = "group_membership",
        user_table_name: str = "users",
        group_table_name: str = "groups",
) -> sqlalchemy.Table:
    """ Generate a user <-> group association table """
    table = sqlalchemy.Table(
        table_name,
        BASE.metadata,
        sqlalchemy.Column(
            "id",
            GUID,
            primary_key=True,
            default=uuid.uuid4,
        ),
        sqlalchemy.Column(
            "group_id",
            GUID,
            sqlalchemy.ForeignKey(group_table_name + ".id")
        ),
        sqlalchemy.Column(
            "user_id",
            GUID,
            sqlalchemy.ForeignKey(user_table_name + ".id")
        ),
        sqlalchemy.Column(
            "updated_at",
            sqlalchemy.DateTime(timezone=True),
            default=tz.utcnow,
            onupdate=tz.utcnow,
            nullable=False,
        ),
        sqlalchemy.Column(
            "created_at",
            sqlalchemy.DateTime(timezone=True),
            default=tz.utcnow,
            onupdate=tz.utcnow,
            nullable=False,
        )
    )
    table.__association__ = "group_membership"
    return table


def create_user_permissions_table(
        table_name: str = "user_permissions",
        user_table_name: str = "users",
        permission_table_name: str = "permissions",
) -> sqlalchemy.Table:
    """ Generate a user <-> permission association table """
    table = sqlalchemy.Table(
        table_name,
        BASE.metadata,
        sqlalchemy.Column(
            "id",
            GUID,
            primary_key=True,
            default=uuid.uuid4,
        ),
        sqlalchemy.Column(
            "user_id",
            GUID,
            sqlalchemy.ForeignKey(user_table_name + ".id")
        ),
        sqlalchemy.Column(
            "permission_id",
            GUID,
            sqlalchemy.ForeignKey(permission_table_name + ".id")
        ),
        sqlalchemy.Column(
            "updated_at",
            sqlalchemy.DateTime(timezone=True),
            default=tz.utcnow,
            onupdate=tz.utcnow,
            nullable=False,
        ),
        sqlalchemy.Column(
            "created_at",
            sqlalchemy.DateTime(timezone=True),
            default=tz.utcnow,
            onupdate=tz.utcnow,
            nullable=False,
        )
    )
    table.__association__ = "user_permissions"
    return table


def create_group_permissions_table(
        table_name: str = "group_permissions",
        group_table_name: str = "groups",
        permission_table_name: str = "permissions",
) -> sqlalchemy.Table:
    """ Generate a group <-> permission association table """
    table = sqlalchemy.Table(
        table_name,
        BASE.metadata,
        sqlalchemy.Column(
            "id",
            GUID,
            primary_key=True,
            default=uuid.uuid4,
        ),
        sqlalchemy.Column(
            "group_id",
            GUID,
            sqlalchemy.ForeignKey(group_table_name + ".id")
        ),
        sqlalchemy.Column(
            "permission_id",
            GUID,
            sqlalchemy.ForeignKey(permission_table_name + ".id")
        ),
        sqlalchemy.Column(
            "updated_at",
            sqlalchemy.DateTime(timezone=True),
            default=tz.utcnow,
            onupdate=tz.utcnow,
            nullable=False,
        ),
        sqlalchemy.Column(
            "created_at",
            sqlalchemy.DateTime(timezone=True),
            default=tz.utcnow,
            onupdate=tz.utcnow,
            nullable=False,
        )
    )
    table.__association__ = "group_permissions"
    return table
