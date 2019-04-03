""" Generic middleware """
from starlette.requests import Request
from starlette.responses import Response

from .models import Session


async def session_middleware(request: Request, call_next):
    """
    Close the session after each request, thus rolling back any
    not committed transactions.  The session is also stored as part
    of the request via request.state.session.
    """
    response = Response("", status_code=500)
    try:
        request.state.session = Session()
        response = await call_next(request)
    finally:
        request.state.session.close()
    return response
