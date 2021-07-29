from __future__ import division
import numpy as np
from ..velocity import VelBinner
#from ..data import base as db
import warnings
from ..tools.misc import slice1d_along_axis, nans_like
from scipy.special import cbrt
import xarray as xr

#kappa = 0.41

class TurbBinner(VelBinner):
    """
    A class that builds upon `VelBinner` for calculating turbulence 
    statistics and velocity spectra

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
                 window='hann'):
        """
        Compute a suite of turbulence statistics for the input data
        advr, and return a `binned` data object.

        Parameters
        ----------

        advr : xarray.Dataset
          The raw adv dataset to `bin`, average and compute
          turbulence statistics of.

        omega_range_epsilon : iterable(2)
          The frequency range (low, high) over which to estimate the
          dissipation rate `epsilon` [rad/s].

        window : 1, None, 'hann'
          The window to use for psds.

        Returns
        -------

        advb : xarray.Dataset
          Returns an 'binned' (i.e. 'averaged') dataset. All
          fields (variables) of the input dataset are averaged in n_bin
          chunks. This object also computes the following items over
          those chunks:

          - tke_vec : The energy in each component (components are also
            accessible as
            :attr:`upup_ <dolfyn.data.velocity.TKE.upup_>`,
            :attr:`vpvp_ <dolfyn.data.velocity.TKE.vpvp_>`,
            :attr:`wpwp_ <dolfyn.data.velocity.TKE.wpwp_>`)

          - stress : The Reynolds stresses (each component is
            accessible as
            :attr:`upvp_ <dolfyn.data.velocity.TKE.upvp_>`,
            :attr:`upwp_ <dolfyn.data.velocity.TKE.upwp_>`,
            :attr:`vpwp_ <dolfyn.data.velocity.TKE.vpwp_>`)

          - U_std : The standard deviation of the horizontal
            velocity `U_mag`.

          - S: A DataArray containing the spectra of the velocity
            in radial frequency units. This DataArray contains:
            - spectra : the velocity spectra array (m^2/s/rad))
            - omega : the radial frequency (rad/s)

        """
        out = type(advr)()
        out = self.do_avg(advr, out)
        
        noise = advr.get('doppler_noise', [0, 0, 0])
        out['tke_vec'] = self.calc_tke(advr['vel'], noise=noise)
        out['stress_vec'] = self.calc_stress(advr['vel'])

        out['S'] = self.calc_vel_psd(advr['vel'],
                                     window=window,
                                     freq_units='rad/s',
                                     noise=noise)
        out.attrs['n_bin'] = self.n_bin
        out.attrs['n_fft'] = self.n_fft
        out.attrs['n_fft_coh'] = self.n_fft_coh

        return out


    def calc_epsilon_LT83(self, S, U_mag, omega_range=[6.28, 12.57]):
        """
        Calculate the dissipation rate from the PSD.

        Parameters
        ----------

        S : xarray.DataArray (...,n_time,n_f)
          The spectrum array [m^2/s/rad] with frequency vector 
          'omega' (rad/s)

        U_mag : |np.ndarray| (...,n_time)
          The bin-averaged horizontal velocity [m/s] (from dataset shortcut)

        omega_range : iterable(2)
          The range over which to integrate/average the spectrum.

        Returns
        -------
        epsilon : xr.DataArray (...,n_time)
          The dissipation rate.

        Notes
        -----
        
        This uses the `standard` formula for dissipation:
            
        .. math:: S(k) = \\alpha \\epsilon^{2/3} k^{-5/3}
        
        where :math:`\\alpha = 0.5` (1.5 for all three velocity
        components), `k` is wavenumber and `S(k)` is the turbulent
        kinetic energy spectrum.
        
        With :math:`k \\rightarrow \\omega / U`, then -- to preserve variance -- 
        :math:`S(k) = U S(\\omega)`, and so this becomes:
            
        .. math:: S(\\omega) = \\alpha \\epsilon^{2/3} \\omega^{-5/3} U^{2/3}

        LT83 : Lumley and Terray "Kinematics of turbulence convected
        by a random wave field" JPO, 1983, 13, 2000-2007.

        """
        omega = S.omega

        idx = np.where((omega_range[0] < omega) & (omega < omega_range[1]))
        idx = idx[0]
        
        a = 0.5
        out = (S.isel(omega=idx) *
               omega.isel(omega=idx)**(5/3) / a).mean(axis=-1)**(3/2) / U_mag
        
        out = xr.DataArray(out, name='dissipation_rate',
                           attrs={'units':'m^2/s^3',
                                       'method':'LT83'})
        return out


    def calc_epsilon_SF(self, vel_raw, U_mag, fs=None, freq_rng=[2., 4.]):
        """
        Calculate dissipation rate using the "structure function" (SF) method

        Parameters
        ----------

        vel_raw : xarray.DataArray
          The raw velocity data (with dimension time) upon 
          which to perform the SF technique. 

        U_mag : xarray.DataArray
          The bin-averaged horizontal velocity (from dataset shortcut)

        fs : float
          The sample rate of `vel_raw` [Hz]

        freq_rng : iterable(2)
          The frequency range over which to compute the SF [Hz]
          (i.e. the frequency range within which the isotropic 
          turbulence cascade falls)

        Returns
        -------

        epsilon : xarray.DataArray
          The dissipation rate

        """
        veldat = vel_raw.values

        fs = self._parse_fs(fs)
        if freq_rng[1] > fs:
            warnings.warn('Max freq_range cannot be greater than fs')
        
        dt = self.reshape(veldat)
        out = np.empty(dt.shape[:-1], dtype=dt.dtype)
        for slc in slice1d_along_axis(dt.shape, -1):
            up = dt[slc]
            lag = U_mag.values[slc[:-1]] / fs * np.arange(up.shape[0])
            DAA = nans_like(lag)
            for L in range(int(fs / freq_rng[1]), int(fs / freq_rng[0])):
                DAA[L] = np.nanmean((up[L:] - up[:-L]) ** 2, dtype=np.float64)
            cv2 = DAA / (lag ** (2 / 3))
            cv2m = np.median(cv2[np.logical_not(np.isnan(cv2))])
            out[slc[:-1]] = (cv2m / 2.1) ** (3 / 2)
            
        return xr.DataArray(out, name='dissipation_rate',
                            coords=U_mag.coords,
                            dims=U_mag.dims,
                            attrs={'units':'m^2/s^3',
                                  'method':'structure function'})


    def _up_angle(self, U_complex):
        """
        Calculate the angle of the turbulence fluctuations.

        Parameters
        ----------
        
        U_complex  : |np.ndarray| (..., n_time * n_bin)
          The complex, raw horizontal velocity (non-binned)

        Returns
        -------

        theta : |np.ndarray| (..., n_time)
          The angle of the turbulence [rad]
          
        """
        dt = self._demean(U_complex)
        fx = dt.imag <= 0
        dt[fx] = dt[fx] * np.exp(1j * np.pi)
        
        return np.angle(np.mean(dt, -1, dtype=np.complex128))


    def _calc_epsTE01_int(self, I_tke, theta):
        """
        The integral, equation A13, in [TE01].

        Parameters
        ----------

        I_tke : |np.ndarray|
          (beta in TE01) is the turbulence intensity ratio:
          \\sigma_u / V


        theta : |np.ndarray|
          is the angle between the mean flow and the primary axis of
          velocity fluctuations

        """
        x = np.arange(-20, 20, 1e-2)  # I think this is a long enough range.
        out = np.empty_like(I_tke.flatten())
        for i, (b, t) in enumerate(zip(I_tke.flatten(), theta.flatten())):
            out[i] = np.trapz(
                cbrt(x**2 - 2/b*np.cos(t)*x + b**(-2)) *
                np.exp(-0.5 * x ** 2), x)
            
        return out.reshape(I_tke.shape) * \
            (2 * np.pi) ** (-0.5) * I_tke ** (2 / 3)
            

    def calc_epsilon_TE01(self, dat_raw, dat_avg, omega_range=[6.28, 12.57]):
        """
        Calculate the dissipation rate according to TE01.

        Parameters
        ----------

        dat_raw : xarray.Dataset
          The raw (off the instrument) adv dataset
          
        dat_avg : xarray.Dataset
          The bin-averaged adv dataset (calc'd from 'calc_turbulence' or
          'do_avg'). The spectra (S) and basic turbulence statistics 
          ('tke_vec' and 'stress_vec') must already be computed.

        Notes
        -----

        TE01 : Trowbridge, J and Elgar, S, "Turbulence measurements in
        the Surf Zone" JPO, 2001, 31, 2403-2417.
               
        """

        # Assign local names
        U_mag = dat_avg.Veldata.U_mag.values
        I_tke = dat_avg.Veldata.I_tke.values
        theta = dat_avg.Veldata.U_dir.values*(np.pi/180) - \
                self._up_angle(dat_raw.Veldata.U.values)
        omega = dat_avg.S.omega.values

        # Calculate constants
        alpha = 1.5
        intgrl = self._calc_epsTE01_int(I_tke, theta)

        # Index data to be used
        inds = (omega_range[0] < omega) & (omega < omega_range[1])
        spec = dat_avg.S[..., inds].values
        omega = omega[inds].reshape([1] * (dat_avg.S.ndim - 2) + [sum(inds)])

        # Estimate values (u and v component calculations are added together)
        # u component (equation 6)
        out = (np.nanmean((spec[0] + spec[1]) * omega**(5/3), -1) /
               (21/55 * alpha * intgrl))**(3/2) / U_mag

        # # v component
        # out = (np.mean((spec[0] + spec[1]) * (omega) ** (5 / 3), -1) /
        #        (21 / 55 * alpha * intgrl)
        #        ) ** (3 / 2) / U_mag
        
        # Add w component
        out += (np.nanmean(spec[2] * omega**(5/3), -1) /
                (12/55 * alpha * intgrl))**(3/2) / U_mag

        # Average the two estimates
        out *= 0.5
        
        return xr.DataArray(out, name='dissipation_rate',
                            coords={'time':dat_avg.S.time}, 
                            dims='time',
                            attrs={'units':'m^2/s^3',
                                   'method':'TE01'})


    def calc_L_int(self, a_cov, vel_avg, fs=None):
        """
        Calculate integral length scales.

        Parameters
        ----------

        a_cov : xarray.DataArray
          The auto-covariance array (i.e. computed using `calc_acov`).

        vel_avg : xarray.DataArray
          The bin-averaged velocity (from dataset shortcut)

        fs : float
          The raw sample rate

        Returns
        -------
        L_int : |np.ndarray| (..., n_time)
          The integral length scale (T_int*U_mag).

        Notes
        ----
        The integral time scale (T_int) is the lag-time at which the
        auto-covariance falls to 1/e.
        
        If T_int is not reached, L_int will default to '0'.

        """
        acov = a_cov.values
        fs = self._parse_fs(fs)
        
        scale = np.argmin((acov/acov[..., :1]) > (1/np.e), axis=-1)
        L_int = (abs(vel_avg) / fs * scale)
        
        return xr.DataArray(L_int, name='L_int', attrs={'units':'m'})
    
    
    # def calc_epsilon_SFz(self, vel_raw, vel_avg, r_range=[0,3], noise=0):
    #     """
    #     Calculate dissipation rate from ADCP beam velocity using the 
    #     "structure function" (SF) method.
        
    #     Parameters
    #     ----------
    #     vel_raw : |xr.DataArray|
    #       The raw beam velocity data (last dimension time) upon 
    #       which to perform the SF technique. 

    #     vel_avg : |xr.DataArray|
    #       The bin-averaged beam velocity (calc'd from 'do_avg')
                                          
    #     r_range: numeric
    #         Range of r in [m] to calc dissipation across
        
    #     noise: numeric
    #         Dopper noise level [m/s]
        
    #     Returns
    #     -------
    #     epsilon : |xr.DataArray|
    #       The dissipation rate
        
    #     Notes
    #     -----
    #     Velocity data should be cleaned of surface interference
        
    #     Wiles, et al, "A novel technique for measuring the rate of 
    #     turbulent dissipation in the marine environment"
    #     GRL, 2006, 33, L21608.
        
    #     """
    #     e = np.empty(vel_avg.shape, dtype='float32')*np.nan
    #     n = np.empty(vel_avg.shape, dtype='float32')*np.nan
        
    #     # bm shape is [range, ensemble time, 'data within ensemble']
    #     bm = self.reshape(vel_raw.values) # will fail if not in beam coord
    #     bm -= vel_avg.values[:,:,None] # take out the ensemble mean
        
    #     bin_size = round(np.diff(vel_raw.range)[0],3)
    #     #surface = np.count_nonzero(~np.isnan(vel_raw.isel(time_b5=0)))
    #     R = int(r_range[0]/bin_size)
    #     r = np.arange(bin_size, r_range[1], bin_size)
        
    #     D = np.zeros((vel_avg.shape[0], r.size, vel_avg.shape[1])) # D(z,r,time)
    #     for r_value in r:
    #         # the i in d is the index based on r and bin size
    #         # bin size index, > 1
    #         i = int(r_value/round(np.diff(vel_raw.range)[0],3))
    #         for idx in range(vel_avg.time.size): # for each ensemble
    #             # subtract the variance of adjacent depth cells
    #             d = np.nanmean((bm[:-i,idx,:] - bm[i:,idx,:]) ** 2, axis=-1)
                
    #             # have to insert 0/nan in first bin to match length
    #             spaces = np.empty((i,))
    #             spaces[:] = np.NaN
    #             D[:,i-1,idx] = np.concatenate((spaces, d))
                
    #     # find best fit line y = mx + b (aka D(z,r) = A*r^2/3 + N) to solve
    #     # epsilon for each depth and ensemble
    #     # only analyze r on "flat" part of curve (select r values)
    #     # plt.figure()
    #     for idx in range(vel_avg.time.size): # for each ensemble
    #         for i in range(D.shape[1],D.shape[0]): #for depth cells
    #             #plt.plot(r**2/3, D[i,:,100])
    #             try:
    #                 e[i,idx], n[i,idx] = np.polyfit(r[R:] ** 2/3, 
    #                                                 D[i, R:, idx], 
    #                                                 deg=1)
    #             except:
    #                 e[i,idx], n[i,idx] = np.nan, np.nan
    #     epsilon = (e/2.1)**(3/2)
        
    #     return xr.DataArray(epsilon, name='dissipation_rate',
    #                         coords=vel_avg.coords,
    #                         dims=vel_avg.dims,
    #                         attrs={'units':'m^2/s^3',
    #                               'method':'structure function'})


