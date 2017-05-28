from __future__ import division
import numpy as np
import warnings
from numpy.linalg import det, inv

deg2rad = np.pi / 180

sin = np.sin
cos = np.cos


def orient2euler(advo):
    """
    Calculate the euler angle orientation of the ADV from the
    orientation matrix.

    Parameters
    ----------
    advo : :class:`ADVraw <base.ADVraw>`
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
    if hasattr(advo, 'orientmat'):
        _check_declination(advo)
        omat = advo.orientmat
    elif isinstance(advo, np.ndarray) and \
            advo.shape[:2] == (3, 3):
        omat = advo
    # I'm pretty sure the 'yaw' is the angle from the east axis, so we
    # correct this for 'deg_true':
    return (np.arcsin(omat[0, 2]) / deg2rad,
            np.arctan2(omat[1, 2], omat[2, 2]) / deg2rad,
            np.arctan2(omat[0, 1], omat[0, 0]) / deg2rad
            )


def _cat4rot(tpl):
    tmp = []
    for vl in tpl:
        tmp.append(vl[None, :])
    return np.concatenate(tuple(tmp), axis=0)


def _beam2inst(dat, transmat, reverse=False):
    if reverse:
        transmat = inv(transmat)
    return np.einsum('ij,jk->ik', transmat, dat)


def _check_declination(advo):

    if 'declination' not in advo.props:
        if 'orientmat' in advo:
            p, r, h = orient2euler(advo['orientmat'])
            advo.add_data('pitch', p, 'orient')
            advo.add_data('roll', r, 'orient')
            advo.add_data('heading', h, 'orient')
        # warnings.warn(
        #     'No declination in adv object.  Assuming a declination of 0.')
        return

    if 'orientmat' in advo and \
       not advo.props.get('declination_in_orientmat', False):
        # Declination is defined as positive if MagN is east of
        # TrueN. Therefore we must rotate about the z-axis by minus
        # the declination angle to get from Mag to True.
        cd = cos(-advo.props['declination'] * deg2rad)
        sd = sin(-advo.props['declination'] * deg2rad)
        # The ordering is funny here because orientmat is the
        # transpose of the inst->earth rotation matrix:
        Rdec = np.array([[cd, -sd, 0],
                         [sd, cd, 0],
                         [0, 0, 1]])
        advo['orientmat'] = np.einsum('ij,kjl->kil',
                                      Rdec,
                                      advo['orientmat'])

        advo.props['declination_in_orientmat'] = True
        p, r, h = orient2euler(advo['orientmat'])
        advo.add_data('pitch', p, 'orient')
        advo.add_data('roll', r, 'orient')
        advo.add_data('heading', h, 'orient')
        advo.props['declination_in_heading'] = True

    if 'heading' in advo and \
       not advo.props.get('declination_in_heading', False):
        advo['heading'] += advo.props['declination']
        advo['heading'][advo['heading'] < 0] += 360
        advo['heading'][advo['heading'] > 360] -= 360
        advo.props['declination_in_heading'] = True


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
        sumstr = 'jik,jk->ik'
        cs_now = 'earth'
        cs_new = 'inst'
    else:
        sumstr = 'ijk,jk->ik'
        cs_now = 'inst'
        cs_new = 'earth'

    if rotate_vars is None:
        rotate_vars = advo.props['rotate_vars']

    if not force:
        if advo.props['coord_sys'] == cs_new:
            print("Data is already in the '%s' coordinate system" % cs_new)
            return
        elif not advo.props['coord_sys'] == cs_now:
            print("Data must be in the '%s' frame prior to using this function" %
                   cs_now)

    _check_declination(advo)

    if hasattr(advo, 'orientmat'):
        # Take the transpose of the orientation to get the inst->earth rotation
        # matrix.
        rmat = np.rollaxis(advo['orientmat'], 1)

    else:
        rr = advo.roll * deg2rad
        pp = advo.pitch * deg2rad
        hh = (advo.heading - 90) * deg2rad
        if np.isnan(rr[-1]) and np.isnan(pp[-1]) and np.isnan(hh[-1]):
            # The end of the data may not have valid orientations
            lastgd = np.nonzero(~np.isnan(rr + pp + hh))[0][-1]
            rr[lastgd:] = rr[lastgd]
            pp[lastgd:] = pp[lastgd]
            hh[lastgd:] = hh[lastgd]
        # NOTE: For Nortek Vector ADVs: 'down' configuration means the
        #       head was pointing UP!  Check the Nortek coordinate
        #       transform matlab script for more info.  The 'up'
        #       orientation corresponds to the communication cable
        #       being up.  This is ridiculous, but apparently a
        #       reality.
        rr[advo.orientation_down] += np.pi

        ch = cos(hh)
        sh = sin(hh)
        cp = cos(pp)
        sp = sin(pp)
        cr = cos(rr)
        sr = sin(rr)

        rmat = np.empty((3, 3, len(sh)), dtype=np.float32)
        rmat[0, 0, :] = ch * cp
        rmat[0, 1, :] = -ch * sp * sr + sh * cr
        rmat[0, 2, :] = -ch * cr * sp - sh * sr
        rmat[1, 0, :] = -sh * cp
        rmat[1, 1, :] = sh * sp * sr + ch * cr
        rmat[1, 2, :] = sh * cr * sp - ch * sr
        rmat[2, 0, :] = sp
        rmat[2, 1, :] = sr * cp
        rmat[2, 2, :] = cp * cr
        # H = np.array([[ch,  sh, 0],
        # [-sh, ch, 0],
        # [0,    0, 1]], dtype=np.float32)
        # P = np.array([[cp, -sp * sr, -cr * sp],
        # [0,        cr,      -sr],
        # [sp,  sr * cp,  cp * cr]], dtype=np.float32)
        # rmat = np.einsum('ijl,jkl->ikl', H, P)

    if not _check_rotmat_det(rmat):
        raise ValueError("Invalid orientation matrix"
                         " (determinant != 1).")

    for nm in rotate_vars:
        advo[nm] = np.einsum(sumstr, rmat, advo[nm])

    advo.props['coord_sys'] = cs_new

    return


def _inst2earth(advo, use_mean_rotation=False):
    """
    Rotate the data from the instrument frame to the earth frame.

    The rotation matrix is computed from heading, pitch, and roll.
    Taken from a "Coordinate transformation" script on the nortek
    site.

    --References--
    http://www.nortek-as.com/en/knowledge-center/forum/software/644656788
    http://www.nortek-as.com/en/knowledge-center/forum/software/644656788/resolveuid/af5dec86a5df8e7fd82a2f2aed1bc537
    """
    _check_declination(advo)
    rr = advo.roll * deg2rad
    pp = advo.pitch * deg2rad
    hh = (advo.heading - 90) * deg2rad
    if use_mean_rotation:
        rr = np.nanmean(np.angle(np.exp(1j * rr)))
        pp = np.nanmean(np.angle(np.exp(1j * pp)))
        hh = np.nanmean(np.angle(np.exp(1j * hh)))
    if 'heading_offset' in advo.props:
        # Offset is in CCW degrees that the case was offset relative
        # to the head.
        hh += advo.props['heading_offset'] * deg2rad
    if advo.config.orientation == 'down':
        # NOTE: For ADVs: 'down' configuration means the head was
        #       pointing UP!  check the Nortek coordinate transform
        #       matlab script for more info.  The 'up' orientation
        #       corresponds to the communication cable begin up.  This
        #       is ridiculous, but apparently a reality.
        rr += np.pi
        # I did some of the math, and this is the same as multiplying
        # rows 2 and 3 of the T matrix by -1 (in the ADV coordinate
        # transform script), and also the same as multiplying columns
        # 2 and 3 of the heading matrix by -1.  Anyway, I did it this
        # way to be consistent with the ADCP rotation script, which
        # looks similar.
        #
        # The way it is written in the adv CT script is annoying:
        #    T and T_org, and minusing rows 2+3 of T, which only goes
        #    into R, but using T_org elsewhere.
    ## if advo.config.coordinate_system == 'XYZ' and not hasattr(advo, 'u_inst'):
    ##     advo.add_data('u_inst', advo.u, 'inst')
    ##     advo.add_data('v_inst', advo.v, 'inst')
    ##     advo.add_data('w_inst', advo.w, 'inst')
    # This is directly from the matlab script:
    # H=np.zeros(shp)
    # H[0,0]=cos(hh);  H[0,1]=sin(hh);
    # H[1,0]=-sin(hh); H[1,1]=cos(hh);
    # H[2,2]=1
    # P=np.zeros(shp)
    # P[0,0]=cos(pp);  P[0,1]=-sin(pp)*sin(rr); P[0,2]=-cos(rr)*sin(pp)
    # P[1,0]=0;        P[1,1]=cos(rr);          P[1,2]=-sin(rr)
    # P[2,0]=sin(pp);  P[2,1]=sin(rr)*cos(pp);  P[2,2]=cos(pp)*cos(rr)
    #
    # This is me redoing the math:
    ch = cos(hh)
    sh = sin(hh)
    cp = cos(pp)
    sp = sin(pp)
    cr = cos(rr)
    sr = sin(rr)
    # rotmat=ch*cp,-ch*sp*sr+sh*cr,-ch*cr*sp-sh*sr;
    # -sh*cp,sh*sp*sr+ch*cr,sh*cr*sp-ch*sr;
    # sp,sr*cp,cp*cr
    # umat=np.empty((3,len(advo.u_inst)),dtype='single')
    # umat=np.tensordot(rotmat,cat4rot((advo.u_inst,
    # advo.v_inst,advo.w_inst)),axes=(1,0)).astype('single')
    # This is me actually doing the rotation:
    # R=np.dot(H,P)
    # u=
    utmp = advo['vel'].copy()
    advo['vel'][0] = ((ch * cp) * utmp[0] +
                      (-ch * sp * sr + sh * cr) * utmp[1] +
                      (-ch * cr * sp - sh * sr) * utmp[2]).astype('single')
    advo['vel'][1] = ((-sh * cp) * utmp[0] +
                      (sh * sp * sr + ch * cr) * utmp[1] +
                      (sh * cr * sp - ch * sr) * utmp[2]).astype('single')
    advo['vel'][2] = ((sp) * utmp[0] +
                      (sr * cp) * utmp[1] +
                      cp * cr * utmp[2]).astype('single')
    advo.props['coord_sys'] = 'earth'


def _check_rotmat_det(rotmat):
    if rotmat.ndim > 2:
        rotmat = np.transpose(rotmat)
    return np.all(np.abs(det(rotmat) - 1) < 1e-3)


def _rotate_vel2body(advo):
    if 'vel_rotated2body' in advo.props and \
       advo.props['vel_rotated2body'] == True:
        # Don't re-rotate the data if its already been rotated.
        return
    if not _check_rotmat_det(advo.props['body2head_rotmat']):
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

    if reverse:
        ang = advo.principal_angle
        cs_now = 'principal'
        cs_new = 'earth'
    else:
        ang = -advo.principal_angle
        cs_now = 'earth'
        cs_new = 'principal'
    if advo.props['coord_sys'] == cs_new:
        print('Data is already in the %s coordinate system' % cs_new)
        return
    elif not advo.props['coord_sys'] == cs_now:
        raise Exception('Data must be in the {} frame prior '
                        'to using this function'.format(cs_now))

    # Calculate the rotation matrix:
    cp, sp = cos(ang), sin(ang)
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
