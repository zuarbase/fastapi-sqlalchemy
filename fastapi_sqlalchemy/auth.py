""" authentication and authorization """
import logging
import asyncio
import inspect
import functools
import typing

from starlette.exceptions import HTTPException
from starlette.requests import HTTPConnection, Request
from starlette.responses import Response
from starlette.concurrency import run_in_threadpool
from starlette.websockets import WebSocket
from starlette.responses import RedirectResponse
from starlette.authentication import (
    AuthenticationBackend, AuthCredentials, SimpleUser
)


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

    async def scopes(self, payload):
        """ Return the list of scopes """
        scopes = []
        if "scopes" in payload:
            scopes = payload["scopes"]
        elif "permissions" in payload:
            scopes = payload["permissions"]

        if isinstance(scopes, str):
            scopes = [scopes]

        result = []
        for scope in scopes:
            result.extend([token.strip() for token in scope.split(",")])

        if self.admin_scope and self.admin_scope in scopes:
            return [self.admin_scope]

        return result

    async def authenticate(
            self,
            conn: HTTPConnection
    ):
        payload = getattr(conn.state, "payload", None)
        if not payload:
            return

        username = payload.get("username")
        if not username:
            return

        try:
            session = conn.state.session
        except AttributeError:
            raise RuntimeError(
                "Missing session: try adding SessionMiddleware."
            )

        if self.user_cls:
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


def _requires(
        test_conn: typing.Callable,
        status_code: int = 403,
        redirect: str = None
) -> typing.Callable:
    """ starlette.authentication.requires """

    def _getarg(args, idx):
        return args[idx] if idx < len(args) else None

    def decorator(func: typing.Callable) -> typing.Callable:
        sig = inspect.signature(func)

        idx = -1
        for idx, parameter in enumerate(sig.parameters.values()):
            if parameter.name == "request" or parameter.name == "websocket":
                parameter_type = parameter.name
                break
        else:
            raise Exception(
                f'No "request" or "websocket" argument on function "{func}"'
            )

        if parameter_type == "websocket":
            # Handle websocket functions. (Always async)
            @functools.wraps(func)
            async def websocket_wrapper(
                    *args: typing.Any,
                    **kwargs: typing.Any
            ) -> None:
                websocket = kwargs.get("websocket", _getarg(args, idx))
                assert isinstance(websocket, WebSocket)

                if not test_conn(websocket):
                    await websocket.close()
                else:
                    await func(*args, **kwargs)

            return websocket_wrapper

        if asyncio.iscoroutinefunction(func):
            # Handle async request/response functions.
            @functools.wraps(func)
            async def async_wrapper(
                    *args: typing.Any,
                    **kwargs: typing.Any
            ) -> Response:
                print(kwargs)
                request = kwargs.get("request", _getarg(args, idx))
                assert isinstance(request, Request)

                if not test_conn(request):
                    if redirect is not None:
                        return RedirectResponse(url=request.url_for(redirect))
                    raise HTTPException(status_code=status_code)
                return await func(*args, **kwargs)

            return async_wrapper

        # Handle sync request/response functions.
        @functools.wraps(func)
        def sync_wrapper(
                *args: typing.Any,
                **kwargs: typing.Any
        ) -> Response:
            request = kwargs.get("request", _getarg(args, idx))
            assert isinstance(request, Request)

            if not test_conn(request):
                if redirect is not None:
                    return RedirectResponse(url=request.url_for(redirect))
                raise HTTPException(status_code=status_code)
            return func(*args, **kwargs)

        return sync_wrapper

    return decorator


def requires_any(
        scopes: typing.Union[str, typing.Sequence[str]],
        status_code: int = 403,
        redirect: str = None,
        admin_scope: str = ADMIN_SCOPE,
) -> typing.Callable:
    """ Any specified scope is allowed (or admin) """
    scopes_list = [scopes] if isinstance(scopes, str) else list(scopes)

    def _has_any_scope(conn: HTTPConnection) -> bool:
        """ Test if all scopes are present (or admin) """
        if not conn.user.is_authenticated:
            return False
        if admin_scope and admin_scope in conn.auth.scopes:
            return True
        for scope in scopes_list:
            if scope in conn.auth.scopes:
                return True
        return False

    return _requires(
        _has_any_scope, status_code=status_code, redirect=redirect
    )


def requires_all(
        scopes: typing.Union[str, typing.Sequence[str]],
        status_code: int = 403,
        redirect: str = None,
        admin_scope: str = ADMIN_SCOPE,
) -> typing.Callable:
    """ All specified scopes are required (or admin) """
    scopes_list = [scopes] if isinstance(scopes, str) else list(scopes)

    def _has_all_scopes(conn: HTTPConnection) -> bool:
        if not conn.user.is_authenticated:
            return False
        if admin_scope and admin_scope in conn.auth.scopes:
            return True
        for scope in scopes_list:
            if scope not in conn.auth.scopes:
                return False
        return True

    return _requires(
        _has_all_scopes, status_code=status_code, redirect=redirect
    )


def requires_admin(
        status_code: int = 403,
        redirect: str = None,
        admin_scope: str = ADMIN_SCOPE,
) -> typing.Callable:
    """ Requires the admin scope """
    return requires_any(
        [], status_code=status_code, redirect=redirect, admin_scope=admin_scope
    )


def authenticated(
        status_code: int = 403,
        redirect: str = None,
        admin_scope: str = ADMIN_SCOPE,
) -> typing.Callable:
    """ Requires the admin scope """
    return requires_all(
        [], status_code=status_code, redirect=redirect, admin_scope=admin_scope
    )
