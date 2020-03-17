""" Extensions to pydantic.types """
from fastapi.params import Query
from pydantic import ConstrainedInt


class NonNegativeInt(ConstrainedInt):
    """ Integer >= 0 """
    ge = 0


class LimitQuery(Query):
    """ The 'limit' query parameter """
    def __init__(
            self,
            limit: int = 100,
            alias: str = None
    ):
        assert limit > 0
        super().__init__(
            limit,
            title="Maximum number of entries to return",
            description="Maximum number of entries to return.",
            alias=alias
        )


class OffsetQuery(Query):
    """ The 'offset' query parameter """
    def __init__(
            self,
            offset: int = 0,
            alias: str = None
    ):
        assert offset >= 0
        super().__init__(
            offset,
            title="Index of the first entry to return",
            description="Index of the first entry to return.",
            alias=alias
        )
