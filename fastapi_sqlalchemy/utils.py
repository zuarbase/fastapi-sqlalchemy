""" Utility functions """
from string import Template
import uuid

import jwt

from starlette.requests import Request


try:
    from ordered_uuid import OrderedUUID
    HAVE_ORDERED_UUID = True
except ImportError:
    HAVE_ORDERED_UUID = False


def ordered_uuid(value=None):
    """ Generate a rearranged uuid1 that is ordered by time.
    This is a more efficient for use as a primary key, see:
    https://www.percona.com/blog/2014/12/19/store-uuid-optimized-way/
    """
    if not HAVE_ORDERED_UUID:
        raise RuntimeError("ordered_uuid package: not found")
    if not value:
        value = str(uuid.uuid1())
    return OrderedUUID(value)


def render(
        path_or_template: str,
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
    """ Get Session from a request
    usage: session = Depends(get_session)
    """
    return request.state.session


def jwt_encode(payload, secret, algorithm="HS256"):
    """ Encode the given payload as a JWT """
    assert "exp" in payload
    return jwt.encode(
        payload,
        str(secret),
        algorithm=algorithm,
    ).decode("utf-8")
