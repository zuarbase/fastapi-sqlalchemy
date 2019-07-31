""" User model """
from passlib.hash import pbkdf2_sha512

from starlette.authentication import SimpleUser

import sqlalchemy
from sqlalchemy import event
from sqlalchemy.orm import validates

from .base import BASE, Session, MODEL_MAPPING
from . import mixins


class User(BASE, SimpleUser, mixins.GuidMixin, mixins.TimestampMixin):
    """
    The user table
    """
    __tablename__ = "users"
    __abstract__ = True

    username = sqlalchemy.Column(
        sqlalchemy.String(255),
        nullable=False,
        unique=True
    )

    hashed_password = sqlalchemy.Column(
        sqlalchemy.String(255),
        nullable=True,
    )

    def as_dict(self):
        """ Convert the User instance to a dictionary """
        result = super().as_dict()
        del result["hashed_password"]
        return result

    @validates("username")
    def _set_name(
            self,
            _key: str,
            value: str
    ) -> str:
        # pylint: disable=no-self-use
        return value.lower()

    def verify(
            self,
            secret: str
    ) -> bool:
        """ Verify a provided secret against the stored hash
        """
        if not self.hashed_password:
            return False
        return pbkdf2_sha512.verify(secret, self.hashed_password)

    @property
    def password(
            self
    ) -> None:
        """ password getter: throws RuntimeError
        """
        raise RuntimeError("Invalid access: get password not allowed")

    @password.setter
    def password(
            self, secret
    ) -> None:
        """ password setter: update the hash using the given secret
        """
        self.hashed_password = pbkdf2_sha512.hash(secret)

    @classmethod
    def get_by_username(
            cls,
            session: Session,
            name: str,
    ):
        """ Lookup a User by name
        """
        return session.query(cls).filter(cls.username == name.lower()).first()

    @property
    def identity(self) -> str:
        return str(self.id)


@event.listens_for(User, "mapper_configured", propagate=True)
def _mapper_configured(_mapper, cls):
    if getattr(cls, "__model_mapping__", True):
        MODEL_MAPPING["User"] = cls
