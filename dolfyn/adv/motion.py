from __future__ import division
import numpy as np
import scipy.signal as sig
from scipy.integrate import cumtrapz
from ..rotate import vector as rot
import warnings


def get_body2imu(make_model):
    if make_model == 'nortek vector':
        # In inches it is: (0.25, 0.25, 5.9)
        return np.array([0.00635, 0.00635, 0.14986])
    elif make_model.startswith('nortek signature'):
        return np.array([0.0, 0.0, 0.0])
    else:
        raise Exception("The imu->body vector is unknown for this instrument.")


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
      signal to remove low-frequency drift. (default: 0.03 Hz)

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
    _default_accel_filtfreq = 0.03

    def __init__(self, advo,
                 accel_filtfreq=None,
                 vel_filtfreq=None,
                 to_earth=True):

        self.advo = advo
        self._check_filtfreqs(accel_filtfreq,
                              vel_filtfreq)
        self.to_earth = to_earth

        self._set_Accel()
        self._set_acclow()
        self.angrt = advo['orient']['angrt']  # No copy because not modified.

    def _check_filtfreqs(self, accel_filtfreq, vel_filtfreq):
        datval = self.advo.props.get('motion accel_filtfreq Hz', None)
        if datval is None:
            if accel_filtfreq is None:
                accel_filtfreq = self._default_accel_filtfreq
                # else use the accel_filtfreq value
        else:
            if accel_filtfreq is None:
                accel_filtfreq = datval
            else:
                if datval != accel_filtfreq:
                    # Neither are None!?!
                    warnings.warn(
                        "The data object specifies a value for accel_filtfreq "
                        "of {} Hz. Overriding this with the user-specified "
                        "value: {} Hz.".format(datval, accel_filtfreq))
        if vel_filtfreq is None:
            vel_filtfreq = self.advo.props.get('motion vel_filtfreq Hz', None)
        if vel_filtfreq is None:
            vel_filtfreq = accel_filtfreq / 3.0
        self.accel_filtfreq = accel_filtfreq
        self.accelvel_filtfreq = vel_filtfreq

    def _set_Accel(self, ):
        advo = self.advo
        if advo.props['coord_sys'] == 'inst':
            self.accel = np.einsum('ij...,i...->j...',
                                   advo['orient']['orientmat'],
                                   advo['orient']['accel'])
        elif self.advo.props['coord_sys'] == 'earth':
            self.accel = advo['orient']['accel'].copy()
        else:
            raise Exception(("Invalid coordinate system '%s'. The coordinate "
                             "system must either be 'earth' or 'inst' to "
                             "perform motion correction.")
                            % (self.advo.props['coord_sys'], ))

    def _set_acclow(self, ):
        """
        """
        self.acclow = acc = self.accel.copy()
        if self.accel_filtfreq == 0:
            acc[:] = acc.mean(-1)[..., None]
        else:
            flt = sig.butter(1, self.accel_filtfreq / (self.advo['props']['fs'] / 2))
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
        return self.calc_velacc() + self.calc_velrot(np.array(vec), )

    def calc_velacc(self, ):
        """
        Calculates the translational velocity from the high-pass
        filtered acceleration signal.

        Returns
        -------
        velacc : |np.ndarray| (3 x n_time)
               The acceleration-induced velocity array (3, n_time).
        """
        samp_freq = self.advo['props']['fs']

        # Get high-pass accelerations
        hp = self.accel - self.acclow

        # Integrate in time to get velocities
        dat = np.concatenate((np.zeros(list(hp.shape[:-1]) + [1]),
                              cumtrapz(hp, dx=1 / samp_freq)), axis=-1)

        # Filter again?
        if self.accelvel_filtfreq > 0:
            filt_freq = self.accelvel_filtfreq
            # 2nd order Butterworth filter
            # Applied twice by 'filtfilt' = 4th order butterworth
            filt = sig.butter(2, float(filt_freq) / (samp_freq / 2))
            for idx in range(hp.shape[0]):
                dat[idx] = dat[idx] - sig.filtfilt(filt[0], filt[1], dat[idx])
        return dat

    def calc_velrot(self, vec, to_earth=None):

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
        velrot : |np.ndarray| (3 x M x N_time)
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
        vec = vec - get_body2imu(self.advo._make_model)[:, None]

        # This motion of the point *vec* due to rotations should be the
        # cross-product of omega (rotation vector) and the vector.
        #   u=dz*omegaY-dy*omegaZ,v=dx*omegaZ-dz*omegaX,w=dy*omegaX-dx*omegaY
        # where vec=[dx,dy,dz], and angrt=[omegaX,omegaY,omegaZ]
        velrot = np.array([(vec[2][:, None] * self.angrt[1] -
                            vec[1][:, None] * self.angrt[2]),
                           (vec[0][:, None] * self.angrt[2] -
                            vec[2][:, None] * self.angrt[0]),
                           (vec[1][:, None] * self.angrt[0] -
                            vec[0][:, None] * self.angrt[1]),
                           ])

        if to_earth:
            velrot = np.einsum('ji...,j...->i...', self.advo['orientmat'], velrot)

        if dimflag:
            return velrot[:, 0, :]

        return velrot


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
    p = advo.props
    if separate_probes and p['inst_make'].lower() == 'nortek' and\
       p['inst_model'].lower == 'vector':
        r = 0.076
        # The angle between the x-y plane and the probes
        phi = np.deg2rad(-30)
        # The angles of the probes from the x-axis:
        theta = np.deg2rad(np.array([0., 120., 240.]))
        return (np.dot(advo.props['body2head_rotmat'].T,
                       np.array([r * np.cos(theta),
                                 r * np.sin(theta),
                                 r * np.tan(phi) * np.ones(3)])) +
                advo.props['body2head_vec'][:, None]
                )
    else:
        return advo.props['body2head_vec']


