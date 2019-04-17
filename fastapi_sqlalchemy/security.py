""" Authorization """
import typing

from starlette.requests import Request
from starlette.exceptions import HTTPException
from fastapi import Depends

PERMISSION_HEADER_NAME = "x-payload-permissions"

ADMIN_PERMISSION = "*"


async def read_permissions(
        request: Request,
        header_name: str = PERMISSION_HEADER_NAME
) -> list:
    """ Read permissions from the request headers """
    result = []
    for header in request.headers.getlist(header_name):
        result.extend([token.strip() for token in header.split(",")])
    if ADMIN_PERMISSION in result:
        return [ADMIN_PERMISSION]
    return result


class TrustedPermissions(Depends):
    """ permission-based authorization """
    def __init__(self):
        super().__init__(read_permissions)


def requires_any(
        permissions: typing.Sequence[str],
        allowed_permissions: typing.Sequence[str],
        status_code: int = 403
) -> None:
    """ Check that any permission is present """
    for permission in permissions:
        if permission == ADMIN_PERMISSION:
            return
        if permission in allowed_permissions:
            return
    raise HTTPException(status_code=status_code)


def requires_all(
        permissions: typing.Sequence[str],
        needed_permissions: typing.Sequence[str],
        status_code: int = 403
) -> None:
    """ Check that all permissions are present """
    if ADMIN_PERMISSION in permissions:
        return

    for permission in needed_permissions:
        if permission not in permissions:
            raise HTTPException(status_code=status_code)


def requires_admin(
        permissions: typing.Sequence[str],
        status_code: int = 403
) -> None:
    """ Check that the 'admin' permission is present """
    if ADMIN_PERMISSION not in permissions:
        raise HTTPException(status_code=status_code)
