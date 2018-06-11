"""
The base module for the adv package.
"""

from ..data import velocity as dbvel


class ADVdata(dbvel.Velocity):
    """The acoustic Doppler velocimeter (ADV) data type.

    See Also
    ========
    :class:`dolfyn.Velocity`
    """
    pass


# !CLEANUP! below this line

class ADVbinned(object):
    # This is a relic maintained here for now for backward compatability.
    def __new__(cls, *args, **kwargs):
        return ADVdata(*args, **kwargs)


class ADVraw(object):
    # This is a relic maintained here for now for backward compatability.
    def __new__(cls, *args, **kwargs):
        return ADVdata(*args, **kwargs)
