""" Generic CRUD operations """
from uuid import UUID
from typing import List, Dict, Any

import sqlalchemy.exc
from pydantic import BaseModel, PositiveInt
from starlette.exceptions import HTTPException
from starlette.concurrency import run_in_threadpool

from sqlalchemy_filters import apply_filters, apply_sort

from . import models, types

# NOTE: always use the session of the caller
# i.e. don't us models.Session in the thread pool synchronous functions
# This is necessary in sqlite3 (at least) to ensure consistency.


async def list_instances(
        cls: models.BASE,
        session: models.Session,
        filter_spec: List[Dict[str, Any]] = None,
        sort_spec: List[Dict[str, str]] = None,
        offset: types.NonNegativeInt = 0,
        limit: PositiveInt = None,
        options: Any = None
) -> List[dict]:
    """ Return all instances of cls """
    query = session.query(cls)
    if filter_spec:
        query = apply_filters(query, filter_spec)
    if sort_spec:
        query = apply_sort(query, sort_spec)

    if options:
        query = query.options(options)

    if limit:
        query = query.limit(limit)
    query = query.offset(offset)

    def _list():
        return [instance.as_dict() for instance in query.all()]

    return await run_in_threadpool(_list)


async def count_instances(
        cls: models.BASE,
        session: models.Session,
        filter_spec: List[Dict[str, Any]] = None,
        sort_spec: List[Dict[str, Any]] = None,
) -> int:
    """ Total count of instances matching the given criteria """
    query = session.query(cls)
    if filter_spec:
        query = apply_filters(query, filter_spec)
    if sort_spec:
        query = apply_sort(query, sort_spec)

    def _count():
        return query.count()

    return await run_in_threadpool(_count)


async def create_instance(
        cls: models.BASE,
        session: models.Session,
        data: BaseModel
) -> dict:
    """ Create an instances of cls with the provided data """
    instance = cls(**data.dict())

    def _create():
        session.add(instance)
        session.commit()
        return session.merge(instance).as_dict()

    try:
        return await run_in_threadpool(_create)
    except sqlalchemy.exc.IntegrityError as ex:
        raise HTTPException(status_code=409, detail=str(ex.orig))


async def retrieve_instance(
        cls: models.BASE,
        session: models.Session,
        instance_id: UUID,
        options: Any = None
) -> dict:
    """ Get an instance of cls by UUID """
    query = session.query(cls)

    if options:
        query = query.options(options)

    def _retrieve():
        instance = query.get(instance_id)
        if instance:
            return instance.as_dict()
        return None

    data = await run_in_threadpool(_retrieve)
    if data is None:
        raise HTTPException(status_code=404)
    return data


async def update_instance(
        cls: models.BASE,
        session: models.Session,
        instance_id: UUID,
        data: BaseModel) -> dict:
    """ Fully update an instances using the provided data """

    def _update():
        instance = session.query(cls).get(instance_id)
        if not instance:
            return None
        for key, value in data.dict().items():
            setattr(instance, key, value)
        session.commit()
        return session.merge(instance).as_dict()

    data = await run_in_threadpool(_update)
    if data is None:
        raise HTTPException(status_code=404)
    return data


async def delete_instance(
        cls: models.BASE,
        session: models.Session,
        instance_id: UUID
) -> dict:
    """ Delete an instance by UUID """

    def _delete():
        instance = session.query(cls).get(instance_id)
        if not instance:
            return None
        result = instance.as_dict()
        session.delete(instance)
        session.commit()
        return result

    data = await run_in_threadpool(_delete)
    if data is None:
        raise HTTPException(status_code=404)
    return data
