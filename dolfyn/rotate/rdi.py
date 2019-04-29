import numpy as np
from .vector import earth2principal, inst2earth as nortek_inst2earth


def calc_beam_rotmatrix(theta=20, convex=True, degrees=True):
    """Calculate the rotation matrix from beam coordinates to
    instrument head coordinates.

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


def beam2inst(adcpo, reverse=False, force=False):
    """Rotate velocitiesfrom beam to instrument coordinates.

    Parameters
    ----------
    adpo : The ADP object containing the data.

    reverse : bool (default: False)
           If True, this function performs the inverse rotation
           (inst->beam).
    force : bool (default: False)
        When true do not check which coordinate system the data is in
        prior to performing this rotation.
    """
    if not force:
        if not reverse and adcpo.props['coord_sys'].lower() != 'beam':
            raise ValueError('The input must be in beam coordinates.')
        if reverse and adcpo.props['coord_sys'] != 'inst':
            raise ValueError('The input must be in inst coordinates.')
    if hasattr(adcpo.config, 'rotmat'):
        rotmat = adcpo.config.rotmat
    elif 'TransMatrix' in adcpo.config:
        rotmat = adcpo.config['TransMatrix']
    elif 'head' in adcpo.config and 'TransMatrix' in adcpo.config['head']:
        # This is for AWACs.
        rotmat = adcpo.config['head']['TransMatrix']
    else:
        rotmat = calc_beam_rotmatrix(adcpo.config.beam_angle,
                                     adcpo.config.beam_pattern == 'convex')
    cs = 'inst'
    if reverse:
        # Can't use transpose because rotation is not between
        # orthogonal coordinate systems
        rotmat = np.linalg.inv(rotmat)
        cs = 'beam'
    adcpo['vel'] = np.einsum('ij,jkl->ikl', rotmat, adcpo['vel'])
    adcpo.props['coord_sys'] = cs


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


def calc_orientmat(adcpo, xducer_misalign = False):

    # Calculate the orientation matrix using the raw 
    # heading, pitch, roll values from the RDI binary file.

    """
     Parameters
    ----------
    -adcpo : The ADP object containing the data.

    -xducer_misalign : The rotation of the positive y-axis (beam 3 transducer)
                       from the foward keel of the boat/buoy. Include it
                       here if dat.config['xducer_misalign'] = 0 but 
                       an adjustment is necessary.
    
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

    # The organization of rotmat is the result H <dot> P <dot> R where
        # H  = ([ch sh 0], [-sh ch 0], [0 0 1])
        # P = ([1 0 0], [0 cp -sp], [0 sp cp])
        # R = ([cr 0 sr],  [0 1 0], [-sr 0 cr])
    # The H is like the wiki Rotation Matrix (and DOLfYN) rotation about z, the same as in rotate/base euler2orient.
    # The P is like the wiki Rotation Matrix (and DOLfYN) rotation about x, but DOLfYN calls that R in rotate/base euler2orient.
    # The R is like the wiki Rotation Maxtrix (and DOLfYN) rotation about y, but DOLfYN calls that P in rotate/base euler2orient.
    # Therefore, rotmat is already organized for EARTH --> INST.
    # The order of rotations that made rotmat is YXZ, where DOLfYN uses a rotation order of ZYX in rotate/base euler2orient.
    # RDI defines pitch and roll differently than DOLfYN.   
    # The 'orientation matrix' is the transpose of the 'rotation matrix' and will organized the matrix for INST --> EARTH.
    # omat = np.rollaxis(rotmat, 1) 

    # In order to produce an omat that would match if it were made in rotate/base euler2orient. rotmat will not agree 
    # because it was created with YXZ rotations, not ZYX rotations, and the pitch and roll matrices are assigned opposite 
    # of how they are in rotate/base euler2orient. Instead of using rotmat, adjust the RDI heading, pitch, roll so they 
    # can be used as inputs to rotate/base euler2orient and then execute rotate/base euler2orient to get omat.

    # When it is important to align the RDI heading with the StableMoor Buoy (e.g), adjust the heading for
    # the misalignment between the nose end of the keel of the buoy and the +y axis of the RDI (beam 3). 
    # If the dat.config['xducer_misalign'] != 0, then this was accounted for during instrument configuration and is built into
    # the raw heading.

    heading = h + xducer_misalign 
    heading = (np.pi / 2 - heading) # Defines heading as +CCW rotation of y-axis from North, following right-hand-rule.
    roll_rdi = r.copy()
    pitch_rdi = p.copy()
    pitch = roll_rdi
    roll = pitch_rdi

    omat = euler2orient(heading, pitch, roll, units='degrees')

    return omat
