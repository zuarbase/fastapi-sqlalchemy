from starlette.middleware.base import BaseHTTPMiddleware

from fastapi_sqlalchemy import crud
from fastapi_sqlalchemy.models import Session
from fastapi_sqlalchemy.middleware import session_middleware


from .people import (
    Person,
    PersonRequestModel,
    PersonResponseModel,
    PEOPLE_DATA
)


def test_endpoint(session, app, client):

    @app.post("/people", response_model=PersonResponseModel)
    async def _create_person(
            data: PersonRequestModel
    ) -> dict:
        return await crud.create_instance(Person, data)

    res = client.post("/people", json=PEOPLE_DATA[0])
    assert res.status_code == 200

    response_data = res.json()
    person = Session.query(Person).get(response_data["id"])
    assert person.as_dict() == response_data


def test_endpoint_duplicate(session, app, client):

    @app.post("/people", response_model=PersonResponseModel)
    async def _create_person(
            data: PersonRequestModel
    ) -> dict:
        return await crud.create_instance(Person, data)

    app.add_middleware(BaseHTTPMiddleware, dispatch=session_middleware)

    res = client.post("/people", json=PEOPLE_DATA[0])
    assert res.status_code == 200

    response_data = res.json()
    person = Session.query(Person).get(response_data["id"])
    assert person.as_dict() == response_data

    res = client.post("/people", json=PEOPLE_DATA[0])
    assert res.status_code == 409

    res = client.post("/people", json=PEOPLE_DATA[1])
    assert res.status_code == 200

    response_data = res.json()
    person = Session.query(Person).get(response_data["id"])
    assert person.as_dict() == response_data
