import uuid

import pytest

from sqlalchemy import Column, Integer, MetaData, Table
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.declarative import declarative_base

from fastapi_sqlalchemy.models import types


def test_guid_type_functional(session):
    meta = MetaData()
    table = Table(
        "test_guid_type",
        meta,
        Column("id", types.GUID, primary_key=True, default=uuid.uuid4),
        Column("other_id", types.GUID)
    )
    table.create(session.bind)

    other_id_uuid = uuid.uuid4()
    other_id_str = str(uuid.uuid4())

    # pylint: disable=no-value-for-parameter
    session.execute(table.insert(), {"other_id": other_id_uuid})
    session.execute(table.insert(), {"other_id": other_id_str})
    session.execute(table.insert(), {"other_id": None})
    # pylint: enable=no-value-for-parameter
    session.commit()

    rows = session.execute(table.select()).fetchall()
    rows = list(map(dict, rows))
    assert len(rows) == 3

    assert isinstance(rows[0]["id"], uuid.UUID)
    assert isinstance(rows[0]["other_id"], uuid.UUID)
    assert rows[0]["other_id"] == other_id_uuid

    assert isinstance(rows[1]["id"], uuid.UUID)
    assert isinstance(rows[1]["other_id"], uuid.UUID)
    assert str(rows[1]["other_id"]) == other_id_str

    assert isinstance(rows[2]["id"], uuid.UUID)
    assert rows[2]["other_id"] is None


def test_guid_type(mocker):
    guid = types.GUID()

    dialect_postgresql = mocker.Mock()
    dialect_postgresql.name = "postgresql"
    dialect_postgresql.type_descriptor = lambda _val: _val

    dialect_impl = guid.load_dialect_impl(dialect_postgresql)
    assert isinstance(dialect_impl, postgresql.UUID)

    value = uuid.uuid4()
    bind_param = guid.process_bind_param(value, dialect_postgresql)
    assert isinstance(bind_param, str)
    assert bind_param == str(value)

    with pytest.raises(NotImplementedError):
        guid.process_literal_param(value=mocker.Mock(), dialect=mocker.Mock())

    with pytest.raises(NotImplementedError):
        assert not guid.python_type


def test_json_encoded_dict_type_functional(session):
    base_cls = declarative_base()

    class TestModel(base_cls):
        __tablename__ = "test_json_encoded_dict_type"

        id = Column(Integer, primary_key=True)

        mutable_data = Column(types.JSON_TYPE)
        non_mutable_data = Column(types.JSONEncodedDict)

    base_cls.metadata.create_all(session.bind)

    mutable_data = {"key": "value"}
    non_mutable_data = {"fixed-key": "fixed-value"}
    model = TestModel(
        mutable_data=mutable_data,
        non_mutable_data=non_mutable_data
    )
    session.add(model)
    session.commit()
    model = session.merge(model)

    assert model.mutable_data == mutable_data
    assert model.non_mutable_data == non_mutable_data

    model.mutable_data["key"] = "updated-value"
    model.mutable_data["new-key"] = "new-value"
    model.non_mutable_data["fixed-key"] = "updated-fixed-value"
    model.non_mutable_data["new-fixed-key"] = "new-fixed-value"
    session.commit()

    assert model.mutable_data == {
        "key": "updated-value",
        "new-key": "new-value"
    }
    # All changes should be reset after commit()
    assert model.non_mutable_data == non_mutable_data

    row = session.query(TestModel).filter(
        TestModel.mutable_data.like("%updated-value%"),
        TestModel.non_mutable_data.notlike("%new-fixed-value%")
    ).one()
    assert row is model

    row = session.query(TestModel).filter(
        TestModel.non_mutable_data == non_mutable_data
    ).one()
    assert row is model


def test_json_encoded_dict_type(mocker):
    json_type = types.JSONEncodedDict()

    with pytest.raises(NotImplementedError):
        json_type.process_literal_param(
            value=mocker.Mock(), dialect=mocker.Mock())

    with pytest.raises(NotImplementedError):
        assert not json_type.python_type
