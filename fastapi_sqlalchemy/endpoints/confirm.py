""" Confirmation of user email addresses """
import os
import logging
from typing import Union

from itsdangerous import URLSafeTimedSerializer, BadData

from starlette.responses import HTMLResponse, JSONResponse
from starlette.concurrency import run_in_threadpool

from fastapi_sqlalchemy import models, tz, utils

logger = logging.getLogger(__name__)


class ConfirmEndpoint:
    """ Class-base endpoint for email confirmation """

    ERROR_TEMPLATE = os.path.join(
        os.path.dirname(__file__), "templates", "failed_email_confirmation.html"
    )

    def __init__(
            self,
            user_cls,
            secret,
            location: str = "/login",
            max_age: int = None,
            salt: str = None,
            template: str = ERROR_TEMPLATE,
    ):
        self.user_cls = user_cls
        self.secret = secret
        self.location = location
        self.salt = salt
        self.max_age = max_age
        self.template = template

    def render(
            self,
            **kwargs
    ) -> str:
        """ Render the template using the passed parameters """
        kwargs.setdefault("error", "")
        kwargs.setdefault("title", "FastAPI-SQLAlchemy")
        kwargs.setdefault("email", "")

        return utils.render(self.template, **kwargs)

    async def on_get(
            self,
            session: models.Session,
            token,
    ) -> Union[HTMLResponse, JSONResponse]:
        """ Handle GET requests """

        def _confirm() -> Union[dict, str]:
            try:
                serializer = URLSafeTimedSerializer(self.secret)
                email = serializer.loads(
                    token,
                    salt=self.salt,
                    max_age=self.max_age,
                )
            except BadData as ex:
                logger.warning("%s: %s", token, str(ex))
                return self.render(
                    error="The confirmation link is invalid or expired."
                )

            user = self.user_cls.get_by_email(session, email)
            if not user:
                logger.info("User not found: %s", email)
                return self.render(
                    error=f"User not found: {email}"
                )

            if user.confirmed:
                logger.info(
                    "User %s <%s> already confirmed", user.username, user.email
                )
            else:
                user.confirmed_at = tz.utcnow()
                session.commit()
                logger.info(
                    "User %s <%s> confirmed", user.username, user.email
                )
            return user.as_dict()

        result = await run_in_threadpool(_confirm)
        if isinstance(result, str):
            # Error condition
            return HTMLResponse(status_code=400, content=result)

        headers = {"location": self.location}
        return JSONResponse(
            content=result,
            status_code=303,
            headers=headers
        )
