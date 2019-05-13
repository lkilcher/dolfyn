import numpy as np
from .vector import earth2principal, inst2earth as nortek_inst2earth
from .base import beam2inst


def inst2earth(adcpo, reverse=False,
               fixed_orientation=False, force=False):
    """Rotate velocities from the instrument to earth coordinates.

    This function also rotates data from the 'ship' frame, into the
    earth frame when it is in the ship frame (and
    ``adcpo.config['use_pitchroll'] == 'yes'``). It does not support the
    'reverse' rotation back into the ship frame.

    Parameters
    ----------
    adpo : The ADP object containing the data.

    reverse : bool (default: False)
           If True, this function performs the inverse rotation
           (earth->inst).
    fixed_orientation : bool (default: False)
        When true, take the average orientation and apply it over the
        whole record.
    force : bool (default: False)
        When true do not check which coordinate system the data is in
        prior to performing this rotation.

    Notes
    -----
    The rotation matrix is taken from the Teledyne RDI ADCP Coordinate
    Transformation manual January 2008

    When performing the forward rotation, this function sets the
    'inst2earth:fixed' flag to the value of `fixed_orientation`. When
    performing the reverse rotation, that value is 'popped' from the
    props dict and the input value to this function
    `fixed_orientation` has no effect. If `'inst2earth:fixed'` is not
    in the props dict than the input value *is* used.
    """
    if adcpo.props['inst_make'].lower() == 'nortek':
        # Handle nortek rotations with the nortek (adv) rotate fn.
        return nortek_inst2earth(adcpo, reverse=reverse, force=force)

    csin = adcpo.props['coord_sys'].lower()
    cs_allowed = ['inst', 'ship']
    if reverse:
        #cs_allowed = ['earth', 'enu']
        cs_allowed = ['earth']
    if not force and csin not in cs_allowed:
        raise ValueError("Invalid rotation for data in {}-frame "
                         "coordinate system.".format(csin))

    # rollaxis gives transpose of orientation matrix.
    # The 'rotation matrix' is the transpose of the 'orientation matrix'
    # NOTE the double 'rollaxis' within this function, and here, has
    # minimal computational impact because np.rollaxis returns a
    # view (not a new array)
    rotmat = np.rollaxis(adcpo['orient']['orientmat'], 1)

    sumstr = 'ijt,j...t->i...t'
    cs = 'earth'
    if reverse:
        cs = 'inst'
        fixed_orientation = adcpo.props.pop('inst2earth:fixed',
                                            fixed_orientation)
        sumstr = sumstr.replace('ij', 'ji')  # Transpose for reverse rotation
    else:
        adcpo.props['inst2earth:fixed'] = fixed_orientation
    if fixed_orientation:
        sumstr = sumstr.replace('t,', ',')
        rotmat = rotmat.mean(-1)

    # Only operate on the first 3-components, b/c the 4th is err_vel
    adcpo['vel'][:3] = np.einsum(sumstr, rotmat, adcpo['vel'][:3])

    if 'bt_vel' in adcpo:
        adcpo['bt_vel'][:3] = np.einsum(sumstr,
                                        rotmat, adcpo['bt_vel'][:3])
    adcpo.props['coord_sys'] = cs


def calc_orientmat(adcpo):

    # Calculate the orientation matrix using the raw 
    # heading, pitch, roll values from the RDI binary file.

    """
     Parameters
    ----------
    adcpo : The ADP object containing the data.
    
    ## RDI-ADCP-MANUAL (Jan 08, section 5.6 page 18)
    The internal tilt sensors do not measure exactly the same
    pitch as a set of gimbals would (the roll is the same). Only in
    the case of the internal pitch sensor being selected (EZxxx1xxx),
    the measured pitch is modified using the following algorithm.

        P = arctan[tan(Tilt1)*cos(Tilt2)]    (Equation 18)

    Where: Tilt1 is the measured pitch from the internal sensor, and
    Tilt2 is the measured roll from the internal sensor The raw pitch
    (Tilt 1) is recorded in the variable leader. P is set to 0 if the
    "use tilt" bit of the EX command is not set."""
    odat = adcpo.orient
    r = np.deg2rad(odat.roll)
    p = np.arctan(np.tan(np.deg2rad(odat.pitch)) * np.cos(r))
    h = np.deg2rad(odat.heading)
    if adcpo.props['inst_make'].lower() == 'rdi':
        if adcpo.config.orientation == 'up':
            """
            ## RDI-ADCP-MANUAL (Jan 08, section 5.6 page 18)
            Since the roll describes the ship axes rather than the
            instrument axes, in the case of upward-looking
            orientation, 180 degrees must be added to the measured
            roll before it is used to calculate M. This is equivalent
            to negating the first and third columns of M. R is set
            to 0 if the "use tilt" bit of the EX command is not set.
            """
            r += np.pi
        if (adcpo.props['coord_sys'] == 'ship' and
                adcpo.config['use_pitchroll'] == 'yes'):
            r[:] = 0
            p[:] = 0
    ch = np.cos(h)
    sh = np.sin(h)
    cr = np.cos(r)
    sr = np.sin(r)
    cp = np.cos(p)
    sp = np.sin(p)
    rotmat = np.empty((3, 3, len(r)))
    rotmat[0, 0, :] = ch * cr + sh * sp * sr
    rotmat[0, 1, :] = sh * cp
    rotmat[0, 2, :] = ch * sr - sh * sp * cr
    rotmat[1, 0, :] = -sh * cr + ch * sp * sr
    rotmat[1, 1, :] = ch * cp
    rotmat[1, 2, :] = -sh * sr - ch * sp * cr
    rotmat[2, 0, :] = -cp * sr
    rotmat[2, 1, :] = sp
    rotmat[2, 2, :] = cp * cr

    # The 'orientation matrix' is the transpose of the 'rotation matrix'.
    omat = np.rollaxis(rotmat, 1) 

    return omat
