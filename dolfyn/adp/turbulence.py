import numpy as np
import xarray as xr
import warnings

from ..velocity import VelBinner
from ..rotate.base import calc_tilt


def _diffz_first(dat, z):
    return np.diff(dat, axis=0) / (np.diff(z)[:, None])


def _diffz_centered(dat, z):
    # Want top - bottom here (u_x+1 - u_x-1)/dx
    # Can use 2*np.diff b/c depth bin size never changes
    return (dat[2:]-dat[:-2]) / (2*np.diff(z)[1:, None])


class ADPBinner(VelBinner):
    def __init__(self, n_bin, fs, n_fft=None, n_fft_coh=None,
                 noise=None, orientation='up', diff_style='centered'):
        """A class for calculating turbulence statistics from ADCP data

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

    def _diff_func(self, vel, u):
        if self.diff_style == 'first':
            out = _diffz_first(vel[u].values, vel['range'].values)
            return out, vel.range[1:]
        elif self.diff_style == 'centered':
            out = _diffz_centered(vel[u].values, vel['range'].values)
            return out, vel.range[1:-1]

    def calc_dudz(self, vel, orientation=None):
        """The shear in the first velocity component.

        Parameters
        ----------
        vel : xarray.DataArray
          ADCP raw velocity
        orientation : str, default=ADPBinner.orientation
          Direction ADCP is facing ('up' or 'down')

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

        dudz, rng = sign*self._diff_func(vel, 0)
        return xr.DataArray(dudz,
                            coords=[rng, vel.time],
                            dims=['range', 'time'],
                            attrs={'units': 's-1',
                                   'long_name': 'Shear in X-direction',
                                   'standard_name': 'x_sea_water_shear'}
                            )

    def calc_dvdz(self, vel):
        """The shear in the second velocity component.

        Parameters
        ----------
        vel : xarray.DataArray
          ADCP raw velocity

        Notes
        -----
        The derivative direction is along the profiler's 'z'
        coordinate ('dz' is actually diff(self['range'])), not necessarily the
        'true vertical' direction.
        """

        dvdz, rng = self._diff_func(vel, 1)
        return xr.DataArray(dvdz,
                            coords=[rng, vel.time],
                            dims=['range', 'time'],
                            attrs={'units': 's-1',
                                   'long_name': 'Shear in Y-direction',
                                   'standard_name': 'y_sea_water_shear'}
                            )

    def calc_dwdz(self, vel):
        """The shear in the third velocity component.

        Parameters
        ----------
        vel : xarray.DataArray
          ADCP raw velocity

        Notes
        -----
        The derivative direction is along the profiler's 'z'
        coordinate ('dz' is actually diff(self['range'])), not necessarily the
        'true vertical' direction.
        """

        dwdz, rng = self._diff_func(vel, 2)
        return xr.DataArray(dwdz,
                            coords=[rng, vel.time],
                            dims=['range', 'time'],
                            attrs={'units': 's-1',
                                   'long_name': 'Shear in Z-direction',
                                   'standard_name': 'z_sea_water_shear'}
                            )

    def calc_shear2(self, vel):
        """The horizontal shear squared.

        Parameters
        ----------
        vel : xarray.DataArray
          ADCP raw velocity

        Notes
        -----
        This is actually (dudz)^2 + (dvdz)^2. So, if those variables
        are not actually vertical derivatives of the horizontal
        velocity, then this is not the 'horizontal shear squared'.

        See Also
        --------
        :math:`dudz`, :math:`dvdz`
        """

        shear2 = self.calc_dudz(vel) ** 2 + self.calc_dvdz(vel) ** 2
        shear2.attrs['units'] = 's-2'
        shear2.attrs['long_name'] = 'Horizontal Shear Squared'
        shear2.attrs['standard_name'] = 'radial_sea_water_shear_squared'

        return shear2

    def calc_doppler_noise(self, psd, pct_fN=0.8):
        """Calculate bias due to Doppler noise using the noise floor
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
        doppler_noise (xarray.DataArray): 
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

        if len(psd.shape) != 2:
            raise Exception('PSD should be 2-dimensional (time, frequency)')

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

        return xr.DataArray(
            noise_level.values.astype('float32'),
            dims=['time'],
            attrs={'units': 'm s-1',
                   'long_name': 'Doppler Noise Level',
                   'description': 'Doppler noise level calculated '
                   'from PSD white noise'})

    def _stress_func_warnings(self, ds, beam_angle, noise, tilt_thresh):
        """List of error and warnings to run through for ADCP stress calculations.
        """
        # Error 1. Beam Angle
        b_angle = getattr(ds, 'beam_angle', beam_angle)
        if b_angle is None:
            raise Exception(
                "    Beam angle not found in dataset and no beam angle supplied.")

        # Warning 1. Memo
        warnings.warn("    The 4-beam stress equations assume the instrument's "
                      "(XYZ) coordinate system is aligned with the principal "
                      "flow directions.")

        # Warning 2. Check tilt
        if any(abs(calc_tilt(ds['pitch'], ds['roll']))) < tilt_thresh:
            warnings.warn(f"    Instrument tilt is greater than {tilt_thresh} degrees."
                          "Stress axes won't be well aligned with flow.")

        # Warning 3. Noise level of instrument is important considering 50 % of variance
        # in ADCP data can be noise
        if noise is None:
            warnings.warn('    No "noise" input supplied. Consider calculating "noise" '
                          'using `calc_doppler_noise`')
            noise = 0

        # Warning 4. Likely not in beam coordinates after running a typical analysis workflow
        if 'beam' not in ds.coord_sys:
            warnings.warn("    Raw dataset must be in the 'beam' coordinate system. "
                          "Rotating raw dataset...")
            ds.velds.rotate2('beam')

        return b_angle, noise

    def _check_orientation(self, ds, orientation, beam5=False):
        """Get the beam order for the beam-stress rotation algorithm

        Note: Stacey defines the beams for down-looking Workhorse ADCPs.
              According to the workhorse coordinate transformation
              documentation, the instrument's:
                               x-axis points from beam 1 to 2, and
                               y-axis points from beam 4 to 3.
        Nortek Signature x-axis points from beam 3 to 1
                         y-axis points from beam 2 to 4
        """

        if orientation is None:
            orientation = getattr(ds, 'orientation', self.orientation)

        if 'TRDI' in ds.inst_make:
            phi2 = np.deg2rad(self.mean(ds['pitch'].values))
            phi3 = np.deg2rad(self.mean(ds['roll'].values))
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
            phi2 = np.deg2rad(self.mean(ds['roll'].values))
            phi3 = -np.deg2rad(self.mean(ds['pitch'].values))
            if 'down' in orientation.lower():
                beams = [2, 0, 3, 1]  # for down-facing Norteks
            elif 'up' in orientation.lower():
                beams = [0, 2, 3, 1]  # for up-facing Norteks
            else:
                raise Exception(
                    "Please provide instrument orientation ['up' or 'down']")

        if beam5:
            beams.append(4)
            return beams, phi2, phi3
        else:
            return beams

    def _beam_variance(self, ds, time, noise, beam_order, n_beams):
        """Calculate along-beam velocity variance and subtract noise
        """
        # Concatenate 5th beam velocity if need be
        if n_beams == 4:
            beam_vel = ds['vel'].values
        elif n_beams == 5:
            beam_vel = np.concatenate((ds['vel'].values,
                                       ds['vel_b5'].values[None, ...]))

        # Calculate along-beam velocity prime squared bar
        bp2_ = np.empty((n_beams, len(ds.range), len(time)))*np.nan
        for i, beam in enumerate(beam_order):
            bp2_[i] = np.nanvar(self.reshape(beam_vel[beam]), axis=-1)

        # Remove doppler_noise
        if type(noise) == type(ds.vel):
            noise = noise.values
        bp2_ -= noise**2

        return bp2_

    def calc_stress_4beam(self, ds, noise=None, orientation=None, beam_angle=None):
        """Calculate the stresses from the covariance of along-beam 
        velocity measurements

        Parameters
        ----------
        ds : xarray.Dataset
          Raw dataset in beam coordinates
        noise : int or xarray.DataArray (time)
          Doppler noise level in units of m/s
        orientation : str, default=ds.attrs['orientation']
          Direction ADCP is facing ('up' or 'down')
        beam_angle : int, default=ds.attrs['beam_angle']
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
        # Run through warnings
        b_angle, noise = self._stress_func_warnings(
            ds, beam_angle, noise, tilt_thresh=5)

        # Fetch beam order
        beam_order = self._check_orientation(ds, orientation, beam5=False)

        # Calculate beam variance and subtract noise
        time = self.mean(ds['time'].values)
        bp2_ = self._beam_variance(ds, time, noise, beam_order, n_beams=4)

        # Run stress calculations
        denm = 4 * np.sin(np.deg2rad(b_angle)) * np.cos(np.deg2rad(b_angle))
        upwp_ = (bp2_[0] - bp2_[1]) / denm
        vpwp_ = (bp2_[2] - bp2_[3]) / denm

        return xr.DataArray(
            np.stack([upwp_*np.nan, upwp_, vpwp_]).astype('float32'),
            coords={'tau': ["upvp_", "upwp_", "vpwp_"],
                    'range': ds.range,
                    'time': time},
            attrs={'units': 'm2 s-2',
                   'long_name': 'Reynolds Stress Vector',
                   'standard_name': 'specific_reynolds_stress_of_sea_water'})

    def calc_stress_5beam(self, ds, noise=None, orientation=None, beam_angle=None, tke_only=False):
        """Calculate the stresses from the covariance of along-beam 
        velocity measurements

        Parameters
        ----------
        ds : xarray.Dataset
          Raw dataset in beam coordinates
        noise : int or xarray.DataArray, default=0 (time)
          Doppler noise level in units of m/s
        orientation : str, default=ds.attrs['orientation']
          Direction ADCP is facing ('up' or 'down')
        beam_angle : int, default=ds.attrs['beam_angle']
          ADCP beam angle in units of degrees
        tke_only : bool, default=False
          If true, only calculates tke components

        Returns
        -------
        tke_vec(, stress_vec) : xarray.DataArray or tuple[xarray.DataArray]
          If tke_only is set to False, function returns `tke_vec` and `stress_vec`.
          Otherwise only `tke_vec` is returned

        Notes
        -----
        Assumes small-angle approximation is applicable.

        Assumes ADCP instrument coordinate system is aligned with principal flow
        directions, i.e. u', v' and w' are aligned to the instrument's (XYZ) 
        frame of reference.

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
        # Check that beam 5 velocity exists
        if 'vel_b5' not in ds.data_vars:
            raise Exception("Must have 5th beam data to use this function.")

        # Run through warnings
        b_angle, noise = self._stress_func_warnings(
            ds, beam_angle, noise, tilt_thresh=5)

        # Fetch beam order
        beam_order, phi2, phi3 = self._check_orientation(
            ds, orientation, beam5=True)

        # Calculate beam variance and subtract noise
        time = self.mean(ds['time'].values)
        bp2_ = self._beam_variance(ds, time, noise, beam_order, n_beams=5)

        # Run tke and stress calculations
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

        tke_vec = xr.DataArray(
            np.stack([upup_, vpvp_, wpwp_]).astype('float32'),
            coords={'tke': ["upup_", "vpvp_", "wpwp_"],
                    'range': ds.range,
                    'time': time},
            attrs={'units': 'm2 s-2',
                   'long_name': 'TKE Vector',
                   'standard_name': 'specific_turbulent_kinetic_energy_of_sea_water'})

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

            stress_vec = xr.DataArray(
                np.stack([upvp_, upwp_, vpwp_]).astype('float32'),
                coords={'tau': ["upvp_", "upwp_", "vpwp_"],
                        'range': ds.range,
                        'time': time},
                attrs={'units': 'm2 s-2',
                       'long_name': 'Reynolds Stress Vector',
                       'standard_name': 'specific_reynolds_stress_of_sea_water'})

            return tke_vec, stress_vec

    def calc_total_tke(self, ds, noise=None, orientation=None, beam_angle=None):
        """Calculate magnitude of turbulent kinetic energy from 5-beam ADCP. 

        Parameters
        ----------
        ds : xarray.Dataset
          Raw dataset in beam coordinates
        ds_avg : xarray.Dataset
          Binned dataset in final coordinate reference frame
        noise : int or xarray.DataArray, default=0 (time)
          Doppler noise level in units of m/s
        orientation : str, default=ds.attrs['orientation']
          Direction ADCP is facing ('up' or 'down')
        beam_angle : int, default=ds.attrs['beam_angle']
          ADCP beam angle in units of degrees

        Returns
        -------
        tke : xarray.DataArray
          Turbulent kinetic energy magnitude

        Notes
        -----
        This function is a wrapper around 'calc_stress_5beam' that then
        combines the TKE components
        """

        tke_vec = self.calc_stress_5beam(
            ds, noise, orientation, beam_angle, tke_only=True)

        tke = tke_vec.sum('tke') / 2
        tke.attrs['units'] = 'm2 s-2'
        tke.attrs['long_name'] = 'TKE Magnitude',
        tke.attrs['standard_name'] = 'specific_turbulent_kinetic_energy_of_sea_water'

        return tke.astype('float32')

    def calc_dissipation_LT83(self, psd, U_mag, freq_range=[0.2, 0.4]):
        """Calculate the TKE dissipation rate from the velocity spectra.

        Parameters
        ----------
        psd : xarray.DataArray (time,f)
          The power spectral density from a single depth bin (range)
        U_mag : xarray.DataArray (time)
          The bin-averaged horizontal velocity (a.k.a. speed) from a single depth bin (range)
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

        if len(psd.shape) != 2:
            raise Exception('PSD should be 2-dimensional (time, frequency)')
        if len(U_mag.shape) != 1:
            raise Exception('U_mag should be 1-dimensional (time)')

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

        return xr.DataArray(
            out.astype('float32'),
            attrs={'units': 'm2 s-3',
                   'long_name': 'Dissipation Rate',
                   'standard_name': 'specific_turbulent_kinetic_energy_dissipation_in_sea_water',
                   'description': 'TKE dissipation rate calculated using the method from Lumley and Terray, 1983'
                   })

    def calc_dissipation_SF(self, vel_raw, r_range=[1, 5]):
        """Calculate TKE dissipation rate from ADCP along-beam velocity using the
        "structure function" (SF) method.

        Parameters
        ----------
        vel_raw : xarray.DataArray
          The raw beam velocity data (one beam, last dimension time) upon
          which to perform the SF technique.
        r_range : numeric, default=[1,5]
          Range of r in [m] to calc dissipation across. Low end of range should be
          bin size, upper end of range is limited to the length of largest eddies
          in the inertial subrange.

        Returns
        -------
        dissipation_rate : xarray.DataArray (range, time)
          Dissipation rate estimated from the structure function
        noise : xarray.DataArray (range, time)
          Noise offset estimated from the structure function at r = 0
        structure_function : xarray.DataArray (range, r, time)
          Structure function D(z,r)

        Notes
        -----
        Dissipation rate outputted by this function is only valid if the isotropic 
        turbulence cascade can be seen in the TKE spectra. 

        Velocity data must be in beam coordinates and should be cleaned of surface 
        interference.

        This method calculates the 2nd order structure function:

        .. math:: D(z,r) = [(u'(z) - u`(z+r))^2]

        where `u'` is the velocity fluctuation `z` is the depth bin, 
        `r` is the separation between depth bins, and [] denotes a time average 
        (size 'ADPBinner.n_bin').

        The stucture function can then be used to estimate the dissipation rate:

        .. math:: D(z,r) = C^2 \\epsilon^{2/3} r^{2/3} + N

        where `C` is a constant (set to 2.1), `\\epsilon` is the dissipation rate,
        and `N` is the offset due to noise. Noise is then calculated by

        .. math:: \\sigma = (N/2)^{1/2}

        Wiles, et al, "A novel technique for measuring the rate of
        turbulent dissipation in the marine environment"
        GRL, 2006, 33, L21608.
        """

        if len(vel_raw.shape) != 2:
            raise Exception(
                "Function input must be single beam and in 'beam' coordinate system")

        if 'range_b5' in vel_raw.dims:
            rng = vel_raw.range_b5
            time = self.mean(vel_raw.time_b5.values)
        else:
            rng = vel_raw.range
            time = self.mean(vel_raw.time.values)

        # bm shape is [range, ensemble time, 'data within ensemble']
        bm = self.demean(vel_raw.values)  # take out the ensemble mean

        e = np.empty(bm.shape[:2], dtype='float32')*np.nan
        n = np.empty(bm.shape[:2], dtype='float32')*np.nan

        bin_size = round(np.diff(rng)[0], 3)
        R = int(r_range[0]/bin_size)
        r = np.arange(bin_size, r_range[1]+bin_size, bin_size)

        # D(z,r,time)
        D = np.zeros((bm.shape[0], r.size, bm.shape[1]))
        for r_value in r:
            # the i in d is the index based on r and bin size
            # bin size index, > 1
            i = int(r_value/bin_size)
            for idx in range(bm.shape[1]):  # for each ensemble
                # subtract the variance of adjacent depth cells
                d = np.nanmean(
                    (bm[:-i, idx, :] - bm[i:, idx, :]) ** 2, axis=-1)

                # have to insert 0/nan in first bin to match length
                spaces = np.empty((i,))
                spaces[:] = np.NaN
                D[:, i-1, idx] = np.concatenate((spaces, d))

        # find best fit line y = mx + b (aka D(z,r) = A*r^2/3 + N) to solve
        # epsilon for each depth and ensemble
        for idx in range(bm.shape[1]):  # for each ensemble
            # start at minimum r_range and work up to surface
            for i in range(D.shape[1], D.shape[0]):
                # average ensembles together
                if not all(np.isnan(D[i, R:, idx])):  # if no nan's
                    e[i, idx], n[i, idx] = np.polyfit(r[R:] ** 2/3,
                                                      D[i, R:, idx],
                                                      deg=1)
                else:
                    e[i, idx], n[i, idx] = np.nan, np.nan
        # A taken as 2.1, n = y-intercept
        epsilon = (e/2.1)**(3/2)
        noise = np.sqrt(n/2)

        epsilon = xr.DataArray(
            epsilon.astype('float32'),
            coords={vel_raw.dims[0]: rng,
                    vel_raw.dims[1]: time},
            dims=vel_raw.dims,
            attrs={'units': 'm2 s-3',
                   'long_name': 'Dissipation Rate',
                   'standard_name': 'specific_turbulent_kinetic_energy_dissipation_in_sea_water'})

        noise = xr.DataArray(
            noise.astype('float32'),
            coords={vel_raw.dims[0]: rng,
                    vel_raw.dims[1]: time},
            attrs={'units': 'm s-1',
                   'long_name': 'Structure Function Noise Offset',
                   'standard_name': 'structure_function_offset_due_to_instrument_noise'})

        SF = xr.DataArray(
            D.astype('float32'),
            coords={vel_raw.dims[0]: rng,
                    'range_SF': r,
                    vel_raw.dims[1]: time},
            attrs={'units': 'm2 s-2',
                   'long_name': 'Structure Function D(z,r)',
                   'standard_name': 'specific_turbulent_kinetic_energy_structure_function_in_sea_water',
                   'description': 'TKE dissipation rate "structure function" from Wiles et al, 2006.'
                   })

        return epsilon, noise, SF

    def calc_ustar_fit(self, ds_avg, upwp_, z_inds=slice(1, 5), H=None):
        """Approximate friction velocity from shear stress using a 
        logarithmic profile.

        Parameters
        ----------
        ds_avg : xarray.Dataset
          Bin-averaged dataset containing `stress_vec`
        upwp_ : xarray.DataArray
          First component of Reynolds shear stress vector, "u-prime v-prime bar"
          Ex `ds_avg['stress_vec'].sel(tau='upwp_')`
        z_inds : slice(int,int)
          Depth indices to use for profile. Default = slice(1, 5)
        H : int (default=`ds_avg.depth`)
          Total water depth

        Returns
        -------
        u_star : xarray.DataArray
          Friction velocity
        """

        if not H:
            H = ds_avg.depth.values
        z = ds_avg['range'].values
        upwp_ = upwp_.values

        sign = np.nanmean(np.sign(upwp_[z_inds, :]), axis=0)
        u_star = np.nanmean(sign * upwp_[z_inds, :] /
                            (1 - z[z_inds, None] / H), axis=0) ** 0.5

        return xr.DataArray(
            u_star.astype('float32'),
            coords={'time': ds_avg.time},
            attrs={'units': 'm s-1',
                   'long_name': 'Friction Velocity',
                   'standard_name': 'x_friction_velocity_in_sea_water'})
