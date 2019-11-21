from starlette.requests import Request

from fastapi import Depends
from fastapi_sqlalchemy import crud, utils


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
        return await crud.create_instance(Person, session, data)

    res = client.post("/people", json=PEOPLE_DATA[0])
    assert res.status_code == 200

    response_data = res.json()
    person = session.query(Person).get(response_data["id"])
    assert person.as_dict() == response_data


def test_endpoint_duplicate(session, app, client):

    @app.post("/people", response_model=PersonResponseModel)
    async def _create_person(
            request: Request,
            data: PersonRequestModel
    ) -> dict:
        return await crud.create_instance(Person, request.state.session, data)

    res = client.post("/people", json=PEOPLE_DATA[0])
    assert res.status_code == 200

    response_data = res.json()
    person = session.query(Person).get(response_data["id"])
    assert person.as_dict() == response_data

    res = client.post("/people", json=PEOPLE_DATA[0])
    assert res.status_code == 409

    res = client.post("/people", json=PEOPLE_DATA[1])
    assert res.status_code == 200

    response_data = res.json()
    person = session.query(Person).get(response_data["id"])
    assert person.as_dict() == response_data


def test_endpoint_get_session(session, app, client):

    @app.get("/endpoint")
    async def _create_person(
            param=Depends(utils.get_session)
    ) -> dict:
        assert param

    res = client.get("/endpoint")
    assert res.status_code == 200
