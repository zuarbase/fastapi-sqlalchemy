""" Bookkeeping """
from sqlalchemy import event, inspect
from sqlalchemy.orm import mapper, relationship

from .base import BASE, MODEL_MAPPING


@event.listens_for(mapper, "after_configured")
def _after_configured():
    # pylint: disable=too-many-branches
    user_cls = MODEL_MAPPING.get("User")
    group_cls = MODEL_MAPPING.get("Group")
    permission_cls = MODEL_MAPPING.get("Permission")

    associations = {}
    for table in BASE.metadata.tables.values():
        association = getattr(table, "__association__", None)
        if association is None:
            continue
        if association in associations:
            raise RuntimeError(
                f"Multiple '{association}' associations found."
                "Only a single table may have a specific __association__ value"
            )
        associations[association] = table

    group_membership_table = associations.get("group_membership")
    if group_membership_table is not None:
        if not user_cls:
            raise RuntimeError(
                "'group_membership' association table found, "
                "but no User table defined."
            )
        if not group_cls:
            raise RuntimeError(
                "'group_membership' association table found, "
                "but no Group table defined."
            )

        if not hasattr(user_cls, "groups"):
            user_cls.groups = relationship(
                group_cls,
                secondary=group_membership_table
            )
        if not hasattr(group_cls, "users"):
            group_cls.users = relationship(
                user_cls,
                secondary=group_membership_table
            )

    user_permissions_table = associations.get("user_permissions")
    if user_permissions_table is not None:
        if not user_cls:
            raise RuntimeError(
                "'user_permissions' association table found, "
                "but no User table defined."
            )
        if not permission_cls:
            raise RuntimeError(
                "'user_permissions' association table found, "
                "but no Permission table defined."
            )

        if not hasattr(user_cls, "user_permissions"):
            user_cls.user_permissions = relationship(
                permission_cls,
                secondary=user_permissions_table
            )
        if not hasattr(permission_cls, "users"):
            permission_cls.users = relationship(
                user_cls,
                secondary=user_permissions_table
            )

    group_permissions_table = associations.get("group_permissions")
    if group_permissions_table is not None:
        if not group_cls:
            raise RuntimeError(
                "'group_permissions' association table found, "
                "but no Group table defined."
            )
        if not permission_cls:
            raise RuntimeError(
                "'group_permissions' association table found, "
                "but no Permission table defined."
            )

        if not hasattr(group_cls, "permissions"):
            group_cls.permissions = relationship(
                permission_cls,
                secondary=group_permissions_table
            )
        if not hasattr(permission_cls, "groups"):
            permission_cls.groups = relationship(
                group_cls,
                secondary=group_permissions_table
            )

    def _permissions(user):
        session = inspect(user).session
        return session.query(permission_cls) \
            .join(user_permissions_table, user_cls) \
            .filter(user_cls.id == user.id) \
            .union(
                session.query(permission_cls)
                .join(group_permissions_table)
                .join(group_cls)
                .join(group_membership_table)
                .join(user_cls)
                .filter(user_cls.id == user.id))

    if user_cls and not hasattr(user_cls, "permissions") and \
            user_permissions_table is not None and \
            group_permissions_table is not None and \
            group_membership_table is not None:
        user_cls.permissions = property(_permissions)
