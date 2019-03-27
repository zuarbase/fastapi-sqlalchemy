""" Logout functionality """
import logging

from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class LogoutEndpoint:
    """ Class-based endpoint for logout """

    def __init__(
            self,
            location: str = "/login",
            cookie_name: str = "jwt",
    ):
        self.cookie_name = cookie_name
        self.location = location

    # NOTE: no GET handler
    async def on_post(
            self
    ) -> JSONResponse:
        """ POST /logout """
        # 303 tells the browser to switch from POST to GET
        headers = {"location": self.location}

        # NOTE: use JSONResponse instead of RedirectResponse to
        # avoid confusing OpenAPI
        response = JSONResponse(status_code=303, headers=headers)
        response.delete_cookie(self.cookie_name)
        return response
