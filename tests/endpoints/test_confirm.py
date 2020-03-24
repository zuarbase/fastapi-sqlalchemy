from datetime import datetime

from itsdangerous import URLSafeTimedSerializer

from fastapi_sqlalchemy import endpoints, models


class User(
        models.User, models.mixins.ConfirmationMixin, models.mixins.DictMixin
):
    __tablename__ = "test_confirm_users"
    __model_mapping__ = False


def test_confirm(session, app, client):
    endpoint = endpoints.ConfirmEndpoint(
        User, secret="s0secret",
    )

    user = User(username="testuser", email="recipient@example.org")
    session.add(user)
    session.commit()

    token_ = URLSafeTimedSerializer("s0secret").dumps(user.email, salt=None)

    @app.get("/confirm/{token}")
    async def _get(
            token: str
    ):
        return await endpoint.on_get(session, token)

    res = client.get(f"/confirm/{token_}", allow_redirects=False)
    assert res.status_code == 303
    assert res.headers.get("location") == "/login"


def test_confirm_user_already_confirmed(session, app, client):
    endpoint = endpoints.ConfirmEndpoint(
        User, secret="s0secret",
    )

    user = User(
        username="testuser",
        email="recipient@example.org",
        confirmed_at=datetime.now()
    )
    session.add(user)
    session.commit()

    token_ = URLSafeTimedSerializer("s0secret").dumps(user.email, salt=None)

    @app.get("/confirm/{token}")
    async def _get(
            token: str
    ):
        return await endpoint.on_get(session, token)

    res = client.get(f"/confirm/{token_}", allow_redirects=False)
    assert res.status_code == 303
    assert res.headers.get("location") == "/login"


def test_confirm_user_not_found(session, app, client):
    endpoint = endpoints.ConfirmEndpoint(
        User, secret="s0secret", template="<${error}"
    )

    nonexistent_email = "nonexistent@local.example.com"
    token_ = URLSafeTimedSerializer(
        "s0secret").dumps(nonexistent_email, salt=None)

    @app.get("/confirm/{token}")
    async def _get(
            token: str
    ):
        return await endpoint.on_get(session, token)

    res = client.get(f"/confirm/{token_}", allow_redirects=False)
    assert res.status_code == 400
    assert res.text == f"<User not found: {nonexistent_email}"


def test_confirm_error(session, app, client):
    endpoint = endpoints.ConfirmEndpoint(
        User,
        secret="s0secret",
        template="<${error}"
    )

    @app.get("/confirm/{token}")
    async def _get(
            token: str
    ):
        return await endpoint.on_get(session, token)

    res = client.get("/confirm/bad-token")
    assert res.status_code == 400
    assert res.text == "<The confirmation link is invalid or expired."
