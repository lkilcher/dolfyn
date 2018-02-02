from .nortek import read_nortek
from .nortek2 import read_signature
from .rdi import read_rdi
from .base import WrongFileType as _WTF
# These are included here for use in the API
from .main import load, mmload


def read(fname, userdata=True, nens=None):
    """Read a binary Nortek (e.g., .VEC, .wpr, .ad2cp, etc.) or RDI
    (.000, .PD0, etc.) data file.

    Notes
    =====
    This function will loop over binary readers until it finds one that works.
    """
    for func in [read_nortek, read_signature, read_rdi]:
        try:
            dat = func(fname, userdata=userdata, nens=nens)
        except _WTF:
            continue
        else:
            return dat
    raise _WTF("Unable to find a suitable reader for "
               "file {}.".format(fname))
