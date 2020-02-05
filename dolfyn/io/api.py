from .nortek import read_nortek
from .nortek2 import read_signature
from .rdi import read_rdi
from .base import WrongFileType as _WTF
# These are included here for use in the API
from .hdf5 import load
from ..base import Path


def read(fname, userdata=True, nens=None):
    """Read a binary Nortek (e.g., .VEC, .wpr, .ad2cp, etc.) or RDI
    (.000, .PD0, etc.) data file.

    Parameters
    ----------
    filename : string or pathlib.Path
               Filename of the file to read.

    userdata : True, False, or string or Path of userdata.json filename
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
    if not isinstance(fname, Path):
        fname = Path(fname)
    # Now resolve it.
    fname = str(fname.resolve())
    if not isinstance(userdata, bool):
        if not isinstance(fname, Path):
            # It should be a string.
            userdata = Path(userdata)
        # Now resolve it.
        userdata = str(userdata.resolve())
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
