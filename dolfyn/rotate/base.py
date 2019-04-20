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


def _check_declination(advo):
    if advo.props.get('__checking_declination__', False):
        # Don't go into an infinite loop.
        return
    odata = advo['orient']
    cs = advo.props['coord_sys']
    if 'declination' not in advo.props:
        if 'orientmat' in odata and \
           advo._make_model.startswith('nortek vector'):
            # Vector's don't have p,r,h when they have an orientmat.
            h, p, r = orient2euler(odata['orientmat'])
            odata['pitch'] = p
            odata['roll'] = r
            odata['heading'] = h
        # warnings.warn(
        #     'No declination in adv object.  Assuming a declination of 0.')
        return

    rotation_done_flag = False

    # This flag avoids an infinitie recursion loop
    advo.props['__checking_declination__'] = True

    if 'orientmat' in odata and \
       not advo.props.get('declination_in_orientmat', False):
        if cs == 'earth':
            # Rotate to instrument coordinate-system before adjusting
            # for declination.
            advo.rotate2('inst', inplace=True)

        # Declination is defined as positive if MagN is east of
        # TrueN. Therefore we must rotate about the z-axis by minus
        # the declination angle to get from Mag to True.
        cd = np.cos(-np.deg2rad(advo.props['declination']))
        sd = np.sin(-np.deg2rad(advo.props['declination']))
        # The ordering is funny here because orientmat is the
        # transpose of the inst->earth rotation matrix:
        Rdec = np.array([[cd, -sd, 0],
                         [sd, cd, 0],
                         [0, 0, 1]])
        odata['orientmat'] = np.einsum('ij,kjl->kil',
                                       Rdec,
                                       odata['orientmat'])
        # NOTE: for a moment I thought I needed to do a tensor
        # rotation on orientmat, but that's not the case. It seems
        # like the rotation matrix isn't actually a "tensor".
        # I checked this by showing that the above actually gives the
        # desired result of rotating vectors by the declination.

        advo.props['declination_in_orientmat'] = True
        if advo._make_model.startswith('nortek vector'):
            h, p, r = orient2euler(odata['orientmat'])
            odata['pitch'] = p
            odata['roll'] = r
            odata['heading'] = h
            advo.props['declination_in_heading'] = True

        if cs == 'earth':
            # Now rotate back to the earth coordinate-system with the
            # declination included in the data
            advo.rotate2('earth', inplace=True)
            rotation_done_flag = True

    if 'heading' in odata and \
       not advo.props.get('declination_in_heading', False):

        if cs == 'earth' and not rotation_done_flag:
            # Rotate to instrument coordinate-system before adjusting
            # for declination.
            advo.rotate2('inst', inplace=True)

        odata['heading'] += advo.props['declination']
        odata['heading'] %= 360
        advo.props['declination_in_heading'] = True

        if cs == 'earth' and not rotation_done_flag:
            # Now rotate back to the earth coordinate-system with the
            # declination included.
            advo.rotate2('earth', inplace=True)
    advo.props.pop('__checking_declination__')


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
        _check_declination(omat)
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
