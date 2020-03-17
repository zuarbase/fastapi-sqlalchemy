import pytest

from fastapi_sqlalchemy import db_registry


@pytest.fixture(name="mock_lock", autouse=True)
def fixture_mock_lock(mocker):
    return mocker.patch("threading.Lock")


@pytest.fixture(name="mock_create_engine")
def fixture_mock_create_engine(mocker):
    return mocker.patch(
        "fastapi_sqlalchemy.db_registry.create_engine",
        side_effect=lambda url, **kwargs: mocker.Mock(url=url, **kwargs))


def test_register_existing_engine(mocker, mock_create_engine):
    url = "/fake/url"
    engine = mocker.Mock(url=url)
    engine.engine = engine  # Follow Connectable interface

    db_registry.register(engine)

    registered_engine = db_registry.get_or_create(url)
    assert registered_engine is engine, "New engine instance was created."


def test_register_url(mocker, mock_create_engine):
    url = "/fake/url"

    kwargs = {"key1": "value1", "echo": True}
    created_engine = db_registry.register(url, **kwargs)
    assert created_engine

    registered_engine = db_registry.get_or_create(url)
    assert registered_engine is created_engine

    assert mock_create_engine.call_args_list == [
        mocker.call(url, pool_pre_ping=True, **kwargs)
    ]


def test_get_or_create_by_url(mock_create_engine):
    url_1 = "/fake/url/1"
    url_2 = "/fake/url/2"

    created_engine_1 = db_registry.get_or_create(url_1)
    assert created_engine_1

    created_engine_2 = db_registry.get_or_create(url_2)
    assert created_engine_2

    registered_engine_1 = db_registry.get_or_create(url_1)
    assert registered_engine_1 is created_engine_1

    registered_engine_2 = db_registry.get_or_create(url_2)
    assert registered_engine_2 is created_engine_2

    assert mock_create_engine.call_count == 2
