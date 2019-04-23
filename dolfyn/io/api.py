from .nortek import read_nortek
from .nortek2 import read_signature
from .rdi import read_rdi
from .base import WrongFileType as _WTF
# These are included here for use in the API
from .hdf5 import load


def read(fname, userdata=True, nens=None, keep_orient_raw=False):
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

    keep_orient_raw : bool (default: False)
        If this is set to True, the raw orientation heading/pitch/roll
        data is retained in the returned data structure in the
        ``dat['orient']['raw']`` data group. This data is exactly as
        it was found in the binary data file, and obeys the instrument
        manufacturers definitions not DOLfYN's.

    Returns
    -------
    dat : :class:`<~dolfyn.data.velocity.Velocity>`
      A DOLfYN velocity data object.

    """
    # Loop over binary readers until we find one that works.
    for func in [read_nortek, read_signature, read_rdi]:
        try:
            dat = func(fname, userdata=userdata, nens=nens,
                       keep_orient_raw=keep_orient_raw)
        except _WTF:
            continue
        else:
            return dat
    raise _WTF("Unable to find a suitable reader for "
               "file {}.".format(fname))