def calc_turbulence(ds_raw, n_bin, fs, n_fft=None, out_type=None,
                    omega_range_epsilon=[6.28, 12.57],
                    window='hann'):
    """
    Functional version of `TurbBinner` that computes a suite of turbulence 
    statistics for the input dataset, and returns a `binned` data object.

    Parameters
    ----------

    ds_raw : xarray.Dataset
      The raw adv datset to `bin`, average and compute
      turbulence statistics of.

    omega_range_epsilon : iterable(2)
      The frequency range (low, high) over which to estimate the
      dissipation rate `epsilon`, in units of [rad/s].

    window : 1, None, 'hann'
      The window to use for calculating power spectral densities

    Returns
    -------

    advb : xarray.Dataset
      Returns an 'binned' (i.e. 'averaged') data object. All
      fields (variables) of the input data object are averaged in n_bin
      chunks. This object also computes the following items over
      those chunks:

      - tke_vec : The energy in each component, each components is
        alternatively accessible as:
        :attr:`upup_ <dolfyn.data.velocity.TKE.upup_>`,
        :attr:`vpvp_ <dolfyn.data.velocity.TKE.vpvp_>`,
        :attr:`wpwp_ <dolfyn.data.velocity.TKE.wpwp_>`)

      - stress : The Reynolds stresses, each component is
        alternatively accessible as:
        :attr:`upwp_ <dolfyn.data.velocity.TKE.upwp_>`,
        :attr:`vpwp_ <dolfyn.data.velocity.TKE.vpwp_>`,
        :attr:`upvp_ <dolfyn.data.velocity.TKE.upvp_>`)

      - U_std : The standard deviation of the horizontal
        velocity `U_mag`.

      - S : DataArray containing the spectra of the velocity
        in radial frequency units. The data-array contains:
        - vel : the velocity spectra array (m^2/s/rad))
        - omega : the radial frequncy (rad/s)

    """
    calculator = TurbBinner(n_bin, fs, n_fft=n_fft)
    
    return calculator(ds_raw, out_type=out_type,
                      omega_range_epsilon=omega_range_epsilon,
                      window=window)
