import fastapi
from fastapi_sqlalchemy import endpoints, models

SENDER = "user@example.com"
BASE_URL = "http://localhost"


class User(
        models.User, models.mixins.ConfirmationMixin, models.mixins.DictMixin
):
    __tablename__ = "test_register_users"
    __model_mapping__ = False


def test_register_get(session, app, client):
    endpoint = endpoints.RegisterEndpoint(
        User, secret="s0secret", sender=SENDER,
        form_template="<html>${title}</html>",
    )

    @app.get("/register")
    async def _get():
        return await endpoint.on_get()

    res = client.get("/register")
    assert res.status_code == 200
    assert res.text == "<html>FastAPI-SQLAlchemy</html>"


def test_register_post(session, app, client, mocker):
    endpoint = endpoints.RegisterEndpoint(
        User, secret="s0secret", sender=SENDER,
        sent_template="<html>${email}</html>",
    )
    mocker.patch.object(endpoint, "send_email_confirmation")

    @app.post("/register")
    async def _post(
            username: str = fastapi.Form(None),
            password: str = fastapi.Form(None),
            email: str = fastapi.Form(None),
    ):
        return await endpoint.on_post(
            BASE_URL, session,
            username=username, password=password, email=email
        )

    recipient = "recipient@example.com"
    res = client.post("/register", data={
        "username": "testuser",
        "password": "passw0rd",
        "email": recipient
    })
    assert res.status_code == 200
    assert res.text == f"<html>{recipient}</html>"


def test_register_post_no_confirmation(session, app, client, mocker):
    endpoint = endpoints.RegisterEndpoint(
        User, secret="s0secret", sender=SENDER,
        form_template="<html>${error}</html>"
    )
    mocker.patch.object(endpoint, "send_email_confirmation")

    @app.post("/register")
    async def _post(
            username: str = fastapi.Form(None),
            password: str = fastapi.Form(None),
            confirm_password: str = fastapi.Form(None),
            email: str = fastapi.Form(None),
    ):
        return await endpoint.on_post(
            BASE_URL, session,
            username=username, email=email,
            password=password, confirm_password=confirm_password
        )

    res = client.post("/register", data={
        "username": "testuser",
        "password": "passw0rd",
        "confirm_password": "other",
        "email": "recipient@example.com",
    })
    assert res.status_code == 400
    assert res.text == "<html>The specified passwords do not match.</html>"


def test_register_post_redo_unconfirmed(session, app, client, mocker):
    user = User(username="testuser", email="recipient@example.com")
    session.add(user)
    session.commit()

    endpoint = endpoints.RegisterEndpoint(
        User, secret="s0secret", sender=SENDER,
        sent_template="<html>${username} <${email}></html>"
    )
    mocker.patch.object(endpoint, "send_email_confirmation")

    @app.post("/register")
    async def _post(
            username: str = fastapi.Form(None),
            password: str = fastapi.Form(None),
            confirm_password: str = fastapi.Form(None),
            email: str = fastapi.Form(None),
    ):
        return await endpoint.on_post(
            BASE_URL, session,
            username=username, email=email,
            password=password, confirm_password=confirm_password
        )

    res = client.post("/register", data={
        "username": "testuser",
        "password": "passw0rd",
        "email": "recipient@example.com",
    })
    assert res.status_code == 200
    assert res.text == "<html>testuser <recipient@example.com></html>"

    assert user.verify("passw0rd")


def test_register_post_duplicate_email(session, app, client, mocker):
    user = User(username="testuser", email="recipient@example.com")
    session.add(user)
    session.commit()

    endpoint = endpoints.RegisterEndpoint(
        User, secret="s0secret", sender=SENDER,
        form_template="<html>${error}</html>"
    )
    mocker.patch.object(endpoint, "send_email_confirmation")

    @app.post("/register")
    async def _post(
            username: str = fastapi.Form(None),
            password: str = fastapi.Form(None),
            confirm_password: str = fastapi.Form(None),
            email: str = fastapi.Form(None),
    ):
        return await endpoint.on_post(
            BASE_URL, session,
            username=username, email=email,
            password=password, confirm_password=confirm_password
        )

    res = client.post("/register", data={
        "username": "testuser2",
        "password": "passw0rd",
        "email": "recipient@example.com",
    })
    assert res.status_code == 409
    assert res.text == "<html>That email address already exists.</html>"


def test_register_post_duplicate_username(session, app, client, mocker):
    user = User(username="testuser", email="recipient@example.com")
    session.add(user)
    session.commit()

    endpoint = endpoints.RegisterEndpoint(
        User, secret="s0secret", sender=SENDER,
        form_template="<html>${error}</html>"
    )
    mocker.patch.object(endpoint, "send_email_confirmation")

    @app.post("/register")
    async def _post(
            username: str = fastapi.Form(None),
            password: str = fastapi.Form(None),
            confirm_password: str = fastapi.Form(None),
            email: str = fastapi.Form(None),
    ):
        return await endpoint.on_post(
            BASE_URL, session,
            username=username, email=email,
            password=password, confirm_password=confirm_password
        )

    res = client.post("/register", data={
        "username": "testuser",
        "password": "passw0rd",
        "email": "recipient2@example.com",
    })
    assert res.status_code == 409
    assert res.text == "<html>That username already exists.</html>"
