from fastapi_sqlalchemy import models


class User(models.User):
    pass


class Group(models.Group):
    pass


class Permission(models.Permission):
    pass
