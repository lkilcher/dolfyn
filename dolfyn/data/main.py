from ..io import Saveable, get_typemap, loader
from base import Dprops
# from binned import bindat


class basic(Saveable, Dprops):

    @property
    def shape(self,):
        return self.mpltime.shape


type_map = get_typemap(__name__)
                       # Get the data classes in the current namespace.


def load(fname, type_map=type_map, data_groups=None):
    """
    A function for loading basic data objects.

    'data_groups' specifies which groups to load.  It can be:
        None  - Load default groups (those not starting with a '#')
        [...] - A list of groups to load (plus 'essential' groups, ie
        those starting with '_')
        'ALL' - Load all groups.
    """
    with loader(fname, type_map) as ldr:
        return ldr.load(data_groups)
