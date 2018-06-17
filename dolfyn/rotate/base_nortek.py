import numpy as np

sin = np.sin
cos = np.cos


def euler2orient(pitch, roll, heading, units='degrees'):
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

    ch = cos(heading)
    sh = sin(heading)
    cp = cos(pitch)
    sp = sin(pitch)
    cr = cos(roll)
    sr = sin(roll)

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


def orient2euler(advo):
    """
    Calculate the euler angle orientation of the ADV from the
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


def _check_declination(advo):
    odata = advo['orient']
    if 'declination' not in advo.props:
        if 'orientmat' in odata and \
           advo._make_model.startswith('nortek vector'):
            # Vector's don't have p,r,h when they have an orientmat.
            p, r, h = orient2euler(odata['orientmat'])
            odata['pitch'] = p
            odata['roll'] = r
            odata['heading'] = h
        # warnings.warn(
        #     'No declination in adv object.  Assuming a declination of 0.')
        return

    if 'orientmat' in odata and \
       not advo.props.get('declination_in_orientmat', False):
        # Declination is defined as positive if MagN is east of
        # TrueN. Therefore we must rotate about the z-axis by minus
        # the declination angle to get from Mag to True.
        cd = cos(-np.deg2rad(advo.props['declination']))
        sd = sin(-np.deg2rad(advo.props['declination']))
        # The ordering is funny here because orientmat is the
        # transpose of the inst->earth rotation matrix:
        Rdec = np.array([[cd, -sd, 0],
                         [sd, cd, 0],
                         [0, 0, 1]])
        odata['orientmat'] = np.einsum('ij,kjl->kil',
                                       Rdec,
                                       odata['orientmat'])

        advo.props['declination_in_orientmat'] = True
        p, r, h = orient2euler(odata['orientmat'])
        odata['pitch'] = p
        odata['roll'] = r
        odata['heading'] = h
        advo.props['declination_in_heading'] = True

    if 'heading' in odata and \
       not advo.props.get('declination_in_heading', False):
        odata['heading'] += advo.props['declination']
        odata['heading'][odata['heading'] < 0] += 360
        odata['heading'][odata['heading'] > 360] -= 360
        advo.props['declination_in_heading'] = True
