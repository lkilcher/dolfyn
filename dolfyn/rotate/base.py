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
            p, r, h = nortek_orient2euler(odata['orientmat'])
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
            p, r, h = nortek_orient2euler(odata['orientmat'])
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


def nortek_euler2orient(pitch, roll, heading, units='degrees'):
    # THIS IS FOR NORTEK data ONLY!

    # Heading input is clockwise from North
    # Returns a rotation matrix that rotates earth (ENU) -> inst.
    # This is based on the Nortek `Transforms.m` file, available in
    # the refs folder.
    if units.lower() == 'degrees':
        pitch = np.deg2rad(pitch)
        roll = np.deg2rad(roll)
        heading = np.deg2rad(heading)
    # I've fixed the definition of heading to be consistent with
    # typical definitions.
    # This also involved swapping the sign on sh in the def of omat
    # below from the values provided in the Nortek Matlab script
    heading = (np.pi / 2 - heading)

    ch = np.cos(heading)
    sh = np.sin(heading)
    cp = np.cos(pitch)
    sp = np.sin(pitch)
    cr = np.cos(roll)
    sr = np.sin(roll)

    # Note that I've transposed these values (from what is defined in
    # Nortek matlab script), so that this is earth->inst (as
    # orientation matrices are typically defined)
    omat = np.empty((3, 3, len(sh)), dtype=np.float32)
    omat[0, 0, :] = ch * cp
    omat[1, 0, :] = -ch * sp * sr - sh * cr
    omat[2, 0, :] = -ch * cr * sp + sh * sr
    omat[0, 1, :] = sh * cp
    omat[1, 1, :] = -sh * sp * sr + ch * cr
    omat[2, 1, :] = -sh * cr * sp - ch * sr
    omat[0, 2, :] = sp
    omat[1, 2, :] = sr * cp
    omat[2, 2, :] = cp * cr

    return omat


def nortek_orient2euler(advo):
    """
    Calculate the euler angle orientations of Nortek data from the
    orientation matrix.

    Parameters
    ----------
    advo : :class:`ADVdata <base.ADVdata>`
      An adv object containing an `orientmat` attribute (array).

    Returns
    -------
    pitch : np.ndarray
      The pitch angle of the ADV (degrees).
    roll : np.ndarray
      The pitch angle of the ADV (degrees).
    heading : np.ndarray
      The heading angle of the ADV (degrees true).

    Notes
    -----

    Citation: Microstrain (April, 2012) "3DM-GX3-25 Single Byte Data
    Communications Protocol", (Rev 15).

    """
    if isinstance(advo, np.ndarray) and \
            advo.shape[:2] == (3, 3):
        omat = advo
    elif hasattr(advo['orient'], 'orientmat'):
        _check_declination(advo)
        omat = advo['orient'].orientmat
    # I'm pretty sure the 'yaw' is the angle from the east axis, so we
    # correct this for 'deg_true':
    return (np.rad2deg(np.arcsin(omat[0, 2])),
            np.rad2deg(np.arctan2(omat[1, 2], omat[2, 2])),
            np.rad2deg(np.arctan2(omat[0, 1], omat[0, 0]))
            )
