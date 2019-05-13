from . import base as rotb
from .vector import earth2principal
from .base import beam2inst
from .vector import _euler2orient as euler2orient
import numpy as np
import warnings
from numpy.linalg import inv
from . import base as rotb


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
        cs_now = 'earth'
        cs_new = 'inst'
    else:
        sumstr = 'ijk,j...k->i...k'
        cs_now = 'inst'
        cs_new = 'earth'

    if rotate_vars is None:
        if 'rotate_vars' in advo.props:
            rotate_vars = advo.props['rotate_vars']
        else:
            rotate_vars = ['vel']

    cs = advo.props['coord_sys'].lower()
    if not force:
        if cs == cs_new:
            print("Data is already in the '%s' coordinate system" % cs_new)
            return
        elif cs != cs_now:
            raise ValueError(
                "Data must be in the '%s' frame when using this function" %
                cs_now)

    od = advo['orient']
    if hasattr(od, 'orientmat'):
        rmat = od['orientmat'].copy()

    else:
        rmat = euler2orient(od['heading'], od['pitch'], od['roll'])
    # Take the transpose of the orientation to get the inst->earth rotation
    # matrix.
    rmat = np.rollaxis(rmat, 1)

    _dcheck = rotb._check_rotmat_det(rmat)
    if not _dcheck.all():
        warnings.warn("Invalid orientation matrix"
                      " (determinant != 1) at"
                      " indices: {}."
                      .format(np.nonzero(~_dcheck)[0]),
                      rotb.BadDeterminantWarning)

    # The dictionary of rotation matrices for different sized arrays.
    rmd = {3: rmat, }

    # The 4-row rotation matrix assume that rows 0,1 are u,v,
    # and 2,3 are independent estimates of w.
    # Confirmed this rotation matrix with Nortek:
    # https://nortek.zendesk.com/attachments/token/g3Xal028bJkYclRph8hRdlIR2/?name=signatureAD2CP_beam2xyz_enu.m
    tmp = rmd[4] = np.zeros((4, 4, rmat.shape[-1]), dtype=np.float64)
    tmp[:3, :3] = rmat
    # Copy row 2 to 3
    tmp[3, :2] = rmat[2, :2]
    tmp[3, 3] = rmat[2, 2]
    # Extend rows 0,1
    tmp[0, 2:] = rmat[0, 2] / 2
    tmp[1, 2:] = rmat[1, 2] / 2

    # # This gets into tricky territory, because Nortek handles the
    # # 5th beam separately. Leave it out for now?
    # # The 5-row rotation matrix assume that rows 0,1 are u,v,
    # # and 2,3,4 are independent estimates of w.
    # tmp = rmd[5] = np.zeros((5, 5, rmat.shape[-1]), dtype=np.float64)
    # tmp[:3, :3] = rmat
    # # Copy row 2 to 3
    # tmp[3, :2] = rmat[2, :2]
    # tmp[3, 3] = rmat[2, 2]
    # # Copy row 2 to 4
    # tmp[4, :2] = rmat[2, :2]
    # tmp[4, 4] = rmat[2, 2]
    # # Extend rows 0,1
    # tmp[0, 2:] = rmat[0, 2] / 3
    # tmp[1, 2:] = rmat[1, 2] / 3

    if reverse:
        # 3-element inverse handled by sumstr definition (transpose)
        rmd[4] = np.moveaxis(inv(np.moveaxis(rmd[4], -1, 0)), 0, -1)

    for nm in rotate_vars:
        n = advo[nm].shape[0]
        if n == 3:
            advo[nm] = np.einsum(sumstr, rmd[3], advo[nm])
        elif n == 4:
            advo[nm] = np.einsum('ijk,j...k->i...k', rmd[4], advo[nm])
        else:
            raise Exception("The entry {} is not a vector, it cannot"
                            "be rotated.".format(nm))

    if reverse:
        rotb.call_rotate_methods(advo, np.rollaxis(rmd[3], 1), 'earth', 'inst')
    else:
        rotb.call_rotate_methods(advo, rmd[3], 'inst', 'earth')

    advo.props['coord_sys'] = cs_new

    return
