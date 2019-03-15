""" Authorization """
import typing

from starlette.requests import Request
from starlette.exceptions import HTTPException
from fastapi import Depends

SCOPE_HEADER_NAME = "x-payload-scopes"


async def read_scopes(
        request: Request,
        header_name: str = SCOPE_HEADER_NAME
) -> list:
    """ Read scopes from the request headers """
    result = []
    for header in request.headers.getlist(header_name):
        result.extend([token.strip() for token in header.split(",")])
    return result


class TrustedScope(Depends):
    """ scope-based authorization """
    def __init__(self, header_name=SCOPE_HEADER_NAME):
        super().__init__(read_scopes)


def requires_any(
        scopes: typing.Sequence[str],
        allowed_scopes: typing.Sequence[str],
        status_code: int = 403
) -> None:
    """ Check that any scope is present """
    for scope in scopes:
        if scope in allowed_scopes:
            return
    raise HTTPException(status_code=status_code)


def requires_all(
        scopes: typing.Sequence[str],
        needed_scopes: typing.Sequence[str],
        status_code: int = 403
) -> None:
    """ Check that all scopes are present """
    if "admin" in scopes:
        return

    for scope in needed_scopes:
        if scope not in scopes:
            raise HTTPException(status_code=status_code)


def requires_admin(
        scopes: typing.Sequence[str],
        status_code: int = 403
) -> None:
    """ Check that the 'admin' scope is present """
    if "admin" not in scopes:
        raise HTTPException(status_code=status_code)
