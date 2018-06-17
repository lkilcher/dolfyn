from __future__ import division
import numpy as np
import warnings
from numpy.linalg import inv
from .base import _check_declination, euler2orient, _check_rotmat_det, \
    BadDeterminantWarning, orient2euler


def beam2inst(advo, reverse=False, force=False):
    """
    Rotate data in an ADV object from beam coordinates to instrument
    coordinates (or vice-versa). NOTE: this only rotates variables
    starting with `'vel'` in `advo.props['rotate_vars']`.

    Parameters
    ----------
    advo : The adv object containing the data.

    reverse : bool (default: False)
           If True, this function performs the inverse rotation
           (principal->earth).

    force : Do not check which frame the data is in prior to
      performing this rotation.

    """
    transmat = advo.config.head.TransMatrix
    csin = 'beam'
    csout = 'inst'
    if reverse:
        transmat = inv(transmat)
        csin = 'inst'
        csout = 'beam'
    if not force and advo.props['coord_sys'] != csin:
        raise ValueError(
            "Data must be in the '%s' frame when using this function" %
            csin)
    for ky in advo.props['rotate_vars']:
        if not ky.startswith('vel'):
            continue
        advo[ky] = np.einsum('ij,jk->ik', transmat, advo[ky])
    advo.props['coord_sys'] = csout


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

    _check_declination(advo)

    odata = advo['orient']
    if hasattr(odata, 'orientmat'):
        # Take the transpose of the orientation to get the inst->earth rotation
        # matrix.
        rmat = np.rollaxis(odata['orientmat'], 1)

    else:
        rr = odata['roll'].copy()
        pp = odata['pitch'].copy()
        hh = odata['heading'].copy()
        if np.isnan(rr[-1]) and np.isnan(pp[-1]) and np.isnan(hh[-1]):
            # The end of the data may not have valid orientations
            lastgd = np.nonzero(~np.isnan(rr + pp + hh))[0][-1]
            rr[lastgd:] = rr[lastgd]
            pp[lastgd:] = pp[lastgd]
            hh[lastgd:] = hh[lastgd]
        if advo._make_model.startswith('nortek vector'):
            # NOTE: For Nortek Vector ADVs: 'down' configuration means the
            #       head was pointing UP!  Check the Nortek coordinate
            #       transform matlab script for more info.  The 'up'
            #       orientation corresponds to the communication cable
            #       being up.  This is ridiculous, but apparently a
            #       reality.
            rr[odata['orientation_down']] += 180

        # Take the transpose of the orientation to get the inst->earth rotation
        # matrix.
        rmat = np.rollaxis(euler2orient(pp, rr, hh), 1)

    _dcheck = _check_rotmat_det(rmat)
    if not _dcheck.all():
        warnings.warn("Invalid orientation matrix"
                      " (determinant != 1) at"
                      " indices: {}."
                      .format(np.nonzero(~_dcheck)[0]),
                      BadDeterminantWarning)

    for nm in rotate_vars:
        n = advo[nm].shape[0]
        if n != 3:
            # size 5 vectors are the Signature.
            raise Exception("The entry {} is not a vector, it cannot"
                            "be rotated.".format(nm))
        # subsample the orientation matrix depending on the size of the object.
        advo[nm] = np.einsum(sumstr, rmat, advo[nm])

    advo.props['coord_sys'] = cs_new

    return


def _rotate_vel2body(advo):
    if (np.diag(np.eye(3)) == 1).all():
        advo.props['vel_rotated2body'] = True
    if 'vel_rotated2body' in advo.props and \
       advo.props['vel_rotated2body'] is True:
        # Don't re-rotate the data if its already been rotated.
        return
    if not _check_rotmat_det(advo.props['body2head_rotmat']).all():
        raise ValueError("Invalid body-to-head rotation matrix"
                         " (determinant != 1).")
    # The transpose should do head to body.
    advo['vel'] = np.dot(advo.props['body2head_rotmat'].T, advo['vel'])
    advo.props['vel_rotated2body'] = True


def earth2principal(advo, reverse=False):
    """
    Rotate data in an ADV object to/from principal axes. If the
    principal angle is not yet computed it will be computed.

    All data in the advo.props['rotate_vars'] list will be
    rotated by the principal angle, and also if the data objet has an
    orientation matrix (orientmat) it will be rotated so that it
    represents the orientation of the ADV in the principal
    (reverse:earth) frame.

    Parameters
    ----------
    advo : The adv object containing the data.
    reverse : bool (default: False)
           If True, this function performs the inverse rotation
           (principal->earth).

    """

    if 'principal_angle' not in advo['props']:
        advo.calc_principal_angle()

    if reverse:
        ang = advo['props']['principal_angle']
        cs_now = 'principal'
        cs_new = 'earth'
    else:
        ang = -advo['props']['principal_angle']
        cs_now = 'earth'
        cs_new = 'principal'

    cs = advo.props['coord_sys'].lower()
    if cs == cs_new:
        print('Data is already in the %s coordinate system' % cs_new)
        return
    elif cs != cs_now:
        raise ValueError(
            'Data must be in the {} frame '
            'to use this function'.format(cs_now))

    if advo.props['coord_sys_principal_ref'] not in ['earth', 'enu']:
        raise ValueError("The reference system in which the principal "
                         "axes is calculated must be 'earth'.")

    # Calculate the rotation matrix:
    cp, sp = np.cos(ang), np.sin(ang)
    rotmat = np.array([[cp, -sp, 0],
                       [sp, cp, 0],
                       [0, 0, 1]], dtype=np.float32)

    # Perform the rotation:
    for nm in advo.props['rotate_vars']:
        dat = advo[nm]
        dat[:2] = np.einsum('ij,j...->i...', rotmat[:2, :2], dat[:2])

    if hasattr(advo, 'orientmat'):
        # The orientmat does earth->inst, so the orientmat needs to
        # rotate from principal to earth first. rotmat does
        # earth->principal, so we use the inverse (via index ordering)
        # This should handle the 'reverse' case also, because the
        # inverse rotmat gets applied first.
        advo['orientmat'] = np.einsum('ijl,kj->ikl',
                                      advo['orientmat'],
                                      rotmat, )

    # Finalize the output.
    advo.props['coord_sys'] = cs_new
