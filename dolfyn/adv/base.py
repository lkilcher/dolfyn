"""
The base module for the adv package.
"""

from ..data import base as db
from ..io import main as dio
from ..data import velocity as dbvel
# import turbulence as turb
ma = db.ma


class ADVconfig(db.config):

    """
    A base class for ADV config objects.
    """
    # Is this needed?
    pass


class ADVraw(dbvel.velocity):

    """
    The base class for ADV data objects.
    """

    def has_imu(self,):
        """
        Test whether this data object contains Inertial Motion Unit
        (IMU) data.
        """
        return hasattr(self, 'Accel') | hasattr(self, 'Veloc')


class ADVbinned(dbvel.vel_bindat_spec, ADVraw):

    """
    A base class for binned ADV objects.
    """
    # Is this needed?
    pass


# Get the data classes in the current namespace:
type_map = dio.get_typemap(__name__)
# This is for backward compatability (I changed the names of these
# classes to conform with PEP8 standards):
type_map.update(
    {'adv_raw': ADVraw,
     'adv_config': ADVconfig,
     'adv_binned': ADVbinned,
     })


def load(fname, data_groups=None, type_map=type_map):
    """
    Load ADV objects from hdf5 format.

    Parameters
    ----------
    fname : string
      The file to load.
    data_groups : {list(strings), None, 'ALL'}
      Specifies which groups to load.  It can be:

      - :class:`None`: Load default groups (those not starting with a '#')
      - :class:`list`: A list of groups to load (plus 'essential' groups, ie
        those starting with '_')
      - 'ALL': Load all groups.

    type_map : dict, type
      A dictionary that maps `class-strings` (stored in the data file)
      to available classes.
    """
    with dio.loader(fname, type_map) as ldr:
        return ldr.load(data_groups)


def mmload(fname, type_map=type_map):
    """
    Memory-map load ADV objects from hdf5 format.

    Parameters
    ----------
    fname : string
      The file to load.
    type_map : dict, type
      A dictionary that maps `class-strings` (stored in the data file)
      to available classes.
    """
    with dio.loader(fname, type_map) as ldr:
        return ldr.mmload('ALL')
