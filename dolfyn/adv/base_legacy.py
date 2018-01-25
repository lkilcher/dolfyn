"""
The base module for the adv package.
"""

from ..data import base_legacy as db
from ..io import main_legacy as dio
from ..data import velocity_legacy as dbvel
import numpy as np
# import turbulence as turb
ma = db.ma

# This is the body->imu vector (in body frame)
# In inches it is: (0.25, 0.25, 5.9)
body2imu = {'Nortek VECTOR': np.array([0.00635, 0.00635, 0.14986])}


class ADVconfig(db.config):

    """
    A base class for ADV config objects.
    """
    # Is this needed?
    pass


class ADVraw(dbvel.Velocity):

    """
    The base class for ADV data objects.
    """

    @property
    def make_model(self,):
        return self.props['inst_make'] + ' ' + self.props['inst_model']

    @property
    def body2imu_vec(self,):
        # Currently only the Nortek VECTOR has an IMU.
        return body2imu[self.make_model]


class ADVbinned(dbvel.VelBindatSpec, ADVraw):

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
    {
        'adv_raw': ADVraw,
        'adv_config': ADVconfig,
        'adv_binned': ADVbinned,
        "<class 'dolfyn.data.base.config'>": db.config,
        "<class 'dolfyn.adv.base.ADVconfig'>": ADVconfig,
    })


def load_legacy(fname, data_groups=None, type_map=type_map):
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


def mmload_legacy(fname, type_map=type_map):
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
