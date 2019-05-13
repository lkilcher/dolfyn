from __future__ import division
import numpy as np
from ..data.velocity import VelBinner
from ..data import base as db
from ..tools.misc import slice1d_along_axis, nans_like
from scipy.special import cbrt


kappa = 0.41


class TurbBinner(VelBinner):

    """
    Computes various averages and turbulence statistics from cleaned
    ADV data.

    Parameters
    ----------
    n_bin : int
      The length of `bin` s, in number of points, for this averaging
      operator.

    n_fft : int (optional, default: n_fft = n_bin)
      The length of the FFT for computing spectra (must be < n_bin)

    """

    def __call__(self, advr, out_type=None,
                 omega_range_epsilon=[6.28, 12.57],
                 Itke_thresh=0, window='hann'):
        """
        Compute a suite of turbulence statistics for the input data
        advr, and return a `binned` data object.

        Parameters
        ----------

        advr : :class:`ADVdata <base.ADVdata>`
          The raw adv data-object to `bin`, average and compute
          turbulence statistics of.

        omega_range_epsilon : iterable(2)
          The frequency range (low, high) over which to estimate the
          dissipation rate `epsilon` [rad/s].

        Itke_thresh : The threshold for velocity magnitude for
          computing the turbulence intensity. Values of Itke where
          U_mag < Itke_thresh are set to NaN.  (default: 0).

        window : 1, None, 'hann'
          The window to use for psds.

        Returns
        -------

        advb : :class:`base.ADVbinned`
          Returns an 'binned' (i.e. 'averaged') data object. All
          fields of the input data object are averaged in n_bin
          chunks. This object also computes the following items over
          those chunks:

          - tke\_vec : The energy in each component (components are also
            accessible as
            :attr:`upup_ <dolfyn.data.velocity.VelBindatTke.upup_>`,
            :attr:`vpvp_ <dolfyn.data.velocity.VelBindatTke.vpvp_>`,
            :attr:`wpwp_ <dolfyn.data.velocity.VelBindatTke.wpwp_>`)

          - stress : The Reynolds stresses (each component is
            accessible as
            :attr:`upwp_ <dolfyn.data.velocity.VelBindatTke.upwp_>`,
            :attr:`vpwp_ <dolfyn.data.velocity.VelBindatTke.vpwp_>`,
            :attr:`upvp_ <dolfyn.data.velocity.VelBindatTke.upvp_>`)

          - sigma_Uh : The standard deviation of the horizontal
            velocity.

          - Spec : A data group containing the spectra of the velocity
            in radial frequency units. The data group contains:
             - vel : the velocity spectra array (m^2/s/radian))
             - omega : the radial frequncy (radian / s)

        """
        # warnings.warn("The instance.__call__ syntax of turbulence averaging"
        #               " is being deprecated. Use the functional form, e.g. '"
        #               "adv.turbulence.calc_turbulence(advr, n_bin={})', instead."
        #               .format(self.n_bin))
        if out_type is None:
            try:
                out_type = advr._avg_class
            except AttributeError:
                out_type = type(advr)
        out = out_type()
        self._check_indata(advr)
        self.do_avg(advr, out)
        noise = advr.get('doppler_noise', [0, 0, 0])
        out['tke_vec'] = self.calc_tke(advr['vel'], noise=noise)
        out['stress'] = self.calc_stress(advr['vel'])
        out['sigma_Uh'] = (np.std(self.reshape(advr.U_mag),
                                  -1,
                                  dtype=np.float64) -
                           (noise[0] + noise[1]) / 2)
        out.props['Itke_thresh'] = Itke_thresh
        out['Spec'] = db.FreqData()
        out['Spec']['vel'] = self.calc_vel_psd(advr['vel'],
                                               noise=noise,
                                               window=window)
        out['Spec']['omega'] = self.calc_omega()
        out.props['n_bin'] = self.n_bin
        out.props['n_fft'] = self.n_fft
        out.props['n_fft_coh'] = self.n_fft_coh

        # out.add_data('epsilon',self.calc_epsilon_LT83(out.Spec,out.omega,
        # out.U_mag,omega_range=omega_range_epsilon),'main')
        # out.add_data('Acov',self.calc_acov(advr['vel']),'corr')
        # out.add_data('Lint',self.calc_Lint(out.Acov,out.U_mag),'main')
        return out

    def calc_epsilon_LT83(self, spec, omega, U_mag, omega_range=[6.28, 12.57]):
        r"""
        Calculate the dissipation rate from the spectrum.

        Parameters
        ----------

        spec : |np.ndarray| (...,n_time,n_f)
          The spectrum array [m^2/s/radian]

        omega : |np.ndarray| (n_f)
          The frequency array [rad/s]

        U_mag : |np.ndarray| (...,n_time)
          The velocity magnitude [m/s]

        omega_range : iterable(2)
          The range over which to integrate/average the spectrum.

        Returns
        -------
        epsilon : np.ndarray (...,n_time)
          The dissipation rate.

        Notes
        -----

        This uses the `standard` formula for dissipation:

        .. math:: S(k) = \alpha \epsilon^{2/3} k^{-5/3}

        where :math:`\alpha = 0.5` (1.5 for all three velocity
        components), `k` is wavenumber and `S(k)` is the turbulent
        kinetic energy spectrum.

        With :math:`k \rightarrow \omega / U` then--to preserve variance--
        :math:`S(k) = U S(\omega)` and so this becomes:

        .. math:: S(\omega) = \alpha \epsilon^{2/3} \omega^{-5/3} U^{2/3}

        LT83 : Lumley and Terray "Kinematics of turbulence convected
        by a random wave field" JPO, 1983, 13, 2000-2007.

        """
        inds = (omega_range[0] < omega) & (omega < omega_range[1])
        a = 0.5
        f_shp = [1] * (spec.ndim - 1) + [inds.sum()]
        return np.mean(spec[..., inds] *
                       (omega[inds].reshape(f_shp)) ** (5 / 3) / a,
                       axis=-1) ** (3 / 2) / U_mag

    def calc_epsilon_SF(self, veldat, umag, fs=None, freq_rng=[.5, 5.]):
        """
        Calculate epsilon using the "structure function" (SF) method.

        Parameters
        ----------

        veldat   : |np.ndarray| (..., n_time, n_bin)
          The raw velocity signal (last dimension time) upon which to
          perform the SF technique.

        umag     : |np.ndarray| (..., n_time)
          The bin-averaged horizontal velocity magnitude.

        fs       : float
          The sample rate of `veldat` [hz].

        freq_rng : iterable(2)
          The frequency range over which to compute the SF [hz].

        Returns
        -------

        epsilon : |np.ndarray| (..., n_time)
          The dissipation rate.

        """
        fs = self._parse_fs(fs)
        dt = self.reshape(veldat)
        out = np.empty(dt.shape[:-1], dtype=dt.dtype)
        for slc in slice1d_along_axis(dt.shape, -1):
            up = dt[slc]
            lag = umag[slc[:-1]] / fs * np.arange(up.shape[0])
            DAA = nans_like(lag)
            for L in range(int(fs / freq_rng[1]), int(fs / freq_rng[0])):
                DAA[L] = np.mean((up[L:] - up[:-L]) ** 2, dtype=np.float64)
            cv2 = DAA / (lag ** (2 / 3))
            cv2m = np.median(cv2[np.logical_not(np.isnan(cv2))])
            out[slc[:-1]] = (cv2m / 2.1) ** (3 / 2)
        return out

    def up_angle(self, Uh_complex):
        """
        Calculate the angle of the turbulence fluctuations.

        Parameters
        ----------
        Uh_complex  : |np.ndarray| (..., n_time * n_bin)
          The complex, raw horizontal velocity (non-binned).

        Returns
        -------

        theta : |np.ndarray| (..., n_time)
          The angle of the turbulence [rad]
        """
        dt = self.demean(Uh_complex)
        fx = dt.imag <= 0
        dt[fx] = dt[fx] * np.exp(1j * np.pi)
        return np.angle(np.mean(dt, -1, dtype=np.complex128))

    def calc_epsilon_TE01(self, advbin, advraw, omega_range=[6.28, 12.57]):
        """
        Calculate the dissipation according to TE01.

        Parameters
        ----------

        advbin : :class:`ADVbinned <base.ADVbinned>`
          The binned adv object. The following spectra and basic
          turbulence statistics must already be computed.

        advraw : :class:`ADVdata <base.ADVdata>`
          The raw adv object.

        Notes
        -----

        TE01 : Trowbridge, J and Elgar, S, "Turbulence measurements in
               the Surf Zone" JPO, 2001, 31, 2403-2417.
        """

        # Assign local names
        U_mag = np.abs(advbin.U)
        Itke = advbin.Itke
        theta = advbin.U_angle - self.up_angle(advraw.U)
        omega = advbin.omega

        # Calculate constants
        alpha = 1.5
        intgrl = self._calc_epsTE01_int(Itke, theta)

        # Index data to be used
        inds = (omega_range[0] < omega) & (omega < omega_range[1])
        spec = advbin.Spec[..., inds]
        omega = advbin.omega[inds].reshape(
            [1] * (advbin.Spec.ndim - 2) + [sum(inds)])

        # Estimate values
        # u component
        out = (np.mean((spec[0] + spec[1]) * (omega) ** (5 / 3), -1) /
               (21 / 55 * alpha * intgrl)
               ) ** (3 / 2) / U_mag
        # v component
        out = (np.mean((spec[0] + spec[1]) * (omega) ** (5 / 3), -1) /
               (21 / 55 * alpha * intgrl)
               ) ** (3 / 2) / U_mag

        out += (np.mean(spec[2] * (omega) ** (5 / 3), -1) /
                (12 / 55 * alpha * intgrl)
                ) ** (3 / 2) / U_mag

        # Average the two estimates.
        out *= 0.5
        return out

    def _calc_epsTE01_int(self, Itke, theta):
        """
        The integral, equation A13, in [TE01].


        Parameters
        ----------

        Itke : |np.ndarray|
          (beta in TE01) is the turbulence intensity ratio:
          \sigma_u / V


        theta : |np.ndarray|
          is the angle between the mean flow, and the primary axis of
          velocity fluctuations.

        """
        x = np.arange(-20, 20, 1e-2)  # I think this is a long enough range.
        out = np.empty_like(Itke.flatten())
        for i, (b, t) in enumerate(zip(Itke.flatten(), theta.flatten())):
            out[i] = np.trapz(
                cbrt(x ** 2 - 2 / b * np.cos(t) * x + b ** (-2)) *
                np.exp(-0.5 * x ** 2), x)
        return out.reshape(Itke.shape) * \
            (2 * np.pi) ** (-0.5) * Itke ** (2 / 3)

    def calc_Lint(self, corr_vel, U_mag, fs=None):
        """
        Calculate integral length scales.

        Parameters
        ----------

        corr_vel : |np.ndarray|
          The auto-covariance array (i.e. computed using calc_acov).

        U_mag : |np.ndarray| (..., n_time)
          The velocity magnitude for this bin.

        fs : float
          The raw sample rate.

        Returns
        -------
        Lint : |np.ndarray| (..., n_time)
          The integral length scale (Tint*U_mag).

        Notes
        -----

        The integral time scale (Tint) is the lag-time at which the
        auto-covariance falls to 1/e.

        """
        fs = self._parse_fs(fs)
        return (U_mag / fs *
                np.argmin((corr_vel / corr_vel[..., :1]) >
                          (1 / np.e), axis=-1))


