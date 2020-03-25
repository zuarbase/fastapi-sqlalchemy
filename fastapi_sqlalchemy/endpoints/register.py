""" Registration functionality """
import os
import logging
import inspect

import ssl
import smtplib
from email.message import EmailMessage

import sqlalchemy.exc
from itsdangerous import URLSafeTimedSerializer
from pydantic import EmailStr

from starlette.responses import HTMLResponse
from starlette.concurrency import run_in_threadpool

from fastapi_sqlalchemy import models, utils

logger = logging.getLogger(__name__)


class RegisterEndpoint:
    """ Class-based endpoint for registration with confirmation """

    FORM_TEMPLATE = os.path.join(
        os.path.dirname(__file__), "templates", "register.html"
    )

    CONFIRMATION_HTML_TEMPLATE = os.path.join(
        os.path.dirname(__file__), "templates", "confirmation_email.html"
    )

    CONFIRMATION_TEXT_TEMPLATE = os.path.join(
        os.path.dirname(__file__), "templates", "confirmation_email.txt"
    )

    SENT_TEMPLATE = os.path.join(
        os.path.dirname(__file__), "templates", "send_confirmation.html"
    )

    def __init__(
            self,
            user_cls,
            secret,
            sender,
            *,
            form_template: str = FORM_TEMPLATE,
            confirmation_html_template: str = CONFIRMATION_HTML_TEMPLATE,
            confirmation_text_template: str = CONFIRMATION_TEXT_TEMPLATE,
            sent_template: str = SENT_TEMPLATE,
            form_action: str = "/register",
            salt: str = None,
            email_subject: str = "Email confirmation",
            email_server: str = "localhost",  # local smtp server
            email_port: str = 0,  # use default
            email_use_ssl: bool = False,
            email_use_tls: bool = False,
            email_login: str = None,
            email_password: str = None,
            confirm_url: str = "/confirm"
    ):
        # pylint: disable=too-many-locals
        assert inspect.isclass(user_cls)
        self.user_cls = user_cls
        self.secret = secret
        self.sender = sender

        self.form_template = form_template
        self.confirmation_html_template = confirmation_html_template
        self.confirmation_text_template = confirmation_text_template
        self.sent_template = sent_template

        self.form_action = form_action
        self.salt = salt

        self.email_subject = email_subject
        self.email_server = email_server
        self.email_port = email_port
        self.email_use_ssl = email_use_ssl
        self.email_use_tls = email_use_tls
        self.email_login = email_login
        self.email_password = email_password

        if not confirm_url.endswith("/"):
            confirm_url += "/"
        self.confirm_url = confirm_url

    @staticmethod
    def render(
            path_or_template: str,
            **kwargs
    ) -> str:
        """ Render the template using the passed parameters """
        kwargs.setdefault("error", "")
        kwargs.setdefault("title", "FastAPI-SQLAlchemy")
        kwargs.setdefault("modal_title", "Register")
        kwargs.setdefault("username", "")
        kwargs.setdefault("email", "")

        return utils.render(path_or_template, **kwargs)

    def render_form(
            self,
            **kwargs
    ) -> str:
        """ Render the registration form """
        kwargs["form_action"] = self.form_action
        return self.render(self.form_template, **kwargs)

    async def on_get(self) -> HTMLResponse:
        """ Handle GET requests """
        html = await run_in_threadpool(self.render_form)
        return HTMLResponse(content=html, status_code=200)

    def _confirmation_token(self, email):
        serializer = URLSafeTimedSerializer(self.secret)
        return serializer.dumps(email, salt=self.salt)

    @staticmethod
    def validate_password(password):
        """ Validate the password format is acceptable """
        if password and len(password) >= 7:
            return None
        raise ValueError(
            "Invalid password - the password must be at least 7 characters."
        )

    def send_message(
            self,
            msg: EmailMessage
    ) -> None:
        """ Delivery the email message """
        if self.email_use_ssl:
            smtp = smtplib.SMTP_SSL(self.email_server, self.email_port)
        else:
            smtp = smtplib.SMTP(self.email_server, self.email_port)

        if self.email_use_tls:
            context = ssl.create_default_context()
            smtp.starttls(context=context)

        if self.email_login:
            smtp.login(self.email_login, self.email_password)

        smtp.send_message(msg)
        smtp.close()

    def send_email_confirmation(self, base_url, email, **kwargs):
        """ Send the email with a confirmation link """
        logger.info("Sending email to %s from %s", email, self.sender)

        msg = EmailMessage()
        msg["Subject"] = self.email_subject
        msg["From"] = self.sender
        msg["To"] = [email]

        confirm_url = self.confirm_url + self._confirmation_token(email)
        if not confirm_url.startswith("http"):
            # Assume relative URL
            confirm_url = base_url + confirm_url

        data = {**{
            "email": email,
            "sender": self.sender,
            "subject": self.email_subject,
            "base_url": base_url,
            "confirm_url": confirm_url,
        }, **kwargs}

        msg.set_content(
            self.render(self.confirmation_text_template, **data)
        )
        msg.add_alternative(
            self.render(self.confirmation_html_template, **data),
            subtype="html"
        )

        try:
            self.send_message(msg)
            logger.info(
                "Email sent to %s with confirm URL: %s", email, confirm_url
            )
        # pylint: disable=bare-except
        except:  # noqa
            logging.exception("EMAIL FAILED TO SEND: %s", email)
        # pylint: enable=bare-except

    async def on_post(
            self,
            base_url: str,
            session: models.Session,
            username: str,
            email: str,
            password: str,
            confirm_password: str = None,
            **kwargs
    ) -> HTMLResponse:
        """ Handle POST requests """

        email = EmailStr.validate(email)

        def _register() -> (int, str):

            try:
                self.validate_password(password)
            except ValueError as ex:
                return 400, self.render_form(error=str(ex), **kwargs)

            if confirm_password is not None:
                # The only way for confirm_password to be None is if a
                # standard form doesn't include it, otherwise the value is ""
                if password != confirm_password:
                    return 400, self.render_form(
                        error="The specified passwords do not match.",
                        **kwargs
                    )

            user = self.user_cls.get_by_email(session, email)
            if user:
                if user.username != username:
                    logger.info("Email '%s' already exists.", email)
                    # Is this an information leak?
                    return 409, self.render_form(
                        error="That email address already exists.", **kwargs
                    )
                if user.confirmed:
                    logger.info("User '%s' already confirmed.", username)
                else:
                    # Unconfirmed, re-registration - update password
                    user.password = password
            else:
                user = self.user_cls(
                    username=username,
                    password=password,
                    email=email,
                )
                session.add(user)

            try:
                session.commit()
            except sqlalchemy.exc.IntegrityError:
                # pragma: no-cover
                return 409, self.render_form(
                    error="That username already exists.", **kwargs
                )

            self.send_email_confirmation(
                base_url, email, username=username, **kwargs
            )

            return 200, self.render(
                self.sent_template,
                username=username, email=email, **kwargs
            )

        status_code, content = await run_in_threadpool(_register)
        return HTMLResponse(status_code=status_code, content=content)
