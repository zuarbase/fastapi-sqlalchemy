from starlette.requests import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.authentication import AuthenticationMiddleware

from fastapi_sqlalchemy import middleware, models, auth
from fastapi_sqlalchemy.auth import authenticated


class User(
        models.User, models.mixins.DictMixin
):
    __tablename__ = "test_middleware_users"
    __model_mapping__ = False


def test_auth(session, app, client):

    user = User(username="testuser")
    session.add(user)
    session.commit()

    @app.get("/me")
    async def _get(
            request: Request
    ):
        return {
            "payload": request.state.payload,
            "user": request.user.as_dict(),
            "scopes": request.auth.scopes
        }

    app.add_middleware(
        AuthenticationMiddleware, backend=auth.PayloadAuthBackend(user_cls=User)
    )
    app.add_middleware(middleware.UpstreamPayloadMiddleware)
    app.add_middleware(
        BaseHTTPMiddleware,
        dispatch=middleware.session_middleware
    )

    headers = {
        "X-Payload-username": user.username,
        "X-Payload-permissions": "read,write,exec"
    }

    res = client.get("/me", headers=headers)
    assert res.status_code == 200

    result = res.json()
    assert result["user"] == user.as_dict()
    assert result["scopes"] == ["read", "write", "exec"]


def test_auth_not_authenticated(session, app, client):

    @app.get("/me")
    @authenticated()
    async def _get(
            request: Request
    ):
        return {}

    app.add_middleware(
        AuthenticationMiddleware, backend=auth.PayloadAuthBackend(user_cls=User)
    )

    res = client.get("/me")
    assert res.status_code == 403