def calc_turbulence(advr, n_bin, n_fft=None, out_type=None,
                    omega_range_epsilon=[6.28, 12.57],
                    Itke_thresh=0, window='hann'):
    """
    Compute a suite of turbulence statistics for the input data
    advr, and return a `binned` data object.

    Parameters
    ----------

    advr : :class:`ADVdata <base.ADVdata>`
      The raw adv data-object to `bin`, average and compute
      turbulence statistics of.

    omega_range_epsilon : iterable(2)
      The frequency range (low, high) over which to estimate the
      dissipation rate `epsilon` [rad/s].

    Itke_thresh : The threshold for velocity magnitude for
      computing the turbulence intensity. Values of Itke where
      U_mag < Itke_thresh are set to NaN.  (default: 0).

    window : 1, None, 'hann'
      The window to use for psds.

    Returns
    -------

    advb : :class:`base.ADVbinned`
      Returns an 'binned' (i.e. 'averaged') data object. All
      fields of the input data object are averaged in n_bin
      chunks. This object also computes the following items over
      those chunks:

      - tke\_vec : The energy in each component, each components is
        alternatively accessible as:
        :attr:`upup_ <dolfyn.data.velocity.VelBindatTke.upup_>`,
        :attr:`vpvp_ <dolfyn.data.velocity.VelBindatTke.vpvp_>`,
        :attr:`wpwp_ <dolfyn.data.velocity.VelBindatTke.wpwp_>`)

      - stress : The Reynolds stresses, each component is
        alternatively accessible as:
        :attr:`upwp_ <dolfyn.data.velocity.VelBindatTke.upwp_>`,
        :attr:`vpwp_ <dolfyn.data.velocity.VelBindatTke.vpwp_>`,
        :attr:`upvp_ <dolfyn.data.velocity.VelBindatTke.upvp_>`)

      - sigma_Uh : The standard deviation of the horizontal
        velocity.

      - Spec : A data group containing the spectra of the velocity
        in radial frequency units. The data group contains:
         - vel : the velocity spectra array (m^2/s/radian))
         - omega : the radial frequncy (radian / s)

    """
    calculator = TurbBinner(n_bin, advr.props['fs'], n_fft=n_fft,
                            out_type=out_type,
                            omega_range_epsilon=omega_range_epsilon,
                            Itke_thresh=Itke_thresh, window=window)
    return calculator(advr)
