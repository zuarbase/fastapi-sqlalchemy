from fastapi_sqlalchemy.models.base import MODEL_MAPPING

from fastapi_sqlalchemy import models

from .models import User, Group, Permission

models.create_group_membership_table()
models.create_user_permissions_table()
models.create_group_permissions_table()


def _create_all(engine, session):

    alice = User(username="alice")
    assert MODEL_MAPPING["User"] == User
    session.add(alice)

    users_group = Group(name="users")
    assert MODEL_MAPPING["Group"] == Group
    session.add(users_group)

    admins_group = Group(name="admins")
    session.add(admins_group)

    read_permission = Permission(name="READ")
    assert MODEL_MAPPING["Permission"] == Permission
    session.add(read_permission)

    write_permission = Permission(name="WRITE")
    session.add(write_permission)

    session.commit()


def test_groups(engine, session):
    _create_all(engine, session)

    alice = User.get_by_username(session, "alice")
    alice.groups.append(Group.get_by_name(session, "users"))
    alice.groups.append(Group.get_by_name(session, "admins"))
    session.commit()

    alice = User.get_by_username(session, "alice")
    assert ["admins", "users"] == sorted(
        group.name for group in alice.groups
    )


def test_user_case(engine, session):
    _create_all(engine, session)

    user = User(username="Bob")
    session.add(user)
    session.commit()

    assert User.get_by_username(session, "BOB")


def test_user_permissions(engine, session):
    _create_all(engine, session)

    alice = User.get_by_username(session, "alice")
    alice.user_permissions.append(Permission.get_by_name(session, "READ"))
    alice.user_permissions.append(Permission.get_by_name(session, "WRITE"))
    session.commit()

    alice = User.get_by_username(session, "alice")
    assert ["READ", "WRITE"] == sorted(
        permission.name for permission in alice.user_permissions
    )


def test_group_permissions(engine, session):
    _create_all(engine, session)

    admins = Group.get_by_name(session, "admins")
    admins.permissions.append(Permission.get_by_name(session, "READ"))
    admins.permissions.append(Permission.get_by_name(session, "WRITE"))
    session.commit()

    admins = Group.get_by_name(session, "admins")
    assert ["READ", "WRITE"] == sorted(
        permission.name for permission in admins.permissions
    )


def test_permissions(engine, session):
    _create_all(engine, session)

    alice = User.get_by_username(session, "alice")

    admins = Group.get_by_name(session, "admins")
    admins.users.append(alice)

    write_permission = Permission.get_by_name(session, "WRITE")
    write_permission.groups.append(admins)

    alice.user_permissions.append(Permission.get_by_name(session, "READ"))
    session.commit()

    alice = User.get_by_username(session, "alice")
    assert ["READ", "WRITE"] == sorted(
        permission.name for permission in alice.permissions
    )


def test_permission_duplicate(engine, session):
    _create_all(engine, session)

    alice = User.get_by_username(session, "alice")

    admins = Group.get_by_name(session, "admins")
    admins.users.append(alice)

    read_permission = Permission.get_by_name(session, "READ")

    admins.permissions.append(Permission.get_by_name(session, "WRITE"))
    admins.permissions.append(read_permission)

    alice.user_permissions.append(read_permission)
    session.commit()

    alice = User.get_by_username(session, "alice")
    assert ["READ", "WRITE"] == sorted(
        permission.name for permission in alice.permissions
    )
