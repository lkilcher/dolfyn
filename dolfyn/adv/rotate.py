import numpy as np
import warnings
import scipy.signal as sig
from scipy.integrate import cumtrapz

sin = np.sin
cos = np.cos


def _calcAccelVel(accel, samp_freq, filt_freq):
    """
    Calculate the translational velocity from the an acceleration
    signal.

    Parameters
    ----------
    accel : |np.ndarray| (3, n_time)
      The linear acceleration array.

    samp_freq : float
      The sample rate of the acceleration signal. (Hz)

    filt_freq : float
      The filter frequency to use (Hz).

    Returns
    -------
    uacc : |np.ndarray| (3, n_time)
      The translational-induced velocity array.

    """
    # 8th order butterworth filter.
    # print float(filt_freq)/(samp_freq/2)
    filt = sig.butter(2, float(filt_freq) / (samp_freq / 2))
    # hp=np.empty_like(accel)
    # for idx in range(accel.shape[0]):
    #    hp[idx]=accel[idx]-sig.filtfilt(filt[0],filt[1],accel[idx])
    hp = accel
    shp = list(accel.shape[:-1])
    shp += [1]
    dat = np.concatenate((np.zeros(shp),
                          cumtrapz(hp, dx=1. / samp_freq)), axis=-1)
    for idx in range(accel.shape[0]):
        dat[idx] = dat[idx] - sig.filtfilt(filt[0], filt[1], dat[idx])
    # NOTE: The minus sign is because the measured induced velocities
    #       are in the opposite direction of the head motion.
    #       i.e. when the head moves one way in stationary flow, it
    #       measures a velocity in the other direction.
    return -dat


def _calcRotationVel(AngRt, vec_imu2sample, transMat=None):
    """
    Calculate the induced velocity due to rotations of the instrument
    about the IMU center.

    Parameters
    ----------
    AngRt : |np.ndarray|
      The angular rate array (3, n_time).
    vec_imu2sample : |np.ndarray|
      The vector from the IMU to the sample (3).
    transMat : |np.ndarray|
      The transformation matrix from beam to head (XYZ) velocities.

    Returns
    -------
    urot : |np.ndarray|
      The rotation-induced velocity array (3, n_time).

    """
    # This motion of the head due to rotations should be the
    # cross-product of omega (rotation vector) and the vector from the
    # IMU to the ADV sample volume.
    #   u=dz*omegaY-dy*omegaZ,v=dx*omegaZ-dz*omegaX,w=dy*omegaX-dx*omegaY

    # where vec_imu2sample=[dx,dy,dz], and AngRt=[omegaX,omegaY,omegaZ]

    # NOTE: The minus sign is because the measured-induced velocities
    #       are in the opposite direction of the head motion.
    #       i.e. when the head moves one way in stationary flow, it
    #       measures a velocity in the opposite direction.
    if vec_imu2sample.ndim == 1:
        vec_imu2sample = vec_imu2sample.copy().reshape((3, 1))

    urot = -np.array([(vec_imu2sample[2][:, None] * AngRt[1] -
                       vec_imu2sample[1][:, None] * AngRt[2]),
                      (vec_imu2sample[0][:, None] * AngRt[2] -
                       vec_imu2sample[2][:, None] * AngRt[0]),
                      (vec_imu2sample[1][:, None] * AngRt[0] -
                       vec_imu2sample[0][:, None] * AngRt[1]),
                      ])

    if urot.shape[:2] == (3, 3) and transMat is not None:
        # The columns of vec_imu2sample are the positions of *each*
        # probe, so we can calculate the velocity of each probe
        # separately and recompute the 'error' velocity.
        return np.einsum('ij,kj->ik',
                         transMat,
                         np.diagonal(np.einsum('ij,jkl->ikl',
                                               np.linalg.inv(transMat),
                                               urot)
                                     ))
        # np.diagonal returns a matrix with colums that contain
        # diagonal elements (thus the ij,kj->ik in einsum).
    else:
        # Here we drop a dimension because we added one with the
        # 'None's above.
        return urot[:, 0, :]

# class rotate_msadv(object):
# order = ['beam', 'head', 'inst', 'earth', 'pax']
# def rot_beam (self,obj,inv=False):
# def rotate(self,obj,to_frame='earth'):


