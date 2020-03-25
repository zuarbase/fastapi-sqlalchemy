import uuid
from datetime import datetime, date
from enum import Enum

import pytest
import sqlalchemy.orm
import sqlalchemy.ext.declarative

from fastapi_sqlalchemy import models
from fastapi_sqlalchemy.models import base
from fastapi_sqlalchemy.models.base import MODEL_MAPPING

from tests.data.models import User, Group, Permission

models.create_group_membership_table()
models.create_user_permissions_table()
models.create_group_permissions_table()


def _create_all(session):

    alice = User(username="alice")
    assert MODEL_MAPPING["User"] is User
    session.add(alice)

    users_group = Group(name="users")
    assert MODEL_MAPPING["Group"] is Group
    session.add(users_group)

    admins_group = Group(name="admins")
    session.add(admins_group)

    read_permission = Permission(name="READ")
    assert MODEL_MAPPING["Permission"] is Permission
    session.add(read_permission)

    write_permission = Permission(name="WRITE")
    session.add(write_permission)

    session.commit()


def test_groups(engine, session):
    _create_all(session)

    alice = User.get_by_username(session, "alice")
    alice.groups.append(Group.get_by_name(session, "users"))
    alice.groups.append(Group.get_by_name(session, "admins"))
    session.commit()

    alice = User.get_by_username(session, "alice")
    assert ["admins", "users"] == sorted(
        group.name for group in alice.groups
    )


def test_user_case(engine, session):
    _create_all(session)

    user = User(username="Bob")
    session.add(user)
    session.commit()

    assert User.get_by_username(session, "BOB") is user
    assert user.identity == str(user.id)


def test_user_permissions(engine, session):
    _create_all(session)

    alice = User.get_by_username(session, "alice")
    alice.user_permissions.append(Permission.get_by_name(session, "READ"))
    alice.user_permissions.append(Permission.get_by_name(session, "WRITE"))
    session.commit()

    alice = User.get_by_username(session, "alice")
    assert ["READ", "WRITE"] == sorted(
        permission.name for permission in alice.user_permissions
    )


def test_group_permissions(engine, session):
    _create_all(session)

    admins = Group.get_by_name(session, "admins")
    admins.permissions.append(Permission.get_by_name(session, "READ"))
    admins.permissions.append(Permission.get_by_name(session, "WRITE"))
    session.commit()

    admins = Group.get_by_name(session, "admins")
    assert ["READ", "WRITE"] == sorted(
        permission.name for permission in admins.permissions
    )


def test_permissions(engine, session):
    _create_all(session)

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
    _create_all(session)

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


def test_model_mapping_update():
    mapping = base.ModelMapping()
    mapping.update({
        "key1": "value1"
    }, key2="value2")
    mapping.update([
        ("key3", "value3")
    ])
    assert mapping == {
        "key1": "value1",
        "key2": "value2",
        "key3": "value3"
    }


def test_model_mapping_duplicate_key_error():
    key = "key"
    mapping = base.ModelMapping()
    mapping[key] = "value-1"

    with pytest.raises(RuntimeError) as exc_info:
        mapping[key] = "value-2"

    expected_msg = f"Duplicate '{key}' model found. " \
                   f"There may only be one non-abstract sub-class."
    assert str(exc_info.value) == expected_msg


def test_model_to_dict():
    base_cls = sqlalchemy.ext.declarative.declarative_base()

    class FoodEnum(str, Enum):
        pizza = "pizza"
        pasta = "pasta"

    class TestRelation(base_cls):
        __tablename__ = "test_relation"

        id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
        dict_id = sqlalchemy.Column(
            sqlalchemy.Integer,
            sqlalchemy.ForeignKey("test_model.id")
        )

    class TestModel(base_cls):
        __tablename__ = "test_model"

        id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
        dt = sqlalchemy.Column(sqlalchemy.DateTime)
        date = sqlalchemy.Column(sqlalchemy.Date)
        uuid = sqlalchemy.Column(models.GUID)
        enum = sqlalchemy.Column(sqlalchemy.Enum(FoodEnum))

        items = sqlalchemy.orm.relationship(TestRelation)

    model = TestModel(
        id=1,
        dt=datetime.now(),
        date=date.today(),
        uuid=uuid.uuid4(),
        enum=FoodEnum.pasta,
        items=[
            TestRelation(id=1),
            TestRelation(id=2),
        ]
    )
    assert base.model_as_dict(model) == {
        "id": model.id,
        "dt": model.dt.isoformat(),
        "date": model.date.isoformat(),
        "uuid": str(model.uuid),
        "enum": model.enum.name,
        # Relations like "items" are not included
    }


def test_base_as_dict(mocker):
    base_cls = sqlalchemy.ext.declarative.declarative_base(cls=base.Base)

    class TestModel(base_cls):
        __tablename__ = "test_base_as_dict"

        id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)

    model = TestModel(id=1)

    mock_model_as_dict = mocker.patch(
        "fastapi_sqlalchemy.models.base.model_as_dict")
    result = model.as_dict()
    assert mock_model_as_dict.call_args == mocker.call(model)
    assert result is mock_model_as_dict.return_value


def test_user_password():
    password = "my_secret"

    user = User(username="user1")
    user.password = password
    assert user.verify(password) is True

    user.hashed_password = None
    assert user.verify(password) is False

    with pytest.raises(RuntimeError) as exc_info:
        assert not user.password

    assert str(exc_info.value) == "Invalid access: get password not allowed"
