""" Utility functions """
import uuid

try:
    from ordered_uuid import OrderedUUID
    HAVE_ORDERED_UUID = True
except ImportError:
    HAVE_ORDERED_UUID = False


def ordered_uuid(value=None):
    """ Generate a rearranged uuid1 that is ordered by time.
    This is a more efficient for use as a primary key, see:
    https://www.percona.com/blog/2014/12/19/store-uuid-optimized-way/
    """
    if not HAVE_ORDERED_UUID:
        raise RuntimeError("ordered_uuid package: not found")
    if not value:
        value = str(uuid.uuid1())
    return OrderedUUID(value)