class CorrectMotion(object):

    """
    This object performs motion correction on an IMU-ADV data
    object. The IMU and ADV data should be tightly synchronized and
    contained in a single data object.

    Parameters
    ----------

    accel_filtfreq : float
      the frequency at which to high-pass filter the acceleration
      signal to remove low-frequency drift.

    vel_filtfreq : float (optional)
      a second frequency to high-pass filter the integrated
      acceleration.  (default: 1/3 of accel_filtfreq)

    separate_probes : bool (optional: False)
      a flag to perform motion-correction at the probe tips, and
      perform motion correction in beam-coordinates, then transform
      back into XYZ/earth coordinates. This correction seems to be
      lower than the noise levels of the ADV, so the defualt is to not
      use it (False).

    Notes
    -----

    Acceleration signals from inertial sensors are notorious for
    having a small bias that can drift slowly in time. When
    integrating these signals to estimate velocity the bias is
    amplified and leads to large errors in the estimated
    velocity. There are two methods for removing these errors,

    1) high-pass filter the acceleration signal prior and/or after
       integrating. This implicitly assumes that the low-frequency
       translational velocity is zero.
    2) provide a slowly-varying reference position (often from a GPS)
       to an IMU that can use the signal (usually using Kalman
       filters) to debias the acceleration signal.

    Because method (1) removes `real` low-frequency acceleration,
    method (2) is more accurate. However, providing reference position
    estimates to undersea instruments is practically challenging and
    expensive. Therefore, lacking the ability to use method (2), this
    function utilizes method (1).

    For deployments in which the ADV is mounted on a mooring, or other
    semi-fixed structure, the assumption of zero low-frequency
    translational velocity is a reasonable one. However, for
    deployments on ships, gliders, or other moving objects it is
    not. The measured velocity, after motion-correction, will still
    hold some of this contamination and will be a sum of the ADV
    motion and the measured velocity on long time scales.  If
    low-frequency motion is known separate from the ADV (e.g. from a
    bottom-tracking ADP, or from a ship's GPS), it may be possible to
    remove that signal from the ADV signal in post-processing. The
    accuracy of this approach has not, to my knowledge, been tested
    yet.

    Examples
    --------

    >>> from dolfyn.adv import api as avm
    >>> dat = avm.read_nortek('my_data_file.vec')
    >>> mc = avm.CorrectMotion(0.1)
    >>> corrected_data = mc(dat)

    """

    def __init__(self, accel_filtfreq=1. / 30,
                 vel_filtfreq=None, separate_probes=False):
        self.accel_filtfreq = accel_filtfreq
        if vel_filtfreq is None:
            vel_filtfreq = accel_filtfreq / 3
        self.accelvel_filtfreq = vel_filtfreq
        self.separate_probes = separate_probes

    def _rotateVel2body(self, advo):
        # The transpose should do head to body.
        advo._u = np.dot(advo.props['body2head_rotmat'].T, advo._u)

    def _calcRotVel(self, advo):
        pos = self._calcProbePos(advo)
        rmat = advo.props['body2head_rotmat']
        if self.separate_probes:
            advo.urot = np.dot(
                rmat.T,
                _calcRotationVel(np.dot(rmat, advo.AngRt),
                                 np.dot(rmat, pos),
                                 advo.config.head.get('TransMatrix', None)))
        else:
            advo.urot = _calcRotationVel(advo.AngRt, pos)
        advo.groups['orient'].add('urot')

    def _calcAccelStable(self, advo):
        # Ordering does inst->earth:
        acctmp = np.einsum('ijk,ik->jk', advo.orientmat, advo.Accel)
        flt = sig.butter(1, self.accel_filtfreq / (advo.fs / 2))
        for idx in range(3):
            acctmp[idx] = sig.filtfilt(flt[0], flt[1], acctmp[idx])
        # Ordering does earth-inst:
        advo.AccelStable = np.einsum('ijk,jk->ik', advo.orientmat, acctmp)
        advo.groups['orient'].add('AccelStable')

    def _calcProbePos(self, advo):
        """
        !!!Currently this only works for Nortek Vectors!

        In the future, we could use the transformation matrix (and a
        probe-length lookup-table?)
        """
        # This is the body->imu vector (in body frame)
        # In inches it is: (0.25, 0.25, 5.9)
        nortek_body2imu = np.array([0.00635, 0.00635, 0.14986])
        # According to the ADV_DataSheet, the probe-length radius is
        # 8.6cm @ 120deg from probe-stem axis.  If I subtract 1cm
        # (!!!checkthis) to get acoustic receiver center, this is
        # 7.6cm.  In the coordinate sys of the center of the probe
        # then, the positions of the centers of the receivers is:
        if advo.props.get('inst_make', None) == 'Nortek' and \
           advo.props.get('inst_model', None) == 'VECTOR' and \
           self.separate_probes:
            r = 0.076
            phi = -30. * np.pi / \
                180.  # The angle between the x-y plane and the probes
            theta = np.array([0., 120., 240.]) * np.pi / \
                180.  # The angles of the probes from the x-axis.
            return np.dot(advo.props['body2head_rotmat'].T,
                          np.array([r * np.cos(theta),
                                    r * np.sin(theta),
                                    r * np.tan(phi) * np.ones(3)])) + \
                advo.props['body2head_vec'][:, None] - nortek_body2imu
        else:
            # The nortek_body2imu vector is subtracted because of
            # vector addition:
            # body2head = body2imu + imu2head
            # Thus:
            # imu2head = body2head - body2imu
            return advo.props['body2head_vec'] - nortek_body2imu

    def _calcAccelVel(self, advo):
        advo.uacc = _calcAccelVel(
            advo.Accel - advo.AccelStable, advo.fs, self.accelvel_filtfreq)
        advo.groups['orient'].add('uacc')

    def __call__(self, advo):
        """
        Perform motion correction on an IMU-equipped ADV object.

        Parameters
        ----------
        advo : :class:`ADVraw <base.ADVraw>`
          The adv object on which to perform motion correction.
          It must contain the following data attributes:

          - _u : The velocity array.
          - Accel : The translational acceleration array.
          - AngRt : The rotation-rate array.
          - orientmat : The orientation matrix.

        Notes
        -----

        This method does not return a data object, it operates on
        (motion corrects) the input `advo`.

        """
        if 'rotate_vars' not in advo.props.keys():
            advo.props['rotate_vars'] = {'_u', 'urot', 'uacc',
                                         'Accel', 'AccelStable',
                                         'AngRt', 'Mag'}
        else:
            advo.props['rotate_vars'].update({'urot', 'uacc', 'AccelStable'})
        self._rotateVel2body(advo)
        self._calcRotVel(advo)
        self._calcAccelStable(advo)
        self._calcAccelVel(advo)
        advo._u -= (advo.urot + advo.uacc)


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
        omat = advo.orientmat
    elif np.ndarray in advo.__class__.__mro__ and \
            advo.shape[:2] == (3, 3):
        omat = advo
    # I'm pretty sure the 'yaw' is the angle from the east axis, so we
    # correct this for 'deg_true':
    return (180 / np.pi * np.arcsin(omat[0, 2]),
            180 / np.pi * np.arctan2(omat[1, 2], omat[2, 2]),
            180 / np.pi * np.arctan2(omat[0, 1], omat[0, 0])
            )


