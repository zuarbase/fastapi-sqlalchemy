import pytest

from fastapi_sqlalchemy.models import base, events


@pytest.fixture(name="mapper")
def fixture_model_mapping(mocker) -> dict:
    return mocker.patch("fastapi_sqlalchemy.models.events.MODEL_MAPPING", {})


@pytest.mark.parametrize("table,relation", (
    ["group_membership", ("User", "Group")],
    ["user_permissions", ("User", "Permission")],
    ["group_permissions", ("Group", "Permission")],
))
def test_permissions_configuration_errors(
        table, relation, mocker, mapper
):
    mocker.patch.object(base.BASE.metadata, "tables", {
        table: mocker.Mock(__association__=table)
    })

    # Test no first relation
    with pytest.raises(RuntimeError) as exc_info:
        events._after_configured()  # pylint: disable=protected-access

    error_msg = f"'{table}' association table found, " \
                f"but no {relation[0]} table defined."
    assert str(exc_info.value) == error_msg

    # Test no second relation
    mapper[relation[0]] = mocker.Mock()
    with pytest.raises(RuntimeError) as exc_info:
        events._after_configured()  # pylint: disable=protected-access

    error_msg = f"'{table}' association table found, " \
                f"but no {relation[1]} table defined."
    assert str(exc_info.value) == error_msg


def test_mapper_configuration_duplicate_key(mocker):
    duplicate_association = "duplicate-table"

    mocker.patch.object(base.BASE.metadata, "tables", {
        "table-1": mocker.Mock(__association__=duplicate_association),
        "table-2": mocker.Mock(__association__=duplicate_association)
    })

    with pytest.raises(RuntimeError) as exc_info:
        events._after_configured()  # pylint: disable=protected-access

    error_msg = f"Multiple '{duplicate_association}' associations found." \
                "Only a single table may have a specific __association__ value"
    assert str(exc_info.value) == error_msg
