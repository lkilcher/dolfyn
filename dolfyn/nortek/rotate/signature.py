from .vector import earth2principal
from dolfyn.rdi.rotate import beam2inst
from .base import _check_declination, euler2orient, _check_rotmat_det
import numpy as np
import warnings


def inst2earth(advo, reverse=False, rotate_vars=None, force=False):
    """
    Rotate data in an ADV object to the earth from the instrument
    frame (or vice-versa).

    Parameters
    ----------
    advo : The adv object containing the data.

    reverse : bool (default: False)
           If True, this function performs the inverse rotation
           (principal->earth).

    rotate_vars : iterable
      The list of variables to rotate. By default this is taken from
      advo.props['rotate_vars'].

    force : Do not check which frame the data is in prior to
      performing this rotation.

    """

    if reverse:
        # The transpose of the rotation matrix gives the inverse
        # rotation, so we simply reverse the order of the einsum:
        sumstr = 'jik,j...k->i...k'
        cs_now = ['earth', 'enu']
        cs_new = ['inst', 'xyz']
    else:
        sumstr = 'ijk,j...k->i...k'
        cs_now = ['inst', 'xyz']
        cs_new = ['earth', 'enu']

    if rotate_vars is None:
        if 'rotate_vars' in advo.props:
            rotate_vars = advo.props['rotate_vars']
        else:
            rotate_vars = ['vel']

    cs = advo.props['coord_sys'].lower()
    if not force:
        if cs in cs_new:
            print("Data is already in the '%s' coordinate system" % cs_new[0])
            return
        elif cs not in cs_now:
            raise ValueError(
                "Data must be in the '%s' frame when using this function" %
                cs_now[0])

    _check_declination(advo)

    od = advo['orient']
    if hasattr(od, 'orientmat'):
        rmat = od['orientmat']

    else:
        rmat = euler2orient(od['pitch'], od['roll'], od['heading'])
    # Take the transpose of the orientation to get the inst->earth rotation
    # matrix.
    rmat = np.rollaxis(rmat, 1)

    _dcheck = _check_rotmat_det(rmat)
    if not _dcheck.all():
        warnings.warn("Invalid orientation matrix"
                      " (determinant != 1) at"
                      " indices: {}."
                      .format(np.nonzero(~_dcheck)[0]),
                      BadDeterminantWarning)
    rmatt = np.zeros((5, 5, rmat.shape[-1]), dtype=np.float64)
    rmatt[:3, :3] = rmat
    # This assumes the extra rows are all w. Therefore, we copy
    # the orientation matrix into those dims...
    # !!!FIXTHIS: Is this correct?
    rmatt[3, :2] = rmat[2, :2]
    rmatt[4, :2] = rmat[2, :2]
    rmatt[3, 3] = rmat[2, 2]
    rmatt[4, 4] = rmat[2, 2]
    rmat = rmatt

    for nm in rotate_vars:
        n = advo[nm].shape[0]
        if n < 3 or n > 5:
            # size 5 vectors are the Signature.
            raise Exception("The entry {} is not a vector, it cannot"
                            "be rotated.".format(nm))
        # subsample the orientation matrix depending on the size of the object.
        advo[nm] = np.einsum(sumstr, rmat[:n, :n], advo[nm])

    advo.props['coord_sys'] = cs_new[0]

    return
