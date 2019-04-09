from fastapi_sqlalchemy import crud

from .people import load_people, Person, PersonRequestModel, PEOPLE_DATA


def test_crud_list(session, loop):
    expected = [person.as_dict() for person in load_people()]
    assert len(expected) == len(PEOPLE_DATA)
    assert expected == loop.run_until_complete(
        crud.list_instances(Person, session)
    )


def test_crud_count(session, loop):
    data = load_people()
    assert len(data) == loop.run_until_complete(
        crud.count_instances(Person, session)
    )


def test_crud_create(session, loop):
    result = loop.run_until_complete(
        crud.create_instance(
            Person, session, PersonRequestModel(**PEOPLE_DATA[0])
        )
    )
    for key in ("id", "updated_at", "created_at"):
        assert result.pop(key)
    assert result == PEOPLE_DATA[0]


def test_crud_retrieve(session, loop):
    person = Person(**PEOPLE_DATA[0])
    session.add(person)
    session.commit()
    person = session.merge(person)

    result = loop.run_until_complete(
        crud.retrieve_instance(Person, session, person.id)
    )
    assert result == person.as_dict()


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
