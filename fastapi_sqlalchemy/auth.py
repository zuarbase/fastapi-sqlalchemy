""" authentication and authorization """
import logging
from typing import Dict, List, Optional, Tuple

from fastapi import Request
from fastapi.security import SecurityScopes
from fastapi import status
from starlette.authentication import (
    AuthenticationBackend, AuthCredentials, SimpleUser
)
from starlette.concurrency import run_in_threadpool
from starlette.exceptions import HTTPException
from starlette.requests import HTTPConnection

ADMIN_SCOPE = "*"

logger = logging.getLogger(__name__)


class PayloadAuthBackend(AuthenticationBackend):
    """ Get auth information from the request payload """

    def __init__(
            self,
            user_cls: type = None,
            admin_scope: str = ADMIN_SCOPE,
    ):
        super().__init__()
        self.user_cls = user_cls
        self.admin_scope = admin_scope

    async def scopes(self, payload: Dict[str, str]) -> List[str]:
        """ Return the list of scopes """
        if "scopes" in payload:
            scopes = payload["scopes"]
        elif "permissions" in payload:
            scopes = payload["permissions"]
        else:
            return []

        if isinstance(scopes, str):
            scopes = [scopes]

        if self.admin_scope and self.admin_scope in scopes:
            return [self.admin_scope]

        result = []
        for scope in scopes:
            result.extend([token.strip() for token in scope.split(",")])

        return result

    async def authenticate(
            self, conn: HTTPConnection
    ) -> Optional[Tuple["AuthCredentials", "BaseUser"]]:
        try:
            payload = conn.state.payload
        except AttributeError:
            raise RuntimeError(
                "Missing 'request.state.payload': "
                "try adding 'middleware.UpstreamPayloadMiddleware'"
            )

        username = payload.get("username")
        if not username:
            return

        if self.user_cls:
            try:
                session = conn.state.session
            except AttributeError:
                raise RuntimeError(
                    "Missing 'request.state.session': "
                    "try adding 'middleware.SessionMiddleware'"
                )

            user = await run_in_threadpool(
                self.user_cls.get_by_username, session, username
            )
            if not user:
                logger.warning("User not found: %s", username)
                return
        else:
            user = SimpleUser(username=username)

        scopes = await self.scopes(payload)
        return AuthCredentials(scopes), user


def validate_authenticated(request: Request):
    """Validate that 'request.user' is authenticated.

    Usage:
        >>> from fastapi import Depends
        >>> @app.get("/my_name", dependencies=[
        ...    Depends(validate_authenticated)
        ... ])
    """
    user: SimpleUser = getattr(request, "user", None)
    if user is not None and not user.is_authenticated:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)


def validate_all_scopes(request: Request, scopes: SecurityScopes):
    """Validate that all defined scopes exist in 'request.auth.scopes'.

    Usage:
        >>> from fastapi import Security
        >>> @app.get("/my_name", dependencies=[
        ...    Security(validate_all_scopes, scopes=["read", "write"])
        ... ])
    """
    req_scopes = request.auth.scopes
    if not all(scope in req_scopes for scope in scopes.scopes):
        raise HTTPException(status.HTTP_403_FORBIDDEN)


def validate_any_scope(request: Request, scopes: SecurityScopes):
    """Validate that at least one defined scope exists in 'request.auth.scopes'.

    Usage:
        >>> from fastapi import Security
        >>> @app.get("/my_name", dependencies=[
        ...    Security(validate_any_scope, scopes=["read", "write"])
        ... ])
    """
    req_scopes = request.auth.scopes
    if not any(scope in req_scopes for scope in scopes.scopes):
        raise HTTPException(status.HTTP_403_FORBIDDEN)
