from datetime import datetime, timedelta

import fastapi
import jwt

from fastapi_sqlalchemy import endpoints

from tests.data.models import User


def test_login_get(session, app, client):
    template = "<html>${title}</html>"
    endpoint = endpoints.LoginEndpoint(
        User, secret="s0secret", template=template
    )

    @app.get("/login")
    async def _get():
        return await endpoint.on_get()

    res = client.get("/login")
    assert res.status_code == 200
    assert res.text == "<html>FastAPI-SQLAlchemy</html>"


def test_login_post(mocker, engine, session, app, client):
    now_dt = datetime.utcnow()
    mocker.patch("fastapi_sqlalchemy.tz.utcnow", return_value=now_dt)

    user = User(username="alice")
    user.password = "test123"
    session.add(user)
    session.commit()
    user = session.merge(user)

    endpoint = endpoints.LoginEndpoint(User, secret="s0secret")

    @app.post("/login")
    async def _post(
            username: str = fastapi.Form(None),
            password: str = fastapi.Form(None)
    ):
        return await endpoint.on_post(session, username, password)

    expected_exp = now_dt + timedelta(seconds=endpoint.token_expiry)
    expected_exp = expected_exp.isoformat()

    expected_data = {
        **user.as_dict(),
        "exp": expected_exp,
    }
    expected_token = jwt.encode(
        expected_data,
        endpoint.secret,
        algorithm=endpoint.jwt_algorithm
    ).decode("utf-8")

    res = client.post(
        "/login",
        data={
            "username": "alice",
            "password": "test123",
        }
    )
    assert res.status_code == 303
    assert res.headers.get("location") == "/"
    assert res.cookies.items() == [
        ("jwt", expected_token)
    ]
    assert res.json() == {
        **expected_data,
        "token": expected_token
    }


def test_login_post_username_not_found(engine, session, app, client):
    endpoint = endpoints.LoginEndpoint(
        User,
        secret="s0secret",
        template="<${error}"
    )

    @app.post("/login")
    async def _post(
            username: str = fastapi.Form(None),
            password: str = fastapi.Form(None)
    ):
        return await endpoint.on_post(session, username, password)

    res = client.post("/login", data={
        "username": "alice",
        "password": "test123",
    })
    assert res.status_code == 401
    assert res.text == "<Login failed; Invalid userID or password"


def test_login_post_invalid_password(engine, session, app, client):
    password = "test123"
    user = User(username="alice")
    user.password = password
    session.add(user)
    session.commit()

    endpoint = endpoints.LoginEndpoint(
        User,
        secret="s0secret",
        template="<${error}"
    )

    @app.post("/login")
    async def _post(
            username: str = fastapi.Form(None),
            password: str = fastapi.Form(None)
    ):
        return await endpoint.on_post(session, username, password)

    res = client.post("/login", data={
        "username": "alice",
        "password": password + "make_it_invalid",
    })
    assert res.status_code == 401
    assert res.text == "<Login failed; Invalid userID or password"
