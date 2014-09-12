from ..data import base as db
from ..io import main as dio
from ..data import velocity as dbvel
# import turbulence as turb
ma = db.ma


class adv_config(db.config):

    """
    A base class for ADV config objects.
    """
    # Is this needed?
    pass


class adv_raw(dbvel.velocity):

    def has_imu(self,):
        return hasattr(self, 'Accel') | hasattr(self, 'Veloc')


class adv_binned(dbvel.vel_bindat_spec, adv_raw):

    """
    A base class for binned ADV objects.
    """
    # Is this needed?
    pass


# Get the data classes in the current namespace:
type_map = dio.get_typemap(__name__)


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
