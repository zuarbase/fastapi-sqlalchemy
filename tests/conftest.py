import os
import asyncio

import sqlalchemy
import pytest

import fastapi
from starlette.testclient import TestClient

from fastapi_sqlalchemy import models

DATABASE_URL = os.environ["DATABASE_URL"]


@pytest.fixture(scope="function", name="loop")
def loop_fixture():
    return asyncio.new_event_loop()


@pytest.fixture(scope="function", name="app")
def app_fixture():
    return fastapi.FastAPI(
        title="fastapi_sqlalchemy",
        version="0.0.0"
    )


@pytest.fixture(scope="function", name="client")
def client_fixture(app):
    client = TestClient(app)
    return client


@pytest.fixture(scope="session", name="engine")
def engine_fixture():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    models.Session.configure(bind=engine)
    return engine


@pytest.fixture(scope="function", name="session")
def session_fixture(engine):

    def _drop_all():
        meta = sqlalchemy.MetaData()
        meta.reflect(bind=engine)
        meta.drop_all(bind=engine)

    _drop_all()
    models.BASE.metadata.create_all(engine)
    yield models.Session()
    models.Session.remove()

    # FIXME: clear all models after each run
    # models.BASE.metadata.clear()
    # models.base.MODEL_MAPPING.clear()
    _drop_all()