def correct_motion(advo,
                   accel_filtfreq=None,
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

      ``velraw`` is the uncorrected velocity

      ``velrot`` is the rotational component of the head motion (from
                 angrt)

      ``velacc`` is the translational component of the head motion (from
                 accel, the high-pass filtered accel signal)

      ``acclow`` is the low-pass filtered accel signal (i.e., 

    The primary velocity vector attribute, ``vel``, is motion corrected
    such that:

          vel = velraw + velrot + velacc

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

    if hasattr(advo, 'velrot') or advo.props.get('motion corrected', False):
        raise Exception('The data object appears to already have been '
                        'motion corrected.')

    if advo.props['coord_sys'] != 'inst':
        advo.rotate2('inst', inplace=True)

    # Be sure the velocity data has been rotated to the body frame.
    rot._rotate_vel2body(advo)

    # Create the motion 'calculator':
    calcobj = CalcMotion(advo,
                         accel_filtfreq=accel_filtfreq,
                         vel_filtfreq=vel_filtfreq,
                         to_earth=to_earth)

    ##########
    # Calculate the translational velocity (from the accel):
    advo['orient']['velacc'] = calcobj.calc_velacc()
    # Copy acclow to the adv-object.
    advo['orient']['acclow'] = calcobj.acclow

    ##########
    # Calculate rotational velocity (from angrt):
    pos = _calc_probe_pos(advo, separate_probes)
    # Calculate the velocity of the head (or probes).
    velrot = calcobj.calc_velrot(pos, to_earth=False)
    if separate_probes:
        # The head->beam transformation matrix
        transMat = advo.config.head.get('TransMatrix', None)
        # The body->head transformation matrix
        rmat = advo.props['body2head_rotmat']

        # 1) Rotate body-coordinate velocities to head-coord.
        velrot = np.dot(rmat, velrot)
        # 2) Rotate body-coord to beam-coord (einsum),
        # 3) Take along beam-component (diagonal),
        # 4) Rotate back to head-coord (einsum),
        velrot = np.einsum('ij,kj->ik',
                           transMat,
                           np.diagonal(np.einsum('ij,j...->i...',
                                                 np.linalg.inv(transMat),
                                                 velrot)))
        # 5) Rotate back to body-coord.
        velrot = np.dot(rmat.T, velrot)
    advo['orient']['velrot'] = velrot

    ##########
    # Rotate the data into the correct coordinate system.
    # inst2earth expects a 'rotate_vars' property.
    # Add velrot, velacc, acclow, to it.
    if 'rotate_vars' not in advo.props:
        advo.props['rotate_vars'] = {'vel', 'orient.velrot', 'orient.velacc',
                                     'orient.accel', 'orient.acclow',
                                     'orient.angrt', 'orient.mag'}
    else:
        advo.props['rotate_vars'].update({'orient.velrot',
                                          'orient.velacc',
                                          'orient.acclow'})

    # NOTE: accel, acclow, and velacc are in the earth-frame after
    #       calc_velacc() call.
    if to_earth:
        advo['orient']['accel'] = calcobj.accel
        rot.inst2earth(advo, rotate_vars=advo.props['rotate_vars'] -
                       {'orient.accel', 'orient.acclow',
                        'orient.velacc', })
    else:
        # rotate these variables back to the instrument frame.
        rot.inst2earth(advo, reverse=True,
                       rotate_vars={'orient.acclow', 'orient.velacc', },
                       force=True, )

    ##########
    # Copy vel -> velraw prior to motion correction:
    advo['velraw'] = advo.vel.copy()
    # Add it to rotate_vars:
    advo.props['rotate_vars'].update({'velraw', })

    ##########
    # Remove motion from measured velocity!
    # NOTE: The plus sign is because the measured-induced velocities
    #       are in the opposite direction of the head motion.
    #       i.e. when the head moves one way in stationary flow, it
    #       measures a velocity in the opposite direction.
    velmot = advo['orient']['velrot'] + advo['orient']['velacc']
    if advo.props['inst_type'] == 'ADP':
        velmot = velmot[:, None]
    advo['vel'][:3] += velmot
    if advo._make_model.startswith('nortek signature') and \
       advo['vel'].shape[0] > 3:
        # This assumes these are w.
        advo['vel'][3:] += velmot[2:]
    advo.props['motion corrected'] = True
    advo.props['motion accel_filtfreq Hz'] = calcobj.accel_filtfreq


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

    def __init__(self, accel_filtfreq=None,
                 vel_filtfreq=None,
                 separate_probes=False):

        self.accel_filtfreq = accel_filtfreq
        self.accelvel_filtfreq = vel_filtfreq
        self.separate_probes = separate_probes
        warnings.warn("The 'CorrectMotion' class is being deprecated "
                      "and will be removed in a future DOLfYN release. "
                      "Use the 'correct_motion' function instead.",
                      DeprecationWarning)

    def _rotate_vel2body(self, advo):
        rot._rotate_vel2body(advo)

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
        velrot = calcobj.calc_velrot(pos, to_earth=False)

        if self.separate_probes:
            # The head->beam transformation matrix
            transMat = advo.config.head.get('TransMatrix', None)
            # The body->head transformation matrix
            rmat = advo.props['body2head_rotmat']

            # 1) Rotate body-coordinate velocities to head-coord.
            velrot = np.dot(rmat, velrot)
            # 2) Rotate body-coord to beam-coord (einsum),
            # 3) Take along beam-component (diagonal),
            # 4) Rotate back to head-coord (einsum),
            velrot = np.einsum('ij,kj->ik',
                               transMat,
                               np.diagonal(np.einsum('ij,j...->i...',
                                                     np.linalg.inv(transMat),
                                                     velrot)))
            # 5) Rotate back to body-coord.
            velrot = np.dot(rmat.T, velrot)

        advo['orient']['velrot'] = velrot

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
        p = advo.props
        if self.separate_probes and p['inst_make'].lower() == 'nortek' and \
           p['inst_model'].lower == 'vector':
            r = 0.076
            # The angle between the x-y plane and the probes
            phi = np.deg2rad(-30)
            # The angles of the probes from the x-axis:
            theta = np.deg2rad(np.array([0., 120., 240.]))
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
        advo['orient']['velacc'] = calcobj.calc_velacc()

    def __call__(self, advo, to_earth=True):
        """
        Perform motion correction on an IMU-equipped ADV object.

        Parameters
        ----------
        advo : :class:`ADVdata <base.ADVdata>`
          The adv object on which to perform motion correction.
          It must contain the following data attributes:

          - vel : The velocity array.
          - accel : The translational acceleration array.
          - angrt : The rotation-rate array.
          - orientmat : The orientation matrix.
          - props : a dictionary that has 'body2head_vec',
            'body2head_rotmat' and 'coord_sys'.

        to_earth : bool (optional, default: True)
          A boolean that specifies whether the data should be
          rotated into the earth frame.

        Notes
        -----

        After calling this function, `advo` will have *velrot* and
        *velacc* data attributes. The velocity vector attribute ``vel``
        will be motion corrected according to:

            u_corr = u_raw + velacc + velrot

        Therefore, to recover the 'raw' velocity, subtract velacc and
        velrot from ``vel``.

        This method does not return a data object, it operates on
        (motion corrects) the input `advo`.

        """
        if hasattr(advo, 'velrot') or \
           advo.props.get('motion corrected', False):
            raise Exception('The data object appears to already have been '
                            'motion corrected.')

        if not advo.props['inst_type'] == 'ADV':
            raise Exception("This motion correction tool currently only works "
                            "for ADV data objects.")

        if advo.props['coord_sys'] != 'inst':
            advo.rotate2('inst', inplace=True)

        calcobj = CalcMotion(advo,
                             accel_filtfreq=self.accel_filtfreq,
                             vel_filtfreq=self.accelvel_filtfreq,
                             to_earth=to_earth)

        if 'rotate_vars' not in advo.props:
            advo.props['rotate_vars'] = {'vel', 'velraw',
                                         'orient.velrot', 'orient.velacc',
                                         'orient.accel', 'orient.acclow',
                                         'orient.angrt', 'orient.mag'}
        else:
            advo.props['rotate_vars'].update({'velraw',
                                              'orient.velrot', 'orient.velacc',
                                              'orient.acclow', })

        self._rotate_vel2body(advo)
        self._calc_rot_vel(calcobj)
        self._calc_accel_vel(calcobj)

        # calcobj.accel, calcobj.acclow, and velacc are already in
        # the earth frame.
        advo['orient']['acclow'] = calcobj.acclow
        advo['velraw'] = advo.vel.copy()
        if to_earth:
            advo['orient']['accel'] = calcobj.accel
            rot.inst2earth(advo, rotate_vars=advo.props['rotate_vars'] -
                           {'orient.accel', 'orient.acclow',
                            'orient.velacc', })
        else:
            # rotate these variables back to the instrument frame.
            rot.inst2earth(advo, reverse=True,
                           rotate_vars={'orient.acclow',
                                        'orient.velacc', },
                           force=True, )
        # NOTE: The plus sign is because the measured-induced velocities
        #       are in the opposite direction of the head motion.
        #       i.e. when the head moves one way in stationary flow, it
        #       measures a velocity in the opposite direction.
        advo['vel'] += (advo['orient']['velrot'] + advo['orient']['velacc'])
        advo.props['motion corrected'] = True
        advo.props['motion accel_filtfreq Hz'] = calcobj.accel_filtfreq
