import sqlalchemy.ext.declarative

from fastapi_sqlalchemy import models
from tests.data.models import User


def test_timestamp_mixin(session):
    assert models.TimestampMixin in User.__mro__

    user = User(username="test_timestamp_mixin")
    session.add(user)
    session.commit()

    updated_at = user.updated_at
    assert user.created_at.replace(microsecond=0) == \
        updated_at.replace(microsecond=0)

    user.username = "test_timestamp_mixin__updated"
    session.add(user)
    session.commit()
    assert user.updated_at != updated_at
    assert user.created_at < user.updated_at


def test_dict_mixin(mocker):
    base_cls = sqlalchemy.ext.declarative.declarative_base()

    class TestModel(base_cls, models.DictMixin):
        __tablename__ = "test_dict_mixin"

        id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)

    model = TestModel(id=1)

    mock_model_as_dict = mocker.patch(
        "fastapi_sqlalchemy.models.mixins.model_as_dict")
    result = model.as_dict()
    assert mock_model_as_dict.call_args == mocker.call(model)
    assert result is mock_model_as_dict.return_value
