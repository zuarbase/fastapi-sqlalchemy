""" Generic middleware """
import logging
from typing import Union, Sequence

import jwt
from sqlalchemy.engine import Connectable
from starlette.requests import Request
from starlette.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from fastapi_sqlalchemy import db_registry
from fastapi_sqlalchemy.models import Session


PAYLOAD_HEADER_PREFIX = "x-payload-"

logger = logging.getLogger(__name__)


class SessionMiddleware(BaseHTTPMiddleware):
    """Add a `models.Session` instance to `request.state.session`.

    Close the session after each request, thus rolling back any
    not committed transactions.

    Given bind will be added to `fastapi_sqlalchemy.db_registry` and so can be
    accessed from there.
    """
    def __init__(
            self,
            app: ASGIApp,
            bind: Union[str, Connectable],
            **engine_kwargs
    ):
        super().__init__(app)
        bind = db_registry.register(bind, **engine_kwargs)
        Session.configure(bind=bind)

    async def dispatch(
            self,
            request: Request,
            call_next
    ) -> Response:
        added = False
        try:
            if not hasattr(request.state, "session"):
                request.state.session = Session()
                added = True
            response = await call_next(request)
        finally:
            if added:
                # Only close a session if we added it, useful for testing
                request.state.session.close()
        return response


class UpstreamPayloadMiddleware(BaseHTTPMiddleware):
    """Parse upstream request headers and set the result to
    `request.state.payload`.

    NOTE: there must be an upstream service (like an API Gateway) to
    ensure these headers are trusted.  Otherwise the client could set
    any desired permissions.
    """

    PAYLOAD_HEADER_PREFIX = PAYLOAD_HEADER_PREFIX

    def __init__(
            self,
            app: ASGIApp,
            header_prefix: str = PAYLOAD_HEADER_PREFIX,
    ):
        super().__init__(app=app)
        self.header_prefix = header_prefix

    async def dispatch(
            self,
            request: Request,
            call_next
    ) -> Response:
        payload = {}
        for header_name in request.headers:
            if header_name.startswith(self.header_prefix):
                name = header_name[len(self.header_prefix):]
                value = request.headers.getlist(header_name)
                if len(value) == 1:
                    payload[name] = value[0]
                else:  # pragma: nocover
                    payload[name] = value
        request.state.payload = payload
        return await call_next(request)


class JwtMiddleware(BaseHTTPMiddleware):
    """Decode a JWT token from cookies (if present) and add the results to
    `request.state.payload`."""

    def __init__(
            self,
            app: ASGIApp,
            secret: str,
            cookie_name: str = "jwt",
            algorithms: Sequence[str] = ("HS256", "HS512"),
            **kwargs,
    ):
        super().__init__(app=app)
        self.secret = secret
        self.cookie_name = cookie_name
        self.algorithms = algorithms
        self.kwargs = kwargs

    async def dispatch(
            self, request: Request, call_next
    ) -> Response:
        token = request.cookies.get(self.cookie_name)
        if token:
            try:
                payload = jwt.decode(
                    token,
                    key=self.secret,
                    algorithms=self.algorithms,
                    **self.kwargs
                )
                request.state.payload = payload
            except jwt.exceptions.InvalidTokenError as ex:
                logger.info("JWT decode error: %s", str(ex))
        else:
            logging.debug("%s: No JWT", str(request.url))

        return await call_next(request)
