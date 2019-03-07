import numpy as np
from . import base


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
        base._check_declination(advo)
        omat = advo['orient'].orientmat
    # I'm pretty sure the 'yaw' is the angle from the east axis, so we
    # correct this for 'deg_true':
    return (np.rad2deg(np.arcsin(omat[0, 2])),
            np.rad2deg(np.arctan2(omat[1, 2], omat[2, 2])),
            np.rad2deg(np.arctan2(omat[0, 1], omat[0, 0]))
            )
