""" The main application """
from typing import Optional, Union

from fastapi import FastAPI
from sqlalchemy.engine import create_engine, Engine
from sqlalchemy.orm import sessionmaker

from fastapi_sqlalchemy import db_registry
from fastapi_sqlalchemy.models import Session, BASE


class FastAPI_SQLAlchemy(FastAPI):
    """ Application class """

    bind: Optional[Engine] = None

    def set_bind(self, bind: Union[str, Engine], **engine_kwargs):
        """Create sqlalchemy engine from a given url and/or store it."""
        if isinstance(bind, str):
            self.bind = create_engine(
                bind, pool_pre_ping=True, **engine_kwargs)
        else:
            self.bind = bind

        Session.configure(bind=self.bind)

    @property
    def Session(self) -> sessionmaker:
        """ Convenience property for the global Session """
        return Session

    @property
    def db_registry(self):
        """Convenience property to access DB registry,"""
        return db_registry

    def create_all(self) -> None:
        """ Create tables from the model """
        if self.bind is None:
            raise TypeError("bind cannot be None.")

        BASE.metadata.create_all(self.bind)
