import numpy as np
import xarray as xr
import warnings
from ..velocity import VelBinner
#import matplotlib.pyplot as plt


def _diffz_first(dat, z):
    return np.diff(dat, axis=0) / (np.diff(z)[:, None])


def _diffz_centered(dat, z):
    # Want top - bottom here (u_x+1 - u_x-1)/dx
    # Can use 2*np.diff b/c depth bin size never changes
    return (dat[2:]-dat[:-2]) / (2*np.diff(z)[1:, None])


class ADPBinner(VelBinner):
    def __init__(self, n_bin, fs, n_fft=None, n_fft_coh=None,
                 noise=0, orientation='up', diff_style='centered'):
        """
        A class for calculating turbulence statistics from ADCP data

        Parameters
        ----------
        n_bin : int
            Number of data points to include in a 'bin' (ensemble), not the
            number of bins
        fs : int
            Instrument sampling frequency in Hz
        n_fft : int
            Number of data points to use for fft (`n_fft`<=`n_bin`).
            Default: `n_fft`=`n_bin`
        n_fft_coh : int
            Number of data points to use for coherence and cross-spectra ffts
            Default: `n_fft_coh`=`n_fft`
        noise : float, list or numpy.ndarray
            Instrument's doppler noise in same units as velocity
        orientation : str, default='up'
            Instrument's orientation, either 'up' or 'down'
        diff_style : str, default='centered'
            Style of numerical differentiation using Newton's Method, 
            either 'first' or 'centered'

        """
        VelBinner.__init__(self, n_bin, fs, n_fft, n_fft_coh, noise)
        self.diff_style = diff_style
        self.orientation = orientation

    def __call___(self, ds, freq_units, freq_range,  window):
        out = type(ds)()
        out = self.do_avg(ds, out)

        # Calculate spectra and dissipation rate for each depth bin
        if hasattr(ds, 'vel_b5'):
            spec = [None]*len(ds.range)
            e = [None]*len(ds.range)
            for r in range(len(ds.range)):
                spec[r] = self.calc_psd(ds['vel_b5'].isel(range_b5=r),
                                        window=window,
                                        freq_units=freq_units)
                e[r] = self.calc_tke_dissipation(spec[r],
                                                 out.velds.U_mag.isel(range=r),
                                                 f_range=freq_range)

            out['auto_spectra_b5'] = xr.concat(spec, dim='range')
            dissipation_rate = xr.concat(e, dim='range')

        # Calculate doppler noise from spectra from mid-water column
        out['noise'] = self.calc_doppler_noise(
            out['auto_spectra'].isel(range=len(range)//2), pct_fN=0.8)

        # Calculate total turbulent kinetic energy with noise subtraction
        out['tke'] = self.calc_total_tke(
            ds, out, noise=out['noise'], orientation=self.orientation)

        # Remove TKE dissipation calculation where noise is greater than TKE signal
        out['dissipation_rate'] = dissipation_rate.where(out['tke'] > 0)

        out.attrs['n_bin'] = self.n_bin
        out.attrs['n_fft'] = self.n_fft
        out.attrs['n_fft_coh'] = self.n_fft_coh

        return out

    def _diff_func(self, vel, u):
        if self.diff_style == 'first':
            return _diffz_first(vel[u].values, vel['range'].values)
        elif self.diff_style == 'centered':
            return _diffz_centered(vel[u].values, vel['range'].values)

    def dudz(self, vel, orientation=None):
        """
        The shear in the first velocity component.

        Notes
        -----
        The derivative direction is along the profiler's 'z'
        coordinate ('dz' is actually diff(self['range'])), not necessarily the
        'true vertical' direction.

        """
        if not orientation:
            orientation = self.orientation
        sign = 1
        if orientation == 'down':
            sign *= -1
        return sign*self._diff_func(vel, 0)

    def dvdz(self, vel):
        """
        The shear in the second velocity component.

        Notes
        -----
        The derivative direction is along the profiler's 'z'
        coordinate ('dz' is actually diff(self['range'])), not necessarily the
        'true vertical' direction.

        """
        return self._diff_func(vel, 1)

    def dwdz(self, vel):
        """
        The shear in the third velocity component.

        Notes
        -----
        The derivative direction is along the profiler's 'z'
        coordinate ('dz' is actually diff(self['range'])), not necessarily the
        'true vertical' direction.

        """
        return self._diff_func(vel, 2)

    def tau2(self, vel):
        """
        The horizontal shear squared.

        Notes
        -----
        This is actually (dudz)^2 + (dvdz)^2. So, if those variables
        are not actually vertical derivatives of the horizontal
        velocity, then this is not the 'horizontal shear squared'.

        See Also
        --------
        :math:`dudz`, :math:`dvdz`

        """
        return self.dudz(vel) ** 2 + self.dvdz(vel) ** 2

    def calc_doppler_noise(self, psd, pct_fN=0.8):
        """
        Calculate bias due to Doppler noise using the noise floor
        of the velocity spectra.

        Parameters
        ----------
        psd : xarray.DataArray (time, f)
          The velocity spectra from a single depth bin (range), typically
          in the mid-water range
        pct_fN : float
          Percent of Nyquist frequency to calculate characeristic frequency

        Returns
        -------
        noise_level (xarray.DataArray): 
              Doppler noise level in units of m/s

        Notes
        -----
        Approximates bias from

        .. :math: \\sigma^{2}_{noise} = N x f_{c}

        where :math: `\\sigma_{noise}` is the bias due to Doppler noise,
        `N` is the constant variance or spectral density, and `f_{c}`
        is the characteristic frequency.

        The characteristic frequency is then found as 

        .. :math: f_{c} = pct_fN * (f_{s}/2)

        where `f_{s}/2` is the Nyquist frequency.


        Richard, Jean-Baptiste, et al. "Method for identification of Doppler noise 
        levels in turbulent flow measurements dedicated to tidal energy." International 
        Journal of Marine Energy 3 (2013): 52-64.

        Thiébaut, Maxime, et al. "Investigating the flow dynamics and turbulence at a 
        tidal-stream energy site in a highly energetic estuary." Renewable Energy 195 
        (2022): 252-262.

        """
        # Characteristic frequency set to 80% of Nyquist frequency
        fN = self.fs/2
        fc = pct_fN * fN

        # Get units right
        if psd.freq.units == "Hz":
            f_range = slice(fc, fN)
        else:
            f_range = slice(2*np.pi*fc, 2*np.pi*fN)

        # Noise floor
        N2 = psd.sel(freq=f_range) * psd.freq.sel(freq=f_range)
        noise_level = np.sqrt(N2.mean(dim='freq'))

        out = xr.DataArray(noise_level.values, name='noise_level',
                           dims=['time'],
                           attrs={'units': 'm/s',
                                  'description': 'Doppler noise level calculated \
                                                  from PSD white noise'})
        return out

    def calc_stress_4beam(self, ds, ds_avg, noise=0, orientation=None, beam_angle=25):
        """
        Calculate the stresses from the covariance of along-beam velocity measurements

        Parameters
        ----------
        ds : xarray.Dataset
          Raw dataset in beam coordinates
        ds_avg : xarray.Dataset
          Binned dataset in instrument reference frame
        noise : int or xarray.DataArray (time)
          Doppler noise level in units of m/s
        orientation : str, default=ds.orientation
          Direction ADCP is facing ('up' or 'down')
        beam_angle : int, default=25
          ADCP beam angle in units of degrees

        Returns
        -------
        stress_vec : xarray.DataArray(s)
          Stress vector with u'w'_ and v'w'_ components

        Notes
        -----
        Assumes zero mean pitch and roll.

        Assumes ADCP instrument coordinate system is aligned with principal flow
        directions.

        Stacey, Mark T., Stephen G. Monismith, and Jon R. Burau. "Measurements 
        of Reynolds stress profiles in unstratified tidal flow." Journal of 
        Geophysical Research: Oceans 104.C5 (1999): 10933-10949.

        """
        warnings.warn("The 4-beam stress equations assume the instrument's "
                      "(XYZ) coordinate system is aligned with the principal "
                      "flow directions.")
        if 'beam' not in ds.coord_sys:
            warnings.warn("Raw dataset must be in the 'beam' coordinate system. "
                          "Rotating raw dataset...")
            ds.velds.rotate2('beam')

        b_angle = getattr(ds, 'beam_angle', beam_angle)
        beam_vel = ds['vel'].values

        # Note: Stacey defines the beams for down-looking Workhorse ADCPs.
        #       According to the workhorse coordinate transformation
        #       documentation, the instrument's:
        #                        x-axis points from beam 1 to 2, and
        #                        y-axis points from beam 4 to 3.
        # Nortek Signature x-axis points from beam 3 to 1
        #                  y-axis points from beam 2 to 4
        if not orientation:
            orientation = ds.orientation
        if 'TRDI' in ds.inst_make:
            if 'down' in orientation.lower():
                # this order is correct given the note above
                beams = [0, 1, 2, 3]  # for down-facing RDIs
            elif 'up' in orientation.lower():
                beams = [0, 1, 3, 2]  # for up-facing RDIs
            else:
                raise Exception(
                    "Please provide instrument orientation ['up' or 'down']")

        # For Nortek Signatures
        elif 'Signature' in ds.inst_model:
            if 'down' in orientation.lower():
                beams = [2, 0, 3, 1]  # for down-facing Norteks
            elif 'up' in orientation.lower():
                beams = [0, 2, 3, 1]  # for up-facing Norteks
            else:
                raise Exception(
                    "Please provide instrument orientation ['up' or 'down']")

        # Calculate along-beam velocity prime squared bar
        bp2_ = np.empty((4, len(ds.range), len(ds_avg.time)))*np.nan
        for i, beam in enumerate(beams):
            bp2_[i] = np.nanvar(self.reshape(beam_vel[beam]), axis=-1)

        # Remove doppler_noise
        if type(noise) == type(ds_avg.vel):
            noise = noise.values
        bp2_ -= noise**2

        denm = 4 * np.sin(np.deg2rad(b_angle)) * np.cos(np.deg2rad(b_angle))
        upwp_ = (bp2_[0] - bp2_[1]) / denm
        vpwp_ = (bp2_[2] - bp2_[3]) / denm

        stress_vec = xr.DataArray(np.stack([upwp_*np.nan, upwp_, vpwp_]),
                                  coords={'tau': ["upvp_", "upwp_", "vpwp_"],
                                          'range': ds_avg.range,
                                          'time': ds_avg.time},
                                  attrs={'units': 'm^2/^2',
                                         'description': "Axes are aligned in "
                                         "instrument's (XYZ) frame of reference"})

        return stress_vec

    def calc_stress_5beam(self, ds, ds_avg, noise=0, orientation=None, beam_angle=25, tke_only=False):
        """
        Calculate the stresses from the covariance of along-beam velocity measurements

        Parameters
        ----------
        ds : xarray.Dataset
          Raw dataset in beam coordinates
        ds_avg : xarray.Dataset
          Binned dataset in final coordinate reference frame
        noise : int or xarray.DataArray, default=0 (time)
          Doppler noise level in units of m/s
        orientation : str, default=ds.orientation
          Direction ADCP is facing ('up' or 'down')
        beam_angle : int, default=25
          ADCP beam angle in units of degrees
        tke_only : bool, default=False

        Returns
        -------
        tke_vec(, stress_vec) : xarray.DataArray or tuple[xarray.DataArray]
          If tke_only is set to False, function returns `tke_vec` and `stress_vec`.
          Otherwise only `tke_vec` is returned

        Notes
        -----
        Assumes small-angle approximation is applicable.

        Assumes ADCP instrument coordinate system is aligned with principal flow
        directions.

        The stress equations here utilize u'v'_ to account for small variations
        in pitch and roll. u'v'_ cannot be directly calculated by a 5-beam ADCP,
        so it is approximated by the covariance of `u` and `v`. The uncertainty
        introduced by using this approximation is small if deviations from pitch
        and roll are small (<5-10 degrees).

        Dewey, R., and S. Stringer. "Reynolds stresses and turbulent kinetic
        energy estimates from various ADCP beam configurations: Theory." J. of
        Phys. Ocean (2007): 1-35.

        Guerra, Maricarmen, and Jim Thomson. "Turbulence measurements from 
        five-beam acoustic Doppler current profilers." Journal of Atmospheric 
        and Oceanic Technology 34.6 (2017): 1267-1284.

        """
        warnings.warn("The 5-beam TKE/stress equations assume the instrument's "
                      "(XYZ) coordinate system is aligned with the principal "
                      "flow directions.")
        if 'vel_b5' not in ds.data_vars:
            raise Exception("Must have 5th beam data")
        if 'beam' not in ds.coord_sys:
            warnings.warn("Raw dataset must be in the 'beam' coordinate system. "
                          "Rotating raw dataset...")
            ds.velds.rotate2('beam')

        b_angle = getattr(ds, 'beam_angle', beam_angle)
        beam_vel = np.concatenate((ds['vel'].values,
                                   ds['vel_b5'].values[None, ...]))

        if not orientation:
            orientation = ds.orientation
        # For TRDI Sentinel V
        if 'TRDI' in ds.inst_make:
            phi2 = np.deg2rad(ds['pitch'].values)
            phi3 = np.deg2rad(ds['roll'].values)

            if 'down' in orientation.lower():
                beams = [0, 1, 2, 3, 4]  # for down-facing RDIs
            elif 'up' in orientation.lower():
                beams = [0, 1, 3, 2, 4]  # for up-facing RDIs
            else:
                raise Exception(
                    "Please provide instrument orientation ['up' or 'down']")

        # For Nortek Signatures
        elif 'Signature' in ds.inst_model or 'AD2CP' in ds.inst_model:
            phi2 = np.deg2rad(self.mean(ds['roll'].values))
            phi3 = -np.deg2rad(self.mean(ds['pitch'].values))

            if 'down' in orientation.lower():
                beams = [2, 0, 3, 1, 4]  # for down-facing Norteks
            elif 'up' in orientation.lower():
                beams = [0, 2, 3, 1, 4]  # for up-facing Norteks
            else:
                raise Exception(
                    "Please provide instrument orientation ['up' or 'down']")

        # Calculate along-beam velocity prime squared bar
        bp2_ = np.empty((5, len(ds.range), len(phi2)))*np.nan
        for i, beam in enumerate(beams):
            bp2_[i] = np.nanvar(self.reshape(beam_vel[beam]), axis=-1)

        # Remove doppler_noise
        if type(noise) == type(ds_avg.vel):
            noise = noise.values
        bp2_ -= noise**2

        th = np.deg2rad(b_angle)
        sin = np.sin
        cos = np.cos
        denm = -4 * sin(th)**6 * cos(th)**2

        upup_ = (-2*sin(th)**4*cos(th)**2*(bp2_[1]+bp2_[0]-2*cos(th)**2*bp2_[4]) +
                 2*sin(th)**5*cos(th)*phi3*(bp2_[1]-bp2_[0])) / denm

        vpvp_ = (-2*sin(th)**4*cos(th)**2*(bp2_[3]+bp2_[0]-2*cos(th)**2*bp2_[4]) -
                 2*sin(th)**4*cos(th)**2*phi3*(bp2_[1]-bp2_[0]) +
                 2*sin(th)**3*cos(th)**3*phi3*(bp2_[1]-bp2_[0]) -
                 2*sin(th)**5*cos(th)*phi2*(bp2_[3]-bp2_[2])) / denm

        wpwp_ = (-2*sin(th)**5*cos(th) *
                 (bp2_[1]-bp2_[0] + 2*sin(th)**5*cos(th)*phi2*(bp2_[3]-bp2_[2]) -
                  4*sin(th)**6*cos(th)**2*bp2_[4])) / denm

        tke_vec = xr.DataArray(np.stack([upup_, vpvp_, wpwp_]),
                               coords={'tke': ["upup_", "vpvp_", "wpwp_"],
                                       'range': ds_avg.range,
                                       'time': ds_avg.time},
                               attrs={'units': 'm^2/^2',
                                      'description': "u', v' and w' are aligned to "
                                      "the instrument's (XYZ) frame of reference"})

        if tke_only:
            return tke_vec

        else:
            # Guerra Thomson calculate u'v' bar from from the covariance of u' and v'
            ds.velds.rotate2('inst')
            vel = self.detrend(ds.vel.values)
            upvp_ = np.nanmean(vel[0] * vel[1], axis=-1,
                               dtype=np.float64).astype(np.float32)

            upwp_ = (sin(th)**5*cos(th)*(bp2_[1]-bp2_[0]) +
                     2*sin(th)**4*cos(th)*2*phi3*(bp2_[1]+bp2_[0]) -
                     4*sin(th)**4*cos(th)*2*phi3*bp2_[4] -
                     4*sin(th)**6*cos(th)*2*phi2*upvp_) / denm

            vpwp_ = (sin(th)**5*cos(th)*(bp2_[3]-bp2_[2]) -
                     2*sin(th)**4*cos(th)*2*phi2*(bp2_[3]+bp2_[2]) +
                     4*sin(th)**4*cos(th)*2*phi2*bp2_[4] +
                     4*sin(th)**6*cos(th)*2*phi3*upvp_) / denm

            stress_vec = xr.DataArray(np.stack([upvp_, upwp_, vpwp_]),
                                      coords={'tau': ["upvp_", "upwp_", "vpwp_"],
                                              'range': ds_avg.range,
                                              'time': ds_avg.time},
                                      attrs={'units': 'm^2/^2',
                                      'description': "u', v' and w' are aligned to "
                                             "the instrument's (XYZ) frame of reference"})

            return tke_vec, stress_vec

    def calc_total_tke(self, ds, ds_avg, noise=0, orientation=None, beam_angle=25):
        """
        Calculate magnitude of turbulent kinetic energy from 5-beam ADCP. 

        Parameters
        ----------
        ds : xarray.Dataset
          Raw dataset in beam coordinates
        ds_avg : xarray.Dataset
          Binned dataset in final coordinate reference frame
        noise : int or xarray.DataArray, default=0 (time)
          Doppler noise level in units of m/s
        orientation : str, default=ds.orientation
          Direction ADCP is facing ('up' or 'down')
        beam_angle : int, default=25
          ADCP beam angle in units of degrees

        Returns
        -------
        tke :
          Turbulent kinetic energy magnitude

        Notes
        -----
        This function is a wrapper around 'calc_stress_5beam' that then
        combines the TKE components

        """
        tke_vec = self.calc_stress_5beam(
            ds, ds_avg, noise, orientation, beam_angle, tke_only=True)

        tke = tke_vec.sum('tke') / 2
        tke.attrs['units'] = 'm^2/s^2'

        return tke

    def calc_tke_dissipation(self, psd, U_mag, freq_range=[0.2, 0.4]):
        """
        Calculate the TKE dissipation rate from the velocity spectra.

        Parameters
        ----------
        psd : xarray.DataArray (time,f)
          The power spectral density from a single depth bin (range)
        U_mag : xarray.DataArray (time)
          The bin-averaged horizontal velocity (a.k.a. speed)
        noise : int or xarray.DataArray, default=0 (time)
          Doppler noise level in units of m/s
        f_range : iterable(2)
          The range over which to integrate/average the spectrum, in units 
          of the psd frequency vector (Hz or rad/s)

        Returns
        -------
        dissipation_rate : xarray.DataArray (...,n_time)
          Turbulent kinetic energy dissipation rate

        Notes
        -----
        This uses the `standard` formula for dissipation:

        .. math:: S(k) = \\alpha \\epsilon^{2/3} k^{-5/3} + N

        where :math:`\\alpha = 0.5` (1.5 for all three velocity
        components), `k` is wavenumber, `S(k)` is the turbulent
        kinetic energy spectrum, and `N' is the doppler noise level
        associated with the TKE spectrum.

        With :math:`k \\rightarrow \\omega / U`, then -- to preserve variance --
        :math:`S(k) = U S(\\omega)`, and so this becomes:

        .. math:: S(\\omega) = \\alpha \\epsilon^{2/3} \\omega^{-5/3} U^{2/3} + N

        With :math:`k \\rightarrow (2\\pi f) / U`, then

        .. math:: S(\\omega) = \\alpha \\epsilon^{2/3} f^{-5/3} (U/(2*\\pi))^{2/3} + N

        LT83 : Lumley and Terray, "Kinematics of turbulence convected
        by a random wave field". JPO, 1983, vol13, pp2000-2007.

        """
        freq = psd.freq
        idx = np.where((freq_range[0] < freq) & (freq < freq_range[1]))
        idx = idx[0]

        if freq.units == 'Hz':
            U = U_mag/(2*np.pi)
        else:
            U = U_mag

        a = 0.5
        out = (psd[:, idx] * freq[idx]**(5/3) /
               a).mean(axis=-1)**(3/2) / U.values

        out = xr.DataArray(out, name='dissipation_rate',
                           attrs={'units': 'm^2/s^3',
                                  'description': 'TKE dissipation rate'})
        return out

    # def calc_epsilon_SFz(self, vel_raw, vel_avg, r_range=[0.1, 5]):
    #     """
    #     Calculate dissipation rate from ADCP beam velocity using the
    #     "structure function" (SF) method.

    #     Parameters
    #     ----------
    #     vel_raw : xarray.DataArray
    #       The raw beam velocity data (one beam, last dimension time) upon
    #       which to perform the SF technique.
    #     vel_avg : xarray.DataArray
    #       The ensemble-averaged beam velocity (calc'd from 'do_avg')

    #     r_range: numeric
    #         Range of r in [m] to calc dissipation across. Low end of range should be
    #         bin size, upper end of range is limited to the length of largest eddies
    #         in the inertial subrange.

    #     Returns
    #     -------
    #     epsilon : xarray.DataArray
    #       The dissipation rate

    #     Notes
    #     -----
    #     Velocity data should be cleaned of surface interference

    #     Wiles, et al, "A novel technique for measuring the rate of
    #     turbulent dissipation in the marine environment"
    #     GRL, 2006, 33, L21608.

    #     """
    #     if type(vel_raw.dir) == list:
    #         raise Exception(
    #             "Function input must be single beam and in 'beam' coordinate system")
    #     if type(vel_raw.dir) == str:
    #         raise Exception("Data must be in 'beam' coordinate system")

    #     e = np.empty(vel_avg.shape, dtype='float32')*np.nan
    #     n = np.empty(vel_avg.shape, dtype='float32')*np.nan

    #     # bm shape is [range, ensemble time, 'data within ensemble']
    #     bm = self.reshape(vel_raw.values)  # will fail if not in beam coord
    #     bm -= vel_avg.values[:, :, None]  # take out the ensemble mean

    #     bin_size = round(np.diff(vel_raw.range)[0], 3)
    #     #surface = np.count_nonzero(~np.isnan(vel_raw.isel(time_b5=0)))
    #     R = int(r_range[0]/bin_size)
    #     r = np.arange(bin_size, r_range[1]+bin_size, bin_size)

    #     # D(z,r,time)
    #     D = np.zeros((vel_avg.shape[0], r.size, vel_avg.shape[1]))
    #     for r_value in r:
    #         # the i in d is the index based on r and bin size
    #         # bin size index, > 1
    #         i = int(r_value/bin_size)
    #         for idx in range(vel_avg.shape[-1]):  # for each ensemble
    #             # subtract the variance of adjacent depth cells
    #             d = np.nanmean(
    #                 (bm[:-i, idx, :] - bm[i:, idx, :]) ** 2, axis=-1)

    #             # have to insert 0/nan in first bin to match length
    #             spaces = np.empty((i,))
    #             spaces[:] = np.NaN
    #             D[:, i-1, idx] = np.concatenate((spaces, d))

    #     # find best fit line y = mx + b (aka D(z,r) = A*r^2/3 + N) to solve
    #     # epsilon for each depth and ensemble
    #     plt.figure()
    #     for idx in range(vel_avg.shape[-1]):  # for each ensemble
    #         for i in range(D.shape[1], D.shape[0]):  # for depth cells
    #             plt.plot(r, D[i, :, 100])  # randomly choose 100th ensemble
    #             try:
    #                 e[i, idx], n[i, idx] = np.polyfit(r[R:] ** 2/3,
    #                                                   D[i, R:, idx],
    #                                                   deg=1)
    #             except:
    #                 e[i, idx], n[i, idx] = np.nan, np.nan
    #     # A taken as 2.1, n = y-intercept
    #     epsilon = (e/2.1)**(3/2)
    #     plt.yscale('log')
    #     plt.ylabel('D [m2/s2]')
    #     plt.xlabel('r [m]')
    #     plt.show()

    #     return xr.DataArray(epsilon, name='dissipation_rate',
    #                         coords=vel_avg.coords,
    #                         dims=vel_avg.dims,
    #                         attrs={'units': 'm^2/s^3',
    #                                'method': 'structure function'})

    def calc_ustar_fit(self, ds_avg, z_inds=slice(1, 5), H=None):
        """
        Approximate friction velocity from shear stress using a 
        log profile

        Parameters
        ----------
        ds_avg : xarray.Dataset
          Bin-averaged dataset containing `stress_vec`
        z_inds : slice(int,int)
          Depth indices to use for profile
        H : int (default=`ds_avg.depth`)
          Total water depth

        Returns
        -------
        ustar : xarray.DataArray

        """
        if not H:
            H = ds_avg.depth.values
        z = ds_avg['range'].values
        upwp_ = ds_avg['stress_vec'].sel(tau='upwp_').values

        sign = np.nanmean(np.sign(upwp_[z_inds, :]), axis=0)
        ustar = np.nanmean(sign * upwp_[z_inds, :] /
                           (1 - z[z_inds, None] / H), axis=0) ** 0.5

        out = xr.DataArray(ustar,
                           coords={'time': ds_avg.time},
                           attrs={'units': 'm/s',
                                  'description': 'Friction velocity'})

        return out


def calc_turbulence(ds_raw, n_bin, fs, n_fft=None, noise=0, freq_units='Hz', freq_range=[0.1, 0.3], window='hann'):
    """
    Functional version of `ADPBinner` that computes a suite of turbulence
    statistics for the input dataset, and returns a `binned` data object.

    Parameters
    ----------
    ds : xarray.Dataset
      The raw adv datset to `bin`, average and compute
      turbulence statistics of.
    freq_units : str
      Frequency units of the returned spectra in either Hz or rad/s 
    frequency_range : iterable
      Frequency range over which to integrate/average the spectrum 
      to calculate TKE dissipation, in Hz
    window : 1, None, 'hann', 'hamm'
      The window to use for calculating power spectral densities

    Returns
    -------
    ds : xarray.Dataset
      Returns an 'binned' (i.e. 'averaged') data object. All
      fields (variables) of the input data object are averaged in n_bin
      chunks. This object also computes the following items over
      those chunks:

      - auto_spectra : DataArray containing the auto-spectra of 
        the vertical (5th beam) along-beam velocity for all depth bins

      - dissipation : DataArray containing the TKE dissipation 
        rate for all depth bins

      - noise : DataArray containing the doppler noise level from 
        the mid-water column

    """
    calculator = ADPBinner(n_bin, fs, n_fft=n_fft, noise=noise)

    return calculator(ds_raw, freq_units=freq_units, freq_range=freq_range, window=window)
