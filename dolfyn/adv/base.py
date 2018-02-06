"""
The base module for the adv package.
"""

from ..data import velocity as dbvel


class ADVraw(dbvel.Velocity):

    """
    The base class for ADV data objects.
    """
    # Is this needed?
    pass


class ADVbinned(dbvel.VelTkeData, ADVraw):

    """
    A base class for binned ADV objects.
    """
    # Is this needed?
    pass
