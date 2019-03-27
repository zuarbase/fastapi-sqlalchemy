from fastapi_sqlalchemy import endpoints


def test_logout_post(engine, session, app, client):
    endpoint = endpoints.LogoutEndpoint()

    @app.post("/logout")
    async def _post():
        return await endpoint.on_post()

    res = client.post("/logout")
    assert res.status_code == 303
    assert res.headers.get("location") == "/login"
