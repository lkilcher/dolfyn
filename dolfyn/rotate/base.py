import numpy as np
from numpy.linalg import det


class BadDeterminantWarning(UserWarning):
    """A warning for the determinant is not equal to 1.
    """
    pass


def _find_method(obj, string):
    """Find methods in object that starts with `string`.
    """
    out = []
    for key in dir(obj):
        if key.startswith(string):
            out.append(getattr(obj, key))
    return out


def call_rotate_methods(velobj, rmat, cs_from, cs_to):

    for rot_method in _find_method(velobj, '_rotate_'):
        # Call the method:
        rot_method(rmat, cs_from, cs_to)
    # Now search subgroups
    for subobj in velobj.iter_subgroups():
        for rot_method in _find_method(subobj, '_rotate_'):
            # And call their rotate methods
            rot_method(rmat, cs_from, cs_to)


def rotate_tensor(tensor, rmat):
    return np.einsum('ij...,jlm...,nl...->inm...', rmat, tensor, rmat)


def is_positive_definite(tensor):
    t = np.moveaxis(tensor, [0, 1], [-2, -1])
    val = t[..., 0, 0] > 0
    for idx in [2, 3]:
        val &= np.linalg.det(t[..., :idx, :idx]) > 0
    return val


def _check_rotmat_det(rotmat, thresh=1e-3):
    """Check that the absolute error of the determinant is small.

          abs(det(rotmat) - 1) < thresh

    Returns a boolean array.
    """
    if rotmat.ndim > 2:
        rotmat = np.transpose(rotmat)
    return np.abs(det(rotmat) - 1) < thresh


def euler2orient(heading, pitch, roll, units='degrees'):
    """
    Calculate the orientation matrix from euler angles.

    Parameters
    ----------
    heading : np.ndarray (Nt)
      The heading angle of the ADV (clockwise from North).
    pitch : np.ndarray (Nt)
      The pitch angle of the ADV.
    roll : np.ndarray (Nt)
      The pitch angle of the ADV.
    units : string {'degrees' (default), 'radians'}

    Returns
    =======
    omat : np.ndarray (3x3xNt)
      The orientation matrix of the data. The returned orientation
      matrix obeys the following conventions:

       - a "ZYX" rotation order. That is, these variables are computed
         assuming that rotation from the earth -> instrument frame happens
         by rotating around the z-axis first (heading), then rotating
         around the y-axis (pitch), then rotating around the x-axis (roll).

       - heading is defined as the direction the x-axis points, positive
         clockwise from North (this is *opposite* the right-hand-rule
         around the Z-axis)

       - pitch is positive when the x-axis pitches up (this is *opposite* the
         right-hand-rule around the Y-axis)

       - roll is positive according to the right-hand-rule around the
         instument's x-axis

    """
    if units.lower() == 'degrees':
        pitch = np.deg2rad(pitch)
        roll = np.deg2rad(roll)
        heading = np.deg2rad(heading)
    elif units.lower() == 'radians':
        pass
    else:
        raise Exception("Invalid units")

    heading = np.pi / 2 - heading

    ch = np.cos(heading)
    sh = np.sin(heading)
    cp = np.cos(pitch)
    sp = np.sin(pitch)
    cr = np.cos(roll)
    sr = np.sin(roll)
    zero = np.zeros_like(sr)
    one = np.ones_like(sr)

    H = np.array(
        [[ch, sh, zero],
         [-sh, ch, zero],
         [zero, zero, one], ])
    P = np.array(
        [[cp, zero, sp],
         [zero, one, zero],
         [-sp, zero, cp], ])
    R = np.array(
        [[one, zero, zero],
         [zero, cr, sr],
         [zero, -sr, cr], ])

    return np.einsum('ij...,jk...,kl...->il...', R, P, H)


def orient2euler(omat):
    """
    Calculate the euler angles from the orientation matrix.

    Parameters
    ----------
    advo : np.ndarray (or :class:`<~dolfyn.data.velocity.Velocity>`)
      The orientation matrix (or a data object containing one).

    Returns
    -------
    heading : np.ndarray
      The heading angle of the ADV (degrees clockwise from North).
    pitch : np.ndarray
      The pitch angle of the ADV (degrees).
    roll : np.ndarray
      The pitch angle of the ADV (degrees).

    """
    if isinstance(omat, np.ndarray) and \
            omat.shape[:2] == (3, 3):
        pass
    elif hasattr(omat['orient'], 'orientmat'):
        omat = omat['orient'].orientmat
    # #####
    # Heading is direction of +x axis clockwise from north.
    # So, for arctan (opposite/adjacent) we want arctan(east/north)
    # omat columns have been reorganized in io.nortek.NortekReader.sci_microstrain to ENU
    # (not the original NED from the Microstrain)

    # Some conventions use rotation matrices as inst->earth, but this omat is 
    # earth->inst, so the order of indices may be reversed from some conventions.
    hh = np.rad2deg(np.arctan2(omat[0, 0], omat[0, 1]))
    hh %= 360
    return (
        # heading (+x axis clockwise from north, range 0-360 rather than -180 to +180)
        hh,
        # pitch (positive up)
        np.rad2deg(np.arcsin(omat[0, 2])),
        # roll
        np.rad2deg(np.arctan2(omat[1, 2], omat[2, 2])),
    )


def calc_principal_angle(vel, tidal_mode=True):
    """
    Compute the principal angle of the horizontal velocity.

    Parameters
    ----------
    vel : np.ndarray (2,...,Nt), or (3,...,Nt)
      The 2D or 3D velocity array (3rd-dim is ignored in this calculation)

    tidal_mode : bool (default: True)

    Returns
    -------
    p_ang : float or ndarray
      The principal angle(s) in radians.

    Notes
    -----

    The tidal mode rotates half of the vectors (negative v) by 180
    degreees, then doubles those angles (to make a complete circle
    again), and computes a mean direction from this. It then halves
    the angle again. The returned angle will always be between 0 and
    :math:`pi` for this mode. So, you may need to add :math:`pi` to
    this if you want your positive direction to be in the
    southern-half of the plane.

    Otherwise, this function simply compute the average direction
    using a vector method.

    """
    dt = vel[0] + vel[1] * 1j
    if tidal_mode:
        # Flip all vectors that are below the x-axis
        dt[dt.imag <= 0] *= -1
        # Now double the angle, so that angles near pi and 0 get averaged
        # together correctly:
        dt *= np.exp(1j * np.angle(dt))
        dt = np.ma.masked_invalid(dt)
        # Divide the angle by 2 to remove the doubling done on the previous
        # line.
        pang = np.angle(
            np.mean(dt, -1, dtype=np.complex128, keepdims=True)) / 2
        pang[pang < 0] += np.pi
    else:
        pang = np.angle(np.mean(dt, -1, keepdims=True))
    if len(pang) == 1:
        pang = pang[0]
    return pang