def _cat4rot(tpl):
    tmp = []
    for vl in tpl:
        tmp.append(vl[None, :])
    return np.concatenate(tuple(tmp), axis=0)


def inst2earth(advo, reverse=False):
    """
    Rotate data in an ADV object to the earth from the isntrument
    frame (or vice-versa). If the

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
        # The transpose of the rotation matrix gives the inverse
        # rotation, so we simply reverse the order of the einsum:
        sumstr = 'jik,jk->ik'
        cs_now = 'earth'
        cs_new = 'inst'
    else:
        sumstr = 'ijk,jk->ik'
        cs_now = 'inst'
        cs_new = 'earth'

    if advo.props['coord_sys'] == cs_new:
        print("Data is already in the '%s' coordinate system" % cs_new)
        return
    elif not advo.props['coord_sys'] == cs_now:
        print("Data must be in the '%s' frame prior to using this function" %
              cs_now)

    if hasattr(advo, 'orientmat'):
        if 'declination' in advo.props and not \
                advo.props.get('declination_in_orientmat', False):
            # Declination is defined as positive if MagN is east of
            # TrueN. Therefore we must rotate about the z-axis by minus
            # the declination angle to get from Mag to True.
            cd, sd = cos(-advo.props['declination'] * np.pi / 180), sin(
                -advo.props['declination'] * np.pi / 180)
            # The ordering is funny here because orientmat is the
            # transpose of the inst->earth rotation matrix:
            advo['orientmat'][:2, :2] = np.einsum(
                'ij,kjl->ikl',
                np.array([[cd, -sd], [sd, cd]]),
                advo['orientmat'][:2, :2])

            advo.props['declination_in_orientmat'] = True

        # Take the transpose of the orientation to get the inst->earth rotation
        # matrix.
        rmat = np.rollaxis(advo['orientmat'], 1)

    else:
        rr = advo.roll * np.pi / 180
        pp = advo.pitch * np.pi / 180
        hh = (advo.heading - 90) * np.pi / 180
        # NOTE: For Nortek Vector ADVs: 'down' configuration means the
        #       head was pointing UP!  Check the Nortek coordinate
        #       transform matlab script for more info.  The 'up'
        #       orientation corresponds to the communication cable
        #       being up.  This is ridiculous, but apparently a
        #       reality.
        rr[advo.orientation_down] += np.pi
        if 'declination' in advo.props.keys():
            hh += (advo.props['declination'] * np.pi / 180)
                   # Declination is in degrees East, so we add this to True
                   # heading.

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

    for nm in advo.props['rotate_vars']:
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
    rr = advo.roll * np.pi / 180
    pp = advo.pitch * np.pi / 180
    hh = (advo.heading - 90) * np.pi / 180
    if use_mean_rotation:
        rr = np.angle(np.exp(1j * rr).mean())
        pp = np.angle(np.exp(1j * pp).mean())
        hh = np.angle(np.exp(1j * hh).mean())
    if 'declination' in advo.props.keys():
        hh += (advo.props['declination'] * np.pi / 180)
        # Declination is in degrees East, so we add this to True
        # heading.
    else:
        warnings.warn(
            'No declination in adv object.  Assuming a declination of 0.')
    if 'heading_offset' in advo.props.keys():
        # Offset is in CCW degrees that the case was offset relative
        # to the head.
        hh += advo.props['heading_offset'] * np.pi / 180
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
    if advo.config.coordinate_system == 'XYZ' and not hasattr(advo, 'u_inst'):
        advo.add_data('u_inst', advo.u, 'inst')
        advo.add_data('v_inst', advo.v, 'inst')
        advo.add_data('w_inst', advo.w, 'inst')
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
    u = ((ch * cp) * advo.u_inst + (-ch * sp * sr + sh * cr) * advo.v_inst +
         (-ch * cr * sp - sh * sr) * advo.w_inst).astype('single')
    v = ((-sh * cp) * advo.u_inst + (sh * sp * sr + ch * cr) * advo.v_inst +
         (sh * cr * sp - ch * sr) * advo.w_inst).astype('single')
    w = ((sp) * advo.u_inst + (sr * cp) * advo.v_inst +
         cp * cr * advo.w_inst).astype('single')
    advo.add_data('u', u, 'main')
    advo.add_data('v', v, 'main')
    advo.add_data('w', w, 'main')
    advo.props['coord_sys'] = 'earth'


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
        print('Data must be in the %s frame prior to using this function' %
              cs_now)

    # Calculate the rotation matrix:
    cp, sp = cos(ang), sin(ang)
    rotmat = np.array([[cp, -sp],
                       [sp, cp]], dtype=np.float32)

    # Perform the rotation:
    for nm in advo.props['rotate_vars']:
        dat = advo[nm]
        dat[:2] = np.einsum('ij,jk', rotmat, dat[:2])

    if hasattr(advo, 'orientmat'):
        advo['orientmat'][:2, :2] = np.einsum(
            'ij,kjl->ikl', rotmat, advo['orientmat'][:2, :2])

    # Finalize the output.
    advo.props['coord_sys'] = cs_new
