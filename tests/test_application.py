"""Tests for application module."""
from fastapi_sqlalchemy import FastAPI_SQLAlchemy


def test_application(engine):
    app = FastAPI_SQLAlchemy(engine)
    assert app.bind is engine
    assert app.Session.kw["bind"] is engine
    assert app.db_registry
