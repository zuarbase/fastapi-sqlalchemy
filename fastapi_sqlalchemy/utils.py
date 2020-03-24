""" Utility functions """
import uuid

from string import Template
from typing import Union

import jwt
from starlette.requests import Request

try:
    from ordered_uuid import OrderedUUID
except ImportError:
    OrderedUUID = None


def ordered_uuid(value=None) -> OrderedUUID:
    """ Generate a rearranged uuid1 that is ordered by time.
    This is a more efficient for use as a primary key, see:
    https://www.percona.com/blog/2014/12/19/store-uuid-optimized-way/
    """
    if OrderedUUID is None:
        raise RuntimeError("ordered_uuid package: not found")
    if not value:
        value = str(uuid.uuid1())
    return OrderedUUID(value)


def render(
        path_or_template: Union[str, Template],
        **kwargs,
) -> str:
    """ Render the specified template - either a file or the actual template """
    if isinstance(path_or_template, Template):
        template = path_or_template
    elif path_or_template.startswith("<"):
        template = Template(path_or_template)
    else:
        with open(path_or_template, "r") as filp:
            contents = filp.read()
        template = Template(contents)
    return template.safe_substitute(**kwargs)


def get_session(request: Request):
    """Get `request.state.session`

    Usage:
        >>> from fastapi import Depends
        >>> session = Depends(get_session)
    """
    return request.state.session


def jwt_encode(payload: dict, secret: str, algorithm: str = "HS256") -> str:
    """ Encode the given payload as a JWT """
    assert "exp" in payload
    return jwt.encode(
        payload,
        str(secret),
        algorithm=algorithm,
    ).decode("utf-8")
