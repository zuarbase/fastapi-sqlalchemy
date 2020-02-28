""" The main application """
from typing import Any, Dict, List, Optional, Union

from sqlalchemy.engine import Engine, Connection


from fastapi import FastAPI
from fastapi.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from fastapi.exceptions import RequestValidationError

from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse
from starlette.exceptions import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.routing import BaseRoute

from fastapi_sqlalchemy import db_registry
from fastapi_sqlalchemy.models import Session, BASE
from fastapi_sqlalchemy.middleware import session_middleware


class FastAPI_SQLAlchemy(FastAPI):
    """ Application class """

    def __init__(
            self,
            bind: Union[str, Engine, Connection, None],
            debug: bool = False,
            routes: List[BaseRoute] = None,
            template_directory: str = None,
            title: str = "Fast API",
            description: str = "",
            version: str = "0.2.0",
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
            self.bind = db_registry.register(bind, pool_pre_ping=True)
            Session.configure(bind=self.bind)
        else:
            self.bind = None

    @property
    def Session(self):
        """ Convenience property for the global Session """
        return Session

    @property
    def db_registry(self):
        """Convenience property to access DB registry,"""
        return db_registry

    def create_all(self) -> None:
        """ Create tables from the model """
        BASE.metadata.create_all(self.bind)

    def setup(self) -> None:
        """ Override setup() to not add openapi_prefix to openapi_url """
        if self.openapi_url:
            async def openapi(_req: Request) -> JSONResponse:
                return JSONResponse(self.openapi())

            self.add_route(self.openapi_url, openapi, include_in_schema=False)
            # REMOVED: openapi_url = self.openapi_prefix + self.openapi_url
        if self.openapi_url and self.docs_url:

            async def swagger_ui_html(_req: Request) -> HTMLResponse:
                return get_swagger_ui_html(
                    openapi_url=self.openapi_url,
                    title=self.title + " - Swagger UI",
                    oauth2_redirect_url=self.swagger_ui_oauth2_redirect_url,
                )

            self.add_route(
                self.docs_url, swagger_ui_html, include_in_schema=False
            )

            if self.swagger_ui_oauth2_redirect_url:
                async def swagger_ui_redirect(_req: Request) -> HTMLResponse:
                    return get_swagger_ui_oauth2_redirect_html()

                self.add_route(
                    self.swagger_ui_oauth2_redirect_url,
                    swagger_ui_redirect,
                    include_in_schema=False,
                )
        if self.openapi_url and self.redoc_url:
            async def redoc_html(_req: Request) -> HTMLResponse:
                return get_redoc_html(
                    openapi_url=self.openapi_url, title=self.title + " - ReDoc"
                )

            self.add_route(self.redoc_url, redoc_html, include_in_schema=False)
        self.add_exception_handler(HTTPException, http_exception_handler)
        self.add_exception_handler(
            RequestValidationError, request_validation_exception_handler
        )
        # ADDED
        self.add_default_middleware()

    def add_default_middleware(self) -> None:
        """ Add any default middleware """
        self.add_middleware(BaseHTTPMiddleware, dispatch=session_middleware)
