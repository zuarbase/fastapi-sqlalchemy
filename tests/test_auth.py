import pytest
from fastapi import Depends, Security
from starlette.authentication import SimpleUser
from starlette.datastructures import State
from starlette.requests import Request
from starlette.middleware.authentication import AuthenticationMiddleware

from fastapi_sqlalchemy import auth, middleware, models


class User(
        models.User, models.mixins.DictMixin
):
    __tablename__ = "test_middleware_users"
    __model_mapping__ = False


def test_auth(session, app, client):
    user = User(username="testuser")
    session.add(user)
    session.commit()

    @app.get("/ping")
    def _ping():
        return "pong"

    @app.get(
        "/me",
        dependencies=[
            Depends(auth.validate_authenticated),
        ]
    )
    async def _get(request: Request):
        return {
            "user": request.user.as_dict(),
            "scopes": request.auth.scopes
        }

    @app.post(
        "/me/scopes",
        dependencies=[
            Depends(auth.validate_authenticated),
            Security(auth.validate_all_scopes, scopes=["test-scope", "write"])
        ]
    )
    def _post(request: Request, ):
        return {
            "user": request.user.as_dict(),
            "scopes": request.auth.scopes
        }

    app.add_middleware(
        AuthenticationMiddleware, backend=auth.PayloadAuthBackend(user_cls=User)
    )
    app.add_middleware(middleware.UpstreamPayloadMiddleware)
    app.add_middleware(middleware.SessionMiddleware, bind=session.bind)

    # Test /ping - no auth & authz required
    res = client.get("/ping")
    assert res.status_code == 200, res.text
    assert res.text == '"pong"'

    # Test /me - auth required, no authz
    res = client.get("/me", headers={
        "X-Payload-username": user.username
    })
    assert res.status_code == 200, res.text
    assert res.json() == {
        "user": user.as_dict(),
        "scopes": []
    }

    # Test /me/scopes - auth & authz required
    res = client.post("/me/scopes", headers={
        "X-Payload-username": user.username,
        "X-Payload-permissions": "test-scope,write"
    })
    assert res.status_code == 200, res.text
    assert res.json() == {
        "user": user.as_dict(),
        "scopes": ["test-scope", "write"]
    }


def test_auth_not_authenticated(session, app, client):

    @app.get(
        "/me",
        dependencies=[Depends(auth.validate_authenticated)]
    )
    async def _get():
        return {}

    app.add_middleware(
        AuthenticationMiddleware, backend=auth.PayloadAuthBackend(user_cls=User)
    )
    app.add_middleware(middleware.UpstreamPayloadMiddleware)
    app.add_middleware(middleware.SessionMiddleware, bind=session.bind)

    payload_prefix = middleware.UpstreamPayloadMiddleware.PAYLOAD_HEADER_PREFIX

    res = client.get("/me", headers={
        f"{payload_prefix}username": "nonexistent_user"
    })
    assert res.status_code == 401


def test_auth_not_authorized(session, app, client):
    user = User(username="testuser")
    session.add(user)
    session.commit()

    @app.get(
        "/me",
        dependencies=[
            Depends(auth.validate_authenticated),
            Security(auth.validate_all_scopes, scopes=["me"])
        ]
    )
    async def _get():
        return {}

    app.add_middleware(
        AuthenticationMiddleware, backend=auth.PayloadAuthBackend(user_cls=User)
    )
    app.add_middleware(middleware.UpstreamPayloadMiddleware)
    app.add_middleware(middleware.SessionMiddleware, bind=session.bind)

    payload_prefix = middleware.UpstreamPayloadMiddleware.PAYLOAD_HEADER_PREFIX

    res = client.get("/me", headers={
        f"{payload_prefix}username": user.username,
        f"{payload_prefix}permissions": "read,write"  # no "me" scope
    })
    assert res.status_code == 403


def test_auth_any_scope(session, app, client):
    user = User(username="testuser")
    session.add(user)
    session.commit()

    @app.get(
        "/me",
        dependencies=[
            Depends(auth.validate_authenticated),
            Security(auth.validate_any_scope, scopes=["admin", "read"])
        ]
    )
    async def _get():
        return {}

    app.add_middleware(
        AuthenticationMiddleware, backend=auth.PayloadAuthBackend(user_cls=User)
    )
    app.add_middleware(middleware.UpstreamPayloadMiddleware)
    app.add_middleware(middleware.SessionMiddleware, bind=session.bind)

    payload_prefix = middleware.UpstreamPayloadMiddleware.PAYLOAD_HEADER_PREFIX

    # Test request with only "admin" scope
    res = client.get("/me", headers={
        f"{payload_prefix}username": user.username,
        f"{payload_prefix}permissions": "admin"
    })
    assert res.status_code == 200

    # Test request with only "read" scope
    res = client.get("/me", headers={
        f"{payload_prefix}username": user.username,
        f"{payload_prefix}permissions": "read"
    })
    assert res.status_code == 200

    # Test request without any scope
    res = client.get("/me", headers={
        f"{payload_prefix}username": user.username,
        f"{payload_prefix}permissions": ""
    })
    assert res.status_code == 403


def test_payload_auth_backend():
    backend = auth.PayloadAuthBackend(user_cls=User, admin_scope="admin")
    assert backend.user_cls is User
    assert backend.admin_scope == "admin"


def test_payload_auth_no_user_cls(mocker, loop):
    expected_username = "user1"

    backend = auth.PayloadAuthBackend()

    mock_conn = mocker.Mock(state=State({
        "payload": {"username": expected_username}
    }))
    result = loop.run_until_complete(backend.authenticate(mock_conn))
    assert result is not None
    assert len(result) == 2
    assert isinstance(result[1], SimpleUser)
    assert result[1].username == expected_username


def test_payload_auth_backend_scopes(loop):
    backend = auth.PayloadAuthBackend(admin_scope="admin")

    result = loop.run_until_complete(backend.scopes({
        "scopes": "read, write"
    }))
    assert result == ["read", "write"]

    result = loop.run_until_complete(backend.scopes({
        "permissions": "read, write"
    }))
    assert result == ["read", "write"]

    result = loop.run_until_complete(backend.scopes({}))
    assert result == []

    result = loop.run_until_complete(backend.scopes({
        "permissions": "admin"
    }))
    assert result == ["admin"]


def test_payload_auth_backend_missing_payload_error(mocker, loop):
    backend = auth.PayloadAuthBackend()

    mock_conn = mocker.Mock(state=State())
    with pytest.raises(RuntimeError) as exc_info:
        loop.run_until_complete(backend.authenticate(mock_conn))

    error_msg = "Missing 'request.state.payload': " \
                "try adding 'middleware.UpstreamPayloadMiddleware'"
    assert str(exc_info.value) == error_msg


def test_payload_auth_backend_missing_session_error(mocker, loop):
    backend = auth.PayloadAuthBackend(user_cls=User)

    mock_conn = mocker.Mock(state=State({
        "payload": {"username": "user1"}
    }))
    with pytest.raises(RuntimeError) as exc_info:
        loop.run_until_complete(backend.authenticate(mock_conn))

    error_msg = "Missing 'request.state.session': " \
                "try adding 'middleware.SessionMiddleware'"
    assert str(exc_info.value) == error_msg
