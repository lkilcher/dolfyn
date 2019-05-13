import numpy as np
from numpy.linalg import det, inv


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
        val &= det(t[..., :idx, :idx]) > 0
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
    Calculate the orientation matrix from DOLfYN-defined euler angles.

    This function is not likely to be called during data processing since it requires
    DOLfYN-defined euler angles. It is intended for testing DOLfYN.

    The matrices H, P, R are the transpose of the matrices for rotation about z, y, x
    as shown here https://en.wikipedia.org/wiki/Rotation_matrix. The transpose is used
    because in DOLfYN the orientation matrix is organized for 
    rotation from EARTH --> INST, while the wiki's matrices are organized for 
    rotation from INST --> EARTH.

    Parameters
    ----------
    heading : np.ndarray (Nt)
      The heading angle.
    pitch : np.ndarray (Nt)
      The pitch angle.
    roll : np.ndarray (Nt)
      The roll angle.
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
         Note this requires matrix multiplication in the reverse order.

       - heading is defined as the direction the x-axis points, positive
         clockwise from North (this is *opposite* the right-hand-rule
         around the Z-axis), range 0-360 degrees.

       - pitch is positive when the x-axis pitches up (this is *opposite* the
         right-hand-rule around the Y-axis)

       - roll is positive according to the right-hand-rule around the
         instrument's x-axis

    """
    if units.lower() == 'degrees':
        pitch = np.deg2rad(pitch)
        roll = np.deg2rad(roll)
        heading = np.deg2rad(heading)
    elif units.lower() == 'radians':
        pass
    else:
        raise Exception("Invalid units")

    heading = np.pi / 2 - heading # Converts the DOLfYN-defined heading to one that follows the right-hand-rule; 
                                  # reports heading as rotation of the y-axis positive counterclockwise from North.

    pitch = -pitch # Converts the DOLfYN-defined pitch to one that follows the right-hand-rule.

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
        [[cp, zero, -sp],
         [zero, one, zero],
         [sp, zero, cp], ])
    R = np.array(
        [[one, zero, zero],
         [zero, cr, sr],
         [zero, -sr, cr], ])

    # As mentioned in the docs, the matrix-multiplication order is "reversed" (i.e., ZYX
    # order of rotations happens by multiplying R*P*H).
    # It helps to think of this as left-multiplying omat onto a vector. In which case,
    # H gets multiplied first, then P, then R (i.e., the ZYX rotation order).
    return np.einsum('ij...,jk...,kl...->il...', R, P, H)


def orient2euler(omat):
    """
    Calculate DOLfYN-defined euler angles from the orientation matrix.

    Parameters
    ----------
    advo : np.ndarray (or :class:`<~dolfyn.data.velocity.Velocity>`)
      The orientation matrix (or a data object containing one).

    Returns
    -------
    heading : np.ndarray
      The heading angle. Heading is defined as the direction the x-axis points,
      positive clockwise from North (this is *opposite* the right-hand-rule
      around the Z-axis), range 0-360 degrees.
    pitch : np.ndarray
      The pitch angle (degrees). Pitch is positive when the x-axis 
      pitches up (this is *opposite* the right-hand-rule around the Y-axis).
    roll : np.ndarray
      The roll angle (degrees). Roll is positive according to the 
      right-hand-rule around the instrument's x-axis.

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
        # heading 
        hh,
        # pitch 
        np.rad2deg(np.arcsin(omat[0, 2])),
        # roll
        np.rad2deg(np.arctan2(omat[1, 2], omat[2, 2])),
    )

def calc_principal_heading(vel, tidal_mode=True):
    """
    Compute the principal angle of the horizontal velocity.

    Parameters
    ----------
    vel : np.ndarray (2,...,Nt), or (3,...,Nt)
      The 2D or 3D velocity array (3rd-dim is ignored in this calculation)

    tidal_mode : bool (default: True)

    Returns
    -------
    p_heading : float or ndarray
      The principal heading(s) in degrees clockwise from North.

    Notes
    -----

    The tidal mode follows these steps:
      1. rotates vectors with negative v by 180 degrees
      2. then doubles those angles to make a complete circle again
      3. computes a mean direction from this, and halves that angle again.
      4. The returned angle is forced to be between 0 and 180. So, you
         may need to add 180 to this if you want your positive
         direction to be in the western-half of the plane.

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
            np.mean(dt, -1, dtype=np.complex128)) / 2
    else:
        pang = np.angle(np.mean(dt, -1))
    return (90 - np.rad2deg(pang))


def _calc_beam_rotmatrix(theta=20, convex=True, degrees=True):
    """Calculate the rotation matrix from beam coordinates to
    instrument head coordinates for an RDI ADCP.

    Parameters
    ----------
    theta : is the angle of the heads (usually 20 or 30 degrees)

    convex : is a flag for convex or concave head configuration.

    degrees : is a flag which specifies whether theta is in degrees
        or radians (default: degrees=True)
    """
    if degrees:
        theta = np.deg2rad(theta)
    if convex == 0 or convex == -1:
        c = -1
    else:
        c = 1
    a = 1 / (2. * np.sin(theta))
    b = 1 / (4. * np.cos(theta))
    d = a / (2. ** 0.5)
    return np.array([[c * a, -c * a, 0, 0],
                     [0, 0, -c * a, c * a],
                     [b, b, b, b],
                     [d, d, -d, -d]])


def beam2inst(dat, reverse=False, force=False):
    """Rotate velocities from beam to instrument coordinates.

    Parameters
    ----------
    dat : The ADP object containing the data.

    reverse : bool (default: False)
           If True, this function performs the inverse rotation
           (inst->beam).
    force : bool (default: False), or list
        When true do not check which coordinate system the data is in
        prior to performing this rotation. When forced-rotations are
        applied, the string '-forced!' is appended to the
        dat.props['coord_sys'] string. If force is a list, it contains
        a list of variables that should be rotated (rather than the
        default values in adpo.props['rotate_vars']).

    """
    if not force:
        if not reverse and dat.props['coord_sys'].lower() != 'beam':
            raise ValueError('The input must be in beam coordinates.')
        if reverse and dat.props['coord_sys'] != 'inst':
            raise ValueError('The input must be in inst coordinates.')

    if dat.props['inst_make'].lower() == 'rdi':
        try:
            rotmat = dat.config.rotmat
        except AttributeError:
            rotmat = _calc_beam_rotmatrix(
                dat.config.beam_angle,
                dat.config.beam_pattern == 'convex')
    elif dat.props['inst_make'].lower() == 'nortek' and \
         dat.props['inst_model'].lower().startswith('signature'):
        rotmat = dat.config['TransMatrix']
    elif dat.props['inst_make'].lower() == 'nortek':
        # Nortek Vector and AWAC
        rotmat = dat.config['head']['TransMatrix']
    else:
        raise Exception("Unrecognized device type.")

    if isinstance(force, (list, set, tuple)):
        # You can force a distinct set of variables to be rotated by
        # specifying it here.
        rotate_vars = force
    else:
        rotate_vars = {ky for ky in dat.props['rotate_vars']
                       if ky.startswith('vel')}

    cs = 'inst'
    if reverse:
        # Can't use transpose because rotation is not between
        # orthogonal coordinate systems
        rotmat = inv(rotmat)
        cs = 'beam'
    for ky in rotate_vars:
        dat[ky] = np.einsum('ij,j...->i...', rotmat, dat[ky])
    if force:
        dat.props['coord_sys'] += '-forced'
    else:
        dat.props['coord_sys'] = cs
