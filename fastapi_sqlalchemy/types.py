""" Extensions to pydantic.types """

from pydantic import ConstrainedInt


class NonNegativeInt(ConstrainedInt):
    """ Integer >= 0 """
    ge = 0
