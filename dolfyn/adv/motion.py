import numpy as np
import scipy.signal as sig
from scipy.integrate import cumtrapz
from .rotate import inst2earth, _rotate_vel2body
import warnings


class CalcMotion(object):

    """
    A 'calculator' for computing the velocity of points that are
    rigidly connected to an ADV-body with an IMU.

    Parameters
    ----------

    advo : `adv_raw<dolfyn.adv.base.adv_raw>`
           The IMU-adv object that will be used to compute motion.

    accel_filtfreq : float
      the frequency at which to high-pass filter the acceleration
      signal to remove low-frequency drift.

    vel_filtfreq : float (optional)
      a second frequency to high-pass filter the integrated
      acceleration.  (default: 1/3 of accel_filtfreq)

    Examples
    --------

    >>> from dolfyn.adv import api as avm
    >>> from dolfyn.adv import motion as avmot

    >>> dat = avm.read_nortek('my_data_file.vec')

    >>> mcalc = avmot.CalcMotion(dat)

    # Calculate the motion of a point that is (.3, .1, .06) meters
    # from the adv-body origin:
    >>> mot = mcalc([.3, .1, .06])

    """

    def __init__(self, advo,
                 accel_filtfreq=1. / 30,
                 vel_filtfreq=None,
                 to_earth=True):

        self.advo = advo
        self.accel_filtfreq = accel_filtfreq
        if vel_filtfreq is None:
            vel_filtfreq = accel_filtfreq / 3
        self.accelvel_filtfreq = vel_filtfreq
        self.to_earth = to_earth

        self._set_Accel()
        self._set_AccelStable()
        self.AngRt = advo.AngRt  # No copy because not modified.

    def _set_Accel(self, ):
        advo = self.advo
        if advo.props['coord_sys'] == 'inst':
            self.Accel = np.einsum('ijk,ik->jk',
                                   advo.orientmat,
                                   advo.Accel)
        elif self.advo.props['coord_sys'] == 'earth':
            self.Accel = advo.Accel.copy()
        else:
            raise Exception(("Invalid coordinate system '%s'. The coordinate "
                             "system must either be 'earth' or 'inst' to "
                             "perform motion correction.")
                            % (self.advo.props['coord_sys'], ))

    def _set_AccelStable(self, ):
        """
        """
        self.AccelStable = acc = self.Accel.copy()
        if self.accel_filtfreq == 0:
            acc[:] = acc.mean(-1)[..., None]
        else:
            flt = sig.butter(1, self.accel_filtfreq / (self.advo.fs / 2))
            for idx in range(3):
                acc[idx] = sig.filtfilt(flt[0], flt[1], acc[idx])

    def __call__(self, vec):
        """
        Calculate the motion of the point specified by vec (in meters,
        in the adv-body coordinate system).

        Parameters
        ----------

        vec : |np.ndarray| (len(3) or 3 x M)
          The vector in meters (or set of vectors) from the
          body-origin (center of head end-cap) to the point of
          interest (in the body coord-sys).

        Returns
        -------
        umot : |np.ndarray| (3 x M x N_time)
          The motion (velocity) array (3, n_time).

        """
        return self.calc_uacc() + self.calc_urot(np.array(vec), )

    def calc_uacc(self, ):
        """
        Calculates the translational velocity from the acceleration
        signal.

        Returns
        -------
        uacc : |np.ndarray| (3 x n_time)
               The acceleration-induced velocity array (3, n_time).
        """
        samp_freq = self.advo.fs

        hp = self.Accel - self.AccelStable

        dat = np.concatenate((np.zeros(list(hp.shape[:-1]) + [1]),
                              cumtrapz(hp, dx=1. / samp_freq)), axis=-1)
        if self.accelvel_filtfreq > 0:
            filt_freq = self.accelvel_filtfreq
            # 8th order butterworth filter.
            filt = sig.butter(2, float(filt_freq) / (samp_freq / 2))
            for idx in range(hp.shape[0]):
                dat[idx] = dat[idx] - sig.filtfilt(filt[0], filt[1], dat[idx])
        return dat

    def calc_urot(self, vec, to_earth=None):

        """
        Calculate the induced velocity due to rotations of the instrument
        about the IMU center.

        Parameters
        ----------

        vec : |np.ndarray| (len(3) or 3 x M)
          The vector in meters (or vectors) from the body-origin
          (center of head end-cap) to the point of interest (in the
          body coord-sys).

        Returns
        -------
        urot : |np.ndarray| (3 x M x N_time)
          The rotation-induced velocity array (3, n_time).

        """

        if to_earth is None:
            to_earth = self.to_earth

        dimflag = False
        if vec.ndim == 1:
            vec = vec.copy().reshape((3, 1))
            dimflag = True

        # Correct for the body->imu distance.
        # The nortek_body2imu vector is subtracted because of
        # vector addition:
        # body2head = body2imu + imu2head
        # Thus:
        # imu2head = body2head - body2imu
        vec = vec - self.advo.body2imu_vec[:, None]

        # This motion of the point *vec* due to rotations should be the
        # cross-product of omega (rotation vector) and the vector.
        #   u=dz*omegaY-dy*omegaZ,v=dx*omegaZ-dz*omegaX,w=dy*omegaX-dx*omegaY
        # where vec=[dx,dy,dz], and AngRt=[omegaX,omegaY,omegaZ]
        urot = np.array([(vec[2][:, None] * self.AngRt[1] -
                          vec[1][:, None] * self.AngRt[2]),
                         (vec[0][:, None] * self.AngRt[2] -
                          vec[2][:, None] * self.AngRt[0]),
                         (vec[1][:, None] * self.AngRt[0] -
                          vec[0][:, None] * self.AngRt[1]),
                         ])

        if to_earth:
            urot = np.einsum('jik,jlk->ilk', self.advo['orientmat'], urot)

        if dimflag:
            return urot[:, 0, :]

        return urot


