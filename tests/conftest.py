import os
import asyncio

import sqlalchemy
import pytest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from fastapi_sqlalchemy import models

DATABASE_URL = os.environ["DATABASE_URL"]


@pytest.fixture(scope="function", name="loop")
def loop_fixture():
    return asyncio.new_event_loop()


@pytest.fixture(scope="session", name="engine")
def engine_fixture() -> sqlalchemy.engine.Engine:
    engine = sqlalchemy.create_engine(DATABASE_URL)
    return engine


@pytest.fixture(scope="function", name="session")
def session_fixture(engine):

    def _drop_all():
        meta = sqlalchemy.MetaData()
        meta.reflect(bind=engine)
        meta.drop_all(bind=engine)

    _drop_all()
    models.BASE.metadata.create_all(engine)

    models.Session.configure(bind=engine)
    session = models.Session()

    yield session
    session.close()


@pytest.fixture(scope="function", name="app")
def app_fixture(engine):
    app = FastAPI(
        title="fastapi_sqlalchemy",
        version="0.0.0"
    )
    return app


@pytest.fixture(scope="function", name="client")
def client_fixture(app):
    client = TestClient(app)
    return client
