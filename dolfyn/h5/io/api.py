from .nortek import read_nortek
from .nortek2 import read_signature
from .rdi import read_rdi
from .base import WrongFileType as _WTF
# These are included here for use in the API
from .hdf5 import load
import pkg_resources


def read(fname, userdata=True, nens=None):
    """Read a binary Nortek (e.g., .VEC, .wpr, .ad2cp, etc.) or RDI
    (.000, .PD0, etc.) data file.

    Parameters
    ----------
    filename : string
               Filename of Nortek file to read.

    userdata : True, False, or string of userdata.json filename
               (default ``True``) Whether to read the
               '<base-filename>.userdata.json' file.

    nens : None (default: read entire file), int, or
           2-element tuple (start, stop)
              Number of pings to read from the file

    Returns
    -------
    dat : :class:`<~dolfyn.data.velocity.Velocity>`
      A DOLfYN velocity data object.

    """
    # Loop over binary readers until we find one that works.
    for func in [read_nortek, read_signature, read_rdi]:
        try:
            dat = func(fname, userdata=userdata, nens=nens)
        except _WTF:
            continue
        else:
            return dat
    raise _WTF("Unable to find a suitable reader for "
               "file {}.".format(fname))

def read_example(name, **kwargs):
    """Read an example data file.

    Parameters
    ==========
    name : string
        Available files:

            AWAC_test01.wpr
            BenchFile01.ad2cp
            RDI_test01.000
            burst_mode01.VEC
            vector_data01.VEC
            vector_data_imu01.VEC
            winriver01.PD0
            winriver02.PD0

    Returns
    =======
    dat : ADV or ADP data object.

    """
    filename = pkg_resources.resource_filename(
        'dolfyn',
        'example_data/' + name)
    return read(filename, **kwargs)