def _calc_probe_pos(advo, separate_probes=False):
    """
    !!!Currently this only works for Nortek Vectors!

    In the future, we could use the transformation matrix (and a
    probe-length lookup-table?)
    """
    # According to the ADV_DataSheet, the probe-length radius is
    # 8.6cm @ 120deg from probe-stem axis.  If I subtract 1cm
    # (!!!checkthis) to get acoustic receiver center, this is
    # 7.6cm.  In the coordinate sys of the center of the probe
    # then, the positions of the centers of the receivers is:
    if advo.make_model == 'Nortek VECTOR' and separate_probes:
        r = 0.076
        # The angle between the x-y plane and the probes
        phi = -30. * np.pi / 180.
        theta = np.array([0., 120., 240.]) * np.pi / \
            180.  # The angles of the probes from the x-axis.
        return (np.dot(advo.props['body2head_rotmat'].T,
                       np.array([r * np.cos(theta),
                                 r * np.sin(theta),
                                 r * np.tan(phi) * np.ones(3)])) +
                advo.props['body2head_vec'][:, None]
                )
    else:
        return advo.props['body2head_vec']


def correct_motion(advo,
                   accel_filtfreq=1. / 30,
                   vel_filtfreq=None,
                   to_earth=True,
                   separate_probes=False, ):
    """
    This function performs motion correction on an IMU-ADV data
    object. The IMU and ADV data should be tightly synchronized and
    contained in a single data object.

    Parameters
    ----------

    advo : dolfyn.adv.adv class

    accel_filtfreq : float
      the frequency at which to high-pass filter the acceleration
      signal to remove low-frequency drift.

    vel_filtfreq : float (optional)
      a second frequency to high-pass filter the integrated
      acceleration.  (default: 1/3 of accel_filtfreq)

    to_earth : bool (optional, default: True)
      All variables in the advo.props['rotate_vars'] list will be
      rotated into either the earth frame (to_earth=True) or the
      instrument frame (to_earth=False).

    separate_probes : bool (optional, default: False)
      a flag to perform motion-correction at the probe tips, and
      perform motion correction in beam-coordinates, then transform
      back into XYZ/earth coordinates. This correction seems to be
      lower than the noise levels of the ADV, so the defualt is to not
      use it (False).

    Returns
    -------
    This function returns None, it operates on the input data object,
    ``advo``. The following attributes are added to `advo`:

      ``uraw`` is the uncorrected velocity

      ``urot`` is the rotational component of the head motion (from
               AngRt)

      ``uacc`` is the translational component of the head motion (from
               Accel)

      ``AccelStable`` is the low-pass filtered Accel signal

    The primary velocity vector attribute, ``_u``, is motion corrected
    such that:

          _u = uraw + urot + uacc

    The signs are correct in this equation. The measured velocity
    induced by head-motion is *in the opposite direction* of the head
    motion.  i.e. when the head moves one way in stationary flow, it
    measures a velocity in the opposite direction. Therefore, to
    remove the motion from the raw signal we *add* the head motion.

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
    >>> avm.motion.correct_motion(dat)

    ``dat`` will now have motion-corrected.

    """

    if hasattr(advo, 'urot'):
        raise Exception('The data object already appears to have been motion corrected.')

    if advo.props['coord_sys'] != 'inst':
        raise Exception('The data object must be in the instrument frame to be motion corrected.')

    if vel_filtfreq is None:
        vel_filtfreq = accel_filtfreq / 3

    # Be sure the velocity data has been rotated to the body frame.
    _rotate_vel2body(advo)

    # Create the motion 'calculator':
    calcobj = CalcMotion(advo,
                         accel_filtfreq=accel_filtfreq,
                         vel_filtfreq=vel_filtfreq,
                         to_earth=to_earth)

    ##########
    # Calculate the translational velocity (from the Accel):
    advo.groups['orient'].add('uacc')
    advo.uacc = calcobj.calc_uacc()
    # Copy AccelStable to the adv-object.
    advo.groups['orient'].add('AccelStable')
    advo.AccelStable = calcobj.AccelStable

    ##########
    # Calculate rotational velocity (from AngRt):
    pos = _calc_probe_pos(advo, separate_probes)
    # Calculate the velocity of the head (or probes).
    urot = calcobj.calc_urot(pos, to_earth=False)
    if separate_probes:
        # The head->beam transformation matrix
        transMat = advo.config.head.get('TransMatrix', None)
        # The body->head transformation matrix
        rmat = advo.props['body2head_rotmat']

        # 1) Rotate body-coordinate velocities to head-coord.
        urot = np.dot(rmat, urot)
        # 2) Rotate body-coord to beam-coord (einsum),
        # 3) Take along beam-component (diagonal),
        # 4) Rotate back to head-coord (einsum),
        urot = np.einsum('ij,kj->ik',
                         transMat,
                         np.diagonal(np.einsum('ij,jkl->ikl',
                                               np.linalg.inv(transMat),
                                               urot)
                                     ))
        # 5) Rotate back to body-coord.
        urot = np.dot(rmat.T, urot)
    advo.urot = urot
    advo.groups['orient'].add('urot')

    ##########
    # Rotate the data into the correct coordinate system.
    # inst2earth expects a 'rotate_vars' property.
    # Add urot, uacc, AccelStable, to it.
    if 'rotate_vars' not in advo.props.keys():
        advo.props['rotate_vars'] = {'_u', 'urot', 'uacc',
                                     'Accel', 'AccelStable',
                                     'AngRt', 'Mag'}
    else:
        advo.props['rotate_vars'].update({'urot', 'uacc', 'AccelStable'})

    # NOTE: Accel, AccelStable, and uacc are in the earth-frame after
    #       calc_uacc() call.
    if to_earth:
        advo.Accel = calcobj.Accel
        inst2earth(advo, rotate_vars=advo.props['rotate_vars'] -
                   {'Accel', 'AccelStable', 'uacc', })
    else:
        # rotate these variables back to the instrument frame.
        inst2earth(advo, reverse=True,
                   rotate_vars={'AccelStable', 'uacc', },
                   force=True,
                   )

    ##########
    # Copy _u -> uraw prior to motion correction:
    advo.add_data('uraw', advo._u.copy(), 'main')
    # Add it to rotate_vars:
    advo.props['rotate_vars'].update({'uraw', })

    ##########
    # Remove motion from measured velocity!
    # NOTE: The plus sign is because the measured-induced velocities
    #       are in the opposite direction of the head motion.
    #       i.e. when the head moves one way in stationary flow, it
    #       measures a velocity in the opposite direction.
    advo._u += (advo.urot + advo.uacc)


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
                 vel_filtfreq=None,
                 separate_probes=False):

        self.accel_filtfreq = accel_filtfreq
        if vel_filtfreq is None:
            vel_filtfreq = accel_filtfreq / 3
        self.accelvel_filtfreq = vel_filtfreq
        self.separate_probes = separate_probes
        warnings.warn("The 'CorrectMotion' class is being deprecated "
                      "and will be removed in a future DOLfYN release. "
                      "Use the 'correct_motion' function instead.",
                      DeprecationWarning)

    def _rotate_vel2body(self, advo):
        # The transpose should do head to body.
        advo._u = np.dot(advo.props['body2head_rotmat'].T, advo._u)

    def _calc_rot_vel(self, calcobj):
        """
        Calculate the 'rotational' velocity as measured by the IMU
        rate sensor.
        """
        advo = calcobj.advo

        # This returns a 3x3 array of probe positions if
        # separate_probes is True.
        pos = self._calc_probe_pos(advo)

        # Calculate the velocity of the head (or probes).
        urot = calcobj.calc_urot(pos, to_earth=False)

        if self.separate_probes:
            # The head->beam transformation matrix
            transMat = advo.config.head.get('TransMatrix', None)
            # The body->head transformation matrix
            rmat = advo.props['body2head_rotmat']

            # 1) Rotate body-coordinate velocities to head-coord.
            urot = np.dot(rmat, urot)
            # 2) Rotate body-coord to beam-coord (einsum),
            # 3) Take along beam-component (diagonal),
            # 4) Rotate back to head-coord (einsum),
            urot = np.einsum('ij,kj->ik',
                             transMat,
                             np.diagonal(np.einsum('ij,jkl->ikl',
                                                   np.linalg.inv(transMat),
                                                   urot)
                                         ))
            # 5) Rotate back to body-coord.
            urot = np.dot(rmat.T, urot)

        advo.urot = urot
        advo.groups['orient'].add('urot')

    def _calc_probe_pos(self, advo):
        """
        !!!Currently this only works for Nortek Vectors!

        In the future, we could use the transformation matrix (and a
        probe-length lookup-table?)
        """
        # According to the ADV_DataSheet, the probe-length radius is
        # 8.6cm @ 120deg from probe-stem axis.  If I subtract 1cm
        # (!!!checkthis) to get acoustic receiver center, this is
        # 7.6cm.  In the coordinate sys of the center of the probe
        # then, the positions of the centers of the receivers is:
        if advo.make_model == 'Nortek VECTOR' and self.separate_probes:
            r = 0.076
            # The angle between the x-y plane and the probes
            phi = -30. * np.pi / 180.
            theta = np.array([0., 120., 240.]) * np.pi / \
                180.  # The angles of the probes from the x-axis.
            return (np.dot(advo.props['body2head_rotmat'].T,
                           np.array([r * np.cos(theta),
                                     r * np.sin(theta),
                                     r * np.tan(phi) * np.ones(3)])) +
                    advo.props['body2head_vec'][:, None]
                    )
        else:
            return advo.props['body2head_vec']

    def _calc_accel_vel(self, calcobj):
        advo = calcobj.advo
        advo.groups['orient'].add('uacc')
        advo.uacc = calcobj.calc_uacc()

    def __call__(self, advo, to_earth=True):
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
          - props : a dictionary that has 'body2head_vec',
            'body2head_rotmat' and 'coord_sys'.

        to_earth : bool (optional, default: True)
          A boolean that specifies whether the data should be
          rotated into the earth frame.

        Notes
        -----

        After calling this function, `advo` will have *urot* and
        *uacc* data attributes. The velocity vector attribute ``_u``
        will be motion corrected according to:

            u_corr = u_raw + uacc + urot

        Therefore, to recover the 'raw' velocity, subtract uacc and
        urot from ``_u``.

        This method does not return a data object, it operates on
        (motion corrects) the input `advo`.

        """

        calcobj = CalcMotion(advo,
                             accel_filtfreq=self.accel_filtfreq,
                             vel_filtfreq=self.accelvel_filtfreq,
                             to_earth=to_earth)

        if 'rotate_vars' not in advo.props.keys():
            advo.props['rotate_vars'] = {'_u', 'urot', 'uacc', 'uraw',
                                         'Accel', 'AccelStable',
                                         'AngRt', 'Mag'}
        else:
            advo.props['rotate_vars'].update({'urot', 'uacc', 'AccelStable', 'uraw'})

        self._rotate_vel2body(advo)
        self._calc_rot_vel(calcobj)
        self._calc_accel_vel(calcobj)

        # calcobj.Accel, calcobj.AccelStable, and uacc are already in
        # the earth frame.
        advo.groups['orient'].add('AccelStable')
        advo.AccelStable = calcobj.AccelStable
        advo.add_data('uraw', advo._u.copy(), 'main')
        if to_earth:
            advo.Accel = calcobj.Accel
            inst2earth(advo, rotate_vars=advo.props['rotate_vars'] -
                       {'Accel', 'AccelStable', 'uacc', })
        else:
            # rotate these variables back to the instrument frame.
            inst2earth(advo, reverse=True,
                       rotate_vars={'AccelStable', 'uacc', },
                       force=True,
                       )
        # NOTE: The plus sign is because the measured-induced velocities
        #       are in the opposite direction of the head motion.
        #       i.e. when the head moves one way in stationary flow, it
        #       measures a velocity in the opposite direction.
        advo._u += (advo.urot + advo.uacc)
