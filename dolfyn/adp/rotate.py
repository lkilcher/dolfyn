import numpy as np
from ..adv.rotate import earth2principal

deg2rad = np.pi / 180.


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
        theta = theta * deg2rad
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


def _cat4rot(tpl):
    tmp = []
    for vl in tpl:
        tmp.append(vl[:, None, :])
    return np.concatenate(tuple(tmp), axis=1)


def beam2inst(adcpo,):
    """Rotate velocities from beam to instrument coordinates.
    """
    if hasattr(adcpo.config, 'rotmat'):
        rotmat = adcpo.config.rotmat
    else:
        rotmat = calc_beam_rotmatrix(adcpo.config.beam_angle,
                                     adcpo.config.beam_pattern == 'convex')
    adcpo.add_data('u_inst',
                   (adcpo.beam1vel * rotmat[0, 0] +
                    adcpo.beam2vel * rotmat[0, 1] +
                    adcpo.beam3vel * rotmat[0, 2] +
                    adcpo.beam4vel * rotmat[0, 3]
                    ).astype('float32'),
                   'inst'
                   )
    adcpo.add_data('v_inst',
                   (adcpo.beam1vel * rotmat[1, 0] +
                    adcpo.beam2vel * rotmat[1, 1] +
                    adcpo.beam3vel * rotmat[1, 2] +
                    adcpo.beam4vel * rotmat[1, 3]
                    ).astype('float32'),
                   'inst'
                   )
    adcpo.add_data('w_inst',
                   (adcpo.beam1vel * rotmat[2, 0] +
                    adcpo.beam2vel * rotmat[2, 1] +
                    adcpo.beam3vel * rotmat[2, 2] +
                    adcpo.beam4vel * rotmat[2, 3]
                    ).astype('float32'),
                   'inst'
                   )
    adcpo.add_data('err_vel',
                   (adcpo.beam1vel * rotmat[3, 0] +
                    adcpo.beam2vel * rotmat[3, 1] +
                    adcpo.beam3vel * rotmat[3, 2] +
                    adcpo.beam4vel * rotmat[3, 3]
                    ).astype('float32'),
                   'main'
                   )


def inst2earth(adcpo, fixed_orientation=False):
    """Rotate velocities from the instrument to the earth frame.

    The rotation matrix is taken from the Teledyne RDI
    ADCP Coordinate Transformation manual January 2008
    """
    r = adcpo.roll_deg * deg2rad
    p = np.arctan(np.tan(adcpo.pitch_deg * deg2rad) * np.cos(r))
    h = adcpo.heading_deg * deg2rad
    if 'heading_offset' in adcpo.props.keys():
        h += adcpo.props['heading_offset'] * deg2rad
    if 'declination' in adcpo.props.keys():
        h += adcpo.props['declination'] * deg2rad
    if adcpo.config.orientation == 'up':
        r += np.pi
    ch = np.cos(h)
    sh = np.sin(h)
    cr = np.cos(r)
    sr = np.sin(r)
    cp = np.cos(p)
    sp = np.sin(p)
    # rotmat = np.empty((3, 3, len(r)))
    # rotmat[0, 0,:] = ch * cr + sh * sp * sr
    # rotmat[0, 1,:] = sh * cp
    # rotmat[0, 2,:] = ch * sr - sh * sp * cr
    # rotmat[1, 0,:] = -sh * cr + ch * sp * sr
    # rotmat[1, 1,:] = ch * cp
    # rotmat[1, 2,:] = -sh * sr - ch * sp * cr
    # rotmat[2, 0,:] = -cp * sr
    # rotmat[2, 1,:] = sp
    # rotmat[2, 2,:] = cp * cr
    # adcpo.add_data('u',
    # (rotmat[0, 0] * adcpo.u_inst +
    # rotmat[0, 1] * adcpo.v_inst +
    # rotmat[0, 2] * adcpo.w_inst
    # ).astype('float32'), 'main')
    # adcpo.add_data('v',
    # (rotmat[1, 0] * adcpo.u_inst +
    # rotmat[1, 1] * adcpo.v_inst +
    # rotmat[1, 2] * adcpo.w_inst
    # ).astype('float32'), 'main')
    # adcpo.add_data('w',
    # (rotmat[2, 0] * adcpo.u_inst +
    # rotmat[2, 1] * adcpo.v_inst +
    # rotmat[2, 2] * adcpo.w_inst
    # ).astype('float32'), 'main')
    adcpo.add_data('u',
                   ((ch * cr + sh * sp * sr) * adcpo.u_inst +
                    sh * cp * adcpo.v_inst +
                    (ch * sr - sh * sp * cr) * adcpo.w_inst
                    ).astype('float32'),
                   'main'
                   )
    adcpo.add_data('v',
                   ((-sh * cr + ch * sp * sr) * adcpo.u_inst +
                    (ch * cp) * adcpo.v_inst +
                    (-sh * sr - ch * sp * cr) * adcpo.w_inst
                    ).astype('float32'),
                   'main'
                   )
    adcpo.add_data('w',
                   (-cp * sr * adcpo.u_inst +
                    sp * adcpo.v_inst
                    + cp * cr * adcpo.w_inst
                    ).astype('float32'),
                   'main'
                   )
    adcpo.props['coord_sys'] = 'earth'


def inst2earth_heading(adpo):
    h = adpo.heading_deg[:] * deg2rad
    if 'heading_offset' in adpo.props.keys():
        h += adpo.props['heading_offset'] * deg2rad
    if 'declination' in adpo.props.keys():
        h += adpo.props['declination'] * deg2rad
    return np.exp(-1j * h)
