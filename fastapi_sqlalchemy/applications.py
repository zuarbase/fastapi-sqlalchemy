""" The main application """
from typing import Any, Dict, List, Optional, Union

from sqlalchemy.engine import Engine, Connection, create_engine


from fastapi import FastAPI
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.applications import http_exception

from starlette.responses import JSONResponse
from starlette.exceptions import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.routing import BaseRoute

from fastapi_sqlalchemy.models import Session, BASE
from fastapi_sqlalchemy.middleware import session_middleware


class FastAPI_SQLAlchemy(FastAPI):
    """ Application class for Mitto """

    def __init__(
            self,
            bind: Union[str, Engine, Connection, None],
            debug: bool = False,
            routes: List[BaseRoute] = None,
            template_directory: str = None,
            title: str = "Fast API",
            description: str = "",
            version: str = "0.1.0",
            openapi_url: Optional[str] = "/openapi.json",
            openapi_prefix: str = "",
            docs_url: Optional[str] = "/docs",
            redoc_url: Optional[str] = "/redoc",
            **extra: Dict[str, Any],
    ):
        super().__init__(
            debug=debug,
            routes=routes,
            template_directory=template_directory,
            title=title,
            description=description,
            version=version,
            openapi_url=openapi_url,
            openapi_prefix=openapi_prefix,
            docs_url=docs_url,
            redoc_url=redoc_url,
            **extra
        )
        if bind is not None:
            if isinstance(bind, str):
                self.bind = create_engine(bind, pool_pre_ping=True)
            else:
                self.bind = bind
            Session.configure(bind=self.bind)
        else:
            self.bind = None

    @property
    def Session(self):
        """ Convenience property for the global Session """
        return Session

    def create_all(self) -> None:
        """ Create tables from the model """
        BASE.metadata.create_all(self.bind)

    def setup(self) -> None:
        """ Override setup() to not add openapi_prefix to openapi_url """
        if self.openapi_url:
            self.add_route(
                self.openapi_url,
                lambda req: JSONResponse(self.openapi()),
                include_in_schema=False,
            )
        if self.openapi_url and self.docs_url:
            self.add_route(
                self.docs_url,
                lambda r: get_swagger_ui_html(
                    openapi_url=self.openapi_url,
                    title=self.title + " - Swagger UI",
                ),
                include_in_schema=False,
            )
        if self.openapi_url and self.redoc_url:
            self.add_route(
                self.redoc_url,
                lambda r: get_redoc_html(
                    openapi_url=self.openapi_url,
                    title=self.title + " - ReDoc",
                ),
                include_in_schema=False,
            )
        self.add_exception_handler(HTTPException, http_exception)
        self.add_default_middleware()

    def add_default_middleware(self) -> None:
        """ Add any default middleware """
        self.add_middleware(BaseHTTPMiddleware, dispatch=session_middleware)
