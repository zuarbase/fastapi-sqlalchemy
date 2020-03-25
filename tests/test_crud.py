import uuid

import pytest
import sqlalchemy.exc

from pydantic import PositiveInt
from starlette.exceptions import HTTPException

from fastapi_sqlalchemy import crud
from fastapi_sqlalchemy.types import NonNegativeInt

from tests.data.people import (
    load_people, Person, PersonRequestModel, PEOPLE_DATA
)


@pytest.fixture(name="mock_sqlalchemy_filters")
def fixture_mock_sqlalchemy_filters(mocker):
    def __query(query, *_args, **__kwargs):
        return query

    apply_filters = mocker.patch(
        "fastapi_sqlalchemy.crud.apply_filters", side_effect=__query)
    apply_sort = mocker.patch(
        "fastapi_sqlalchemy.crud.apply_sort", side_effect=__query)
    return apply_filters, apply_sort


def test_crud_list(session, loop):
    expected = [person.as_dict() for person in load_people(session)]
    actual = loop.run_until_complete(
        crud.list_instances(Person, session)
    )
    assert expected == actual


def test_crud_list_query(mocker, loop, mock_sqlalchemy_filters):
    def __query(*_args, **__kwargs):
        return mock_query

    apply_filters, apply_sort = mock_sqlalchemy_filters

    mock_query = mocker.Mock()
    mock_query.options = mocker.Mock(side_effect=__query)
    mock_query.offset = mocker.Mock(side_effect=__query)
    mock_query.limit = mocker.Mock(side_effect=__query)
    mock_query.all = mocker.Mock(return_value=[])

    session = mocker.Mock()
    session.query = mocker.Mock(return_value=mock_query)

    filter_spec = [{"filter1": "value1"}]
    sort_spec = [{"sort1": "value1"}]
    options = ("option1", "option2")
    offset = NonNegativeInt(10)
    limit = PositiveInt(50)

    loop.run_until_complete(crud.list_instances(
        Person, session, filter_spec, sort_spec, offset, limit, options
    ))
    assert apply_filters.call_args == mocker.call(mock_query, filter_spec)
    assert apply_sort.call_args == mocker.call(mock_query, sort_spec)
    assert mock_query.options.call_args == mocker.call(options)
    assert mock_query.offset.call_args == mocker.call(offset)
    assert mock_query.limit.call_args == mocker.call(limit)


def test_crud_count(session, loop):
    data = load_people(session)
    actual = loop.run_until_complete(
        crud.count_instances(Person, session)
    )
    assert len(data) == actual


def test_crud_count_query(mocker, loop, mock_sqlalchemy_filters):
    apply_filters, apply_sort = mock_sqlalchemy_filters

    mock_query = mocker.Mock()
    session = mocker.Mock(query=mocker.Mock(return_value=mock_query))

    filter_spec = [{"filter1": "value1"}]
    sort_spec = [{"sort1": "value1"}]

    loop.run_until_complete(
        crud.count_instances(Person, session, filter_spec, sort_spec)
    )
    assert apply_filters.call_args == mocker.call(mock_query, filter_spec)
    assert apply_sort.call_args == mocker.call(mock_query, sort_spec)


def test_crud_create(session, loop):
    result = loop.run_until_complete(
        crud.create_instance(
            Person, session, PersonRequestModel(**PEOPLE_DATA[0])
        )
    )
    for key in ("id", "updated_at", "created_at"):
        assert result.pop(key)
    assert result == PEOPLE_DATA[0]


def test_crud_create_409(mocker, loop):
    exc = sqlalchemy.exc.IntegrityError(
        statement="fake statement",
        params={},
        orig=Person
    )

    session = mocker.Mock()
    session.commit = mocker.Mock(side_effect=exc)

    with pytest.raises(HTTPException) as exc_info:
        loop.run_until_complete(
            crud.create_instance(
                Person, session, PersonRequestModel(**PEOPLE_DATA[0])
            )
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == str(exc.orig)


def test_crud_retrieve(session, loop):
    person = Person(**PEOPLE_DATA[0])
    session.add(person)
    session.commit()
    person = session.merge(person)

    result = loop.run_until_complete(
        crud.retrieve_instance(Person, session, person.id)
    )
    assert result == person.as_dict()


def test_crud_retrieve_404(session, loop):
    with pytest.raises(HTTPException) as exc_info:
        loop.run_until_complete(
            crud.retrieve_instance(Person, session, uuid.uuid4())
        )

    assert exc_info.value.status_code == 404


def test_crud_retrieve_query(mocker, loop):
    def __query(*_args, **__kwargs):
        return mock_query

    mock_query = mocker.Mock()
    mock_query.options = mocker.Mock(side_effect=__query)

    session = mocker.Mock()
    session.query = mocker.Mock(return_value=mock_query)

    options = ("option1", "option2")

    loop.run_until_complete(
        crud.retrieve_instance(Person, session, uuid.uuid4(), options)
    )
    assert mock_query.options.call_args == mocker.call(options)


def test_crud_update(session, loop):
    person = Person(**PEOPLE_DATA[0])
    session.add(person)
    session.commit()
    person = session.merge(person)

    assert person.name == "alice"

    data = person.as_dict()
    data["name"] = "edith"

    result = loop.run_until_complete(
        crud.update_instance(
            Person, session, person.id, PersonRequestModel(**data)
        )
    )
    assert result["name"] == "edith"

    session.refresh(person)
    assert person.name == "edith"


def test_crud_update_404(session, loop):
    with pytest.raises(HTTPException) as exc_info:
        loop.run_until_complete(
            crud.update_instance(
                Person,
                session,
                uuid.uuid4(),
                PersonRequestModel(**PEOPLE_DATA[0])
            )
        )

    assert exc_info.value.status_code == 404


def test_crud_delete(session, loop):
    person = Person(**PEOPLE_DATA[0])
    session.add(person)
    session.commit()
    person = session.merge(person)

    result = loop.run_until_complete(
        crud.delete_instance(Person, session, person.id)
    )
    assert person.as_dict() == result

    assert session.query(Person).get(person.id) is None


def test_crud_delete_404(session, loop):
    with pytest.raises(HTTPException) as exc_info:
        loop.run_until_complete(
            crud.delete_instance(Person, session, uuid.uuid4())
        )
    assert exc_info.value.status_code == 404
