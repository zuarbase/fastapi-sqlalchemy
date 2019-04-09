""" Group model """
import sqlalchemy
from sqlalchemy import event

from .base import BASE, Session, MODEL_MAPPING
from . import mixins


class Group(BASE, mixins.GuidMixin, mixins.TimestampMixin):
    """ The groups table """
    __tablename__ = "groups"
    __abstract__ = True

    name = sqlalchemy.Column(
        sqlalchemy.String(255),
        nullable=False,
    )

    @classmethod
    def get_by_name(
            cls,
            session: Session,
            name: str
    ):
        """ Lookup a group by name
        """
        return session.query(cls).filter(cls.name == name).first()


@event.listens_for(Group, "mapper_configured", propagate=True)
def _mapper_configured(_mapper, cls):
    MODEL_MAPPING["Group"] = cls
