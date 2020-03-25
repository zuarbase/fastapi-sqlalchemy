import pytest

from fastapi_sqlalchemy import types


def test_query_types_functional(app, client):
    @app.get("/types")
    def _get(
            limit: int = types.LimitQuery(50, alias="lim"),
            offset: int = types.OffsetQuery(20, alias="off")
    ):
        return {
            "limit": limit,
            "offset": offset,
        }

    response = client.get("/types", params={
        "lim": 10,
        "off": 100
    })
    assert response.status_code == 200
    assert response.json() == {
        "limit": 10,
        "offset": 100,
    }

    response = client.get("/types")
    assert response.status_code == 200
    assert response.json() == {
        "limit": 50,
        "offset": 20,
    }


def test_limit_query():
    limit = types.LimitQuery()
    assert limit.default == 100
    assert limit.alias is None
    assert limit.title == "Maximum number of entries to return"
    assert limit.description == "Maximum number of entries to return."

    # Verify that negative default value cannot be set
    with pytest.raises(AssertionError):
        types.LimitQuery(-100)


def test_offset_query():
    limit = types.OffsetQuery()
    assert limit.default == 0
    assert limit.alias is None
    assert limit.title == "Index of the first entry to return"
    assert limit.description == "Index of the first entry to return."

    # Verify that negative default value cannot be set
    with pytest.raises(AssertionError):
        types.OffsetQuery(-100)


def test_pydantic_types(app, client):
    assert types.NonNegativeInt.ge == 0

    @app.get("/types")
    def _get(
            non_negative: types.NonNegativeInt = 0
    ):
        return {
            "non_negative": non_negative
        }

    response = client.get("/types", params={
        "non_negative": 1
    })
    assert response.status_code == 200
    assert response.json() == {
        "non_negative": 1,
    }

    response = client.get("/types")
    assert response.status_code == 200
    assert response.json() == {
        "non_negative": 0,
    }

    response = client.get("/types", params={
        "non_negative": -1
    })
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail[0]["loc"] == ["query", "non_negative"]
