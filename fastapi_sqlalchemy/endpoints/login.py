""" Login functionality """
import os
import logging
import inspect
from string import Template
from typing import Any, Optional

import jwt

from starlette.responses import HTMLResponse, JSONResponse
from starlette.concurrency import run_in_threadpool

from fastapi_sqlalchemy import tz, models

logger = logging.getLogger(__name__)


class LoginEndpoint:
    """ Class-based endpoint for login """

    DEFAULT_TEMPLATE = os.path.join(
        os.path.dirname(__file__), "templates", "login.html"
    )

    def __init__(
            self,
            user_cls,
            secret,
            *,
            template: str = DEFAULT_TEMPLATE,
            error_status_code: int = 401,
            location: str = "/",
            token_expiry: int = 86400,  # 24 hours
            secure: bool = True,
            cookie_name: str = "jwt",
            jwt_algorithm: str = "HS256",
            form_action: str = "/login"
    ):
        assert inspect.isclass(user_cls)
        self.secret = secret
        self.user_cls = user_cls
        self.template = template.strip()
        self.error_status_code = error_status_code
        self.location = location
        self.token_expiry = token_expiry
        self.secure = secure
        self.cookie_name = cookie_name
        self.jwt_algorithm = jwt_algorithm
        self.form_action = form_action

    async def render(self, **kwargs) -> str:
        """ Render the template using the passed parameters """
        kwargs.setdefault("username", "")
        kwargs.setdefault("error", "")
        kwargs.setdefault("form_action", self.form_action)
        kwargs.setdefault("modal_title", "Login to your Account")
        kwargs.setdefault("title", "FastAPI-SQLAlchemy")

        def _read():
            with open(self.template, "r") as filp:
                content = filp.read()
            return Template(content)

        if self.template.startswith("<"):
            template = Template(self.template)
        else:
            template = await run_in_threadpool(_read)
        return template.safe_substitute(**kwargs)

    async def jwt_encode(self, payload):
        """ Build the JWT """
        assert "exp" in payload
        return jwt.encode(
            payload,
            str(self.secret),
            algorithm=self.jwt_algorithm,
        ).decode("utf-8")

    async def payload(self, user_data):
        """ Determine the JWT contents (keep for sub-classes """
        user_data.pop("password", None)
        return user_data

    async def authenticate(
            self,
            session: models.Session,
            username: str,
            password: str
    ) -> Optional[dict]:
        """ Perform authentication against database """
        def _get_by_username():
            return self.user_cls.get_by_username(username, session=session)

        user = await run_in_threadpool(_get_by_username)
        if not user:
            logger.info("Invalid user '%s'", username)
            return None

        if not user.verify(password):
            logger.info("Invalid password for user '%s'", user.username)
            return None

        logger.info("Authenticated user '%s'", user.username)
        return user.as_dict()

    async def on_get(self) -> HTMLResponse:
        """ Handle GET requests """
        html = await self.render()
        return HTMLResponse(content=html, status_code=200)

    async def on_post(
            self,
            username: str,
            password: str,
            session: models.Session = None
    ) -> Any:
        """ Handle POST requests """

        if session is None:
            session = models.Session()

        user_data = await self.authenticate(
            session,
            username=username,
            password=password
        )
        if not user_data:
            # ref: OWASP
            error = "Login failed; Invalid userID or password"
            html = await self.render(username=username, error=error)
            return HTMLResponse(
                content=html,
                status_code=self.error_status_code
            )

        result = await self.payload(user_data)

        expiry = tz.utcnow() + tz.timedelta(seconds=self.token_expiry)

        # jwt_encode will convert this to an epoch inside the token
        result["exp"] = expiry

        token = await self.jwt_encode(result)
        result["token"] = token
        result["exp"] = expiry.isoformat()

        headers = {"location": self.location}
        response = JSONResponse(
            content=result,
            status_code=303,
            headers=headers
        )
        response.set_cookie(
            self.cookie_name, token,
            path="/", expires=int(expiry.timestamp()), secure=self.secure
        )
        return response
