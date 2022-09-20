import numpy as np
import xarray as xr
import warnings
from ..rotate import rdi, signature
from ..rotate.vector import _earth2principal
from ..velocity import VelBinner
#import matplotlib.pyplot as plt


def _diffz_first(dat, z, axis=0):
    return np.diff(dat, axis=0) / (np.diff(z)[:, None])


def _diffz_centered(dat, z, axis=0):
    # Want top - bottom here (u_x+1 - u_x-1)/dx
    # Can use 2*np.diff b/c depth bin size never changes
    return (dat[2:, ...]-dat[:-2, ...]) / (2*np.diff(z)[1:, None])


class ADPBinner(VelBinner):
    """A class for calculating turbulence statistics from ADCP data
    """

    def __call___(self, ds, diff_func='centered', window='hann', doppler_noise=0):
        self.nm = ds
        self.diff_style = diff_func

        out = type(ds)()
        out = self.do_avg(ds, out)

        if hasattr(ds, 'vel_b5'):
            out['auto_spectra_b5'] = self.calc_psd(ds['vel_b5'].isel(range=5),
                                                   window=window,
                                                   freq_units='rad/s',
                                                   noise=doppler_noise)

            out['tke_b5'] = self.calc_tke(ds['vel_b5'], noise=doppler_noise)

        out.attrs['n_bin'] = self.n_bin
        out.attrs['n_fft'] = self.n_fft
        out.attrs['n_fft_coh'] = self.n_fft_coh

        return out

    def _diff_func(self, nm):
        if self.diff_style == 'first':
            return _diffz_first(getattr(self, nm), self['range'])
        else:
            return _diffz_centered(getattr(self, nm), self['range'])

    @property
    def dudz(self):
        """The shear in the first velocity component.

        Notes
        -----
        The derivative direction is along the profiler's 'z'
        coordinate ('dz' is actually diff(self['range'])), not necessarily the
        'true vertical' direction.

        """
        return self._diff_func('u')

    @property
    def dvdz(self):
        """The shear in the second velocity component.

        Notes
        -----
        The derivative direction is along the profiler's 'z'
        coordinate ('dz' is actually diff(self['range'])), not necessarily the
        'true vertical' direction.

        """
        return self._diff_func('v')

    @property
    def dwdz(self):
        """The shear in the third velocity component.

        Notes
        -----
        The derivative direction is along the profiler's 'z'
        coordinate ('dz' is actually diff(self['range'])), not necessarily the
        'true vertical' direction.

        """
        return self._diff_func('w')

    @property
    def tau2(self):
        """The horizontal shear squared.

        Notes
        -----
        This is actually (dudz)^2 + (dvdz)^2. So, if those variables
        are not actually vertical derivatives of the horizontal
        velocity, then this is not the 'horizontal shear squared'.

        See Also
        --------
        :math:`dudz`, :math:`dvdz`

        """
        return self.dudz ** 2 + self.dvdz ** 2

    def calc_ustar_fit(self, ds_avg, d_inds=slice(None), H=None):
        """
        Approximate friction velocity from shear stress

        Parameters
        ----------
        ds : xarray.Dataset
        d_inds :
            depth indices to use
        H : int
            water depth

        """
        if not H:
            H = self.mean(ds_avg.depth.values)
        z = ds_avg['range'].values
        upwp_ = ds_avg['stress_vec'].sel(tau='upwp_').values

        sign = np.nanmean(np.sign(upwp_[d_inds, :]), axis=0)
        ustar = np.nanmean(sign * upwp_[d_inds, :] /
                           (1 - z[d_inds, None] / H[None, :]), axis=0) ** 0.5

        return ustar

    def calc_doppler_noise(self, psd, pct_fN=0.8):
        """Calculate bias due to Doppler noise from the spectral noise floor

        Parameters
        ----------
        psd (xarray.DataArray): 
            Power spectral density with dimensions of frequency and time
        pct_fN (float):
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
        fc = pct_fN * (self.fs/2)

        # Get units right
        if psd.freq.units == "Hz":
            f_range = slice(fc, self.fs)
        else:
            f_range = slice(2*np.pi*fc, 2*np.pi*self.fs)

        # Noise floor
        N2 = psd.sel(freq=f_range) * psd.freq.sel(freq=f_range)
        noise_level = np.sqrt(N2.mean(dim='freq'))

        out = xr.DataArray(noise_level.values, name='noise_level',
                           dims=['time'],
                           attrs={'units': 'm/s',
                                  'description': 'Doppler noise level calculated \
                                                    from PSD white noise'})
        return out

    def _stress_rotations(self, ds_avg, stress_matrix):
        # Create dummy dataset to handle rotations
        ds_rot = type(ds_avg)()
        ds_rot.attrs = ds_avg.attrs
        ds_rot = ds_rot.assign_coords(ds_avg.coords)

        # Add Reynolds stress tensor and orientation matrix
        ds_rot['stress_matrix'] = stress_matrix
        ds_rot['orientmat'] = ds_avg.orientmat

        # Rotate into coordinate system of binned dataset
        if ds_rot.coord_sys != 'inst':
            if 'rdi' in ds_avg.inst_make.lower():
                func = rdi._inst2earth
            elif 'signature' in ds_avg.inst_model.lower():
                func = signature._inst2earth
            # rotate to earth
            ds_rot = func(ds_rot, rotate_vars=('stress_matrix',), force=True)
        # rotate to principal
        if ds_rot.coord_sys == 'principal':
            ds_rot = _earth2principal(ds_rot, rotate_vars='stress_matrix')

        return ds_rot

    def calc_stress_4beam(self, ds, ds_avg, noise=0, beam_angle=25):
        """Calculate the stresses from the difference in the beam variances.
        Assumes zero mean pitch and roll

        Parameters
        ----------
        ds (xarray.Dataset):
          Raw dataset in beam coordinates
        ds_avg (xarray.Dataset):
          Binned dataset in final coordinate reference frame
        noise (int or xarray.DataArray):
          Doppler noise level
        beam_angle (int, default=25):
          ADCP beam angle

        Returns
        -------
        None :
          Operates inplace. Adds `tke_vec` and `stress_vec` to 'ds_avg'

        Notes
        -----
        Stacey, Mark T., Stephen G. Monismith, and Jon R. Burau. "Measurements 
        of Reynolds stress profiles in unstratified tidal flow." Journal of 
        Geophysical Research: Oceans 104.C5 (1999): 10933-10949.

        """
        if 'beam' in ds_avg.coord_sys:
            raise Exception(
                'Binned data should be in "inst", "earth", or "principal" coordinates.')
        if 'beam' not in ds.coord_sys:
            warnings.warn(
                "Raw data must be in 'beam' coordinate system. \
                    Rotating raw data into beam coordinates")
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
        if 'TRDI' in ds.inst_make:
            if 'down' in ds.orientation.lower():
                # this order is correct given the note above
                beams = [0, 1, 2, 3]  # for down-facing RDIs
            else:
                beams = [0, 1, 3, 2]  # for up-facing RDIs

        # For Nortek Signatures
        elif 'Signature' in ds.inst_model:
            if 'down' in ds.orientation.lower():
                beams = [2, 0, 3, 1]  # for down-facing Norteks
            else:
                # for up-facing or AHRS-equipped Norteks
                beams = [0, 2, 3, 1]

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

        # Set other stress variables as None for tensor rotation
        upvp_ = np.empty(upwp_.shape)
        upup_ = np.empty(upwp_.shape)
        vpvp_ = np.empty(upwp_.shape)
        wpwp_ = np.empty(upwp_.shape)

        stress_matrix = xr.DataArray(np.stack([[upup_, upvp_, upwp_],
                                               [upvp_, vpvp_, vpwp_],
                                               [upwp_, vpwp_, wpwp_]]),
                                     dims=['inst', 'dirIMU',
                                           'range', 'time'],  # use dummy dimensions
                                     attrs={'units': 'm^2/^2'})

        # Tensor rotation
        ds_rot = self._stress_rotations(ds_avg, stress_matrix)

        ds_avg['stress_vec'] = xr.DataArray(np.stack([ds_rot.stress_matrix[0, 1]*np.nan,
                                                      ds_rot.stress_matrix[0, 2],
                                                      ds_rot.stress_matrix[1, 2]]),
                                            coords={'tau': ["upvp_", "upwp_", "vpwp_"],
                                                    'range': ds_avg.range,
                                                    'time': ds_avg.time},
                                            attrs={'units': 'm^2/^2'})

        # Function works inplace

    def calc_stress_5beam(self, ds, ds_avg, noise=0, beam_angle=25):
        """Calculate the stresses from the difference in the beam variances.
        Assumes small-angle approximation is applicable

        Parameters
        ----------
        ds (xarray.Dataset):
          Raw dataset in beam coordinates
        ds_avg (xarray.Dataset):
          Binned dataset in final coordinate reference frame
        noise (int or xarray.DataArray):
          Doppler noise level
        beam_angle (int, default=25):
          ADCP beam angle

        Returns
        -------
        None :
          Operates inplace. Adds `tke_vec` and `stress_vec` to 'ds_avg'

        Notes
        -----
        Dewey, R., and S. Stringer. "Reynolds stresses and turbulent kinetic
        energy estimates from various ADCP beam configurations: Theory." J. of
        Phys. Ocean (2007): 1-35.

        Guerra, Maricarmen, and Jim Thomson. "Turbulence measurements from 
        five-beam acoustic Doppler current profilers." Journal of Atmospheric 
        and Oceanic Technology 34.6 (2017): 1267-1284.

        """
        if 'vel_b5' not in ds.data_vars:
            raise Exception("Must have 5th beam data")
        if 'beam' in ds_avg.coord_sys:
            raise Exception(
                'Binned data should be in "inst", "earth", or "principal" coordinates.')
        if 'beam' not in ds.coord_sys:
            warnings.warn(
                "Raw data must be in 'beam' coordinate system. \
                Rotating raw data into beam coordinates")
            ds.velds.rotate2('beam')

        b_angle = getattr(ds, 'beam_angle', beam_angle)
        beam_vel = np.concatenate((ds['vel'].values,
                                   ds['vel_b5'].values[None, ...]))

        if 'TRDI' in ds.inst_make:
            # For TRDI Sentinel V
            phi2 = np.deg2rad(ds['pitch'].values)
            phi3 = np.deg2rad(ds['roll'].values)
            if 'down' in ds.orientation.lower():
                beams = [0, 1, 2, 3, 4]  # for down-facing RDIs
            else:
                beams = [0, 1, 3, 2, 4]  # for up-facing RDIs

        # For Nortek Signatures
        elif 'Signature' in ds.inst_model:
            phi2 = np.deg2rad(self.mean(ds['roll'].values))
            phi3 = -np.deg2rad(self.mean(ds['pitch'].values))
            if 'down' in ds.orientation.lower():
                beams = [2, 0, 3, 1, 4]  # for down-facing Norteks
            else:
                # for up-facing or AHRS-equipped Norteks
                beams = [0, 2, 3, 1, 4]

        # Calculate along-beam velocity prime squared bar
        bp2_ = np.empty((5, len(ds.range), len(phi2)))*np.nan
        for i, beam in enumerate(beams):
            bp2_[i] = np.nanvar(self.reshape(beam_vel[beam]), axis=-1)

        # Remove doppler_noise
        if type(noise) == type(ds_avg.vel):
            noise = noise.values
        bp2_ -= noise**2

        # Guerra Thomson calculate u'v' bar from from the covariance of u' and v'
        ds.velds.rotate2('inst')
        vel = self.detrend(ds.vel.values)
        upvp_ = np.nanmean(vel[0] * vel[1], axis=-1,
                           dtype=np.float64).astype(np.float32)
        ds.velds.rotate2('beam')

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

        upwp_ = (sin(th)**5*cos(th)*(bp2_[1]-bp2_[0]) +
                 2*sin(th)**4*cos(th)*2*phi3*(bp2_[1]+bp2_[0]) -
                 4*sin(th)**4*cos(th)*2*phi3*bp2_[4] -
                 4*sin(th)**6*cos(th)*2*phi2*upvp_) / denm

        vpwp_ = (sin(th)**5*cos(th)*(bp2_[3]-bp2_[2]) -
                 2*sin(th)**4*cos(th)*2*phi2*(bp2_[3]+bp2_[2]) +
                 4*sin(th)**4*cos(th)*2*phi2*bp2_[4] +
                 4*sin(th)**6*cos(th)*2*phi3*upvp_) / denm

        stress_matrix = xr.DataArray(np.stack([[upup_, upvp_, upwp_],
                                               [upvp_, vpvp_, vpwp_],
                                               [upwp_, vpwp_, wpwp_]]),
                                     dims=['inst', 'dirIMU',
                                           'range', 'time'],  # use dummy dimensions
                                     attrs={'units': 'm^2/^2'})

        # Tensor rotation
        ds_rot = self._stress_rotations(ds_avg, stress_matrix)

        # Reorganize stress matrix into readable fashion
        ds_avg['tke_vec'] = xr.DataArray(np.stack([ds_rot.stress_matrix[0, 0],
                                                   ds_rot.stress_matrix[1, 1],
                                                   ds_rot.stress_matrix[2, 2]]),
                                         coords={'tke': ["upup_", "vpvp_", "wpwp_"],
                                                 'range': ds_avg.range,
                                                 'time': ds_avg.time},
                                         attrs={'units': 'm^2/^2'})
        ds_avg['stress_vec'] = xr.DataArray(np.stack([ds_rot.stress_matrix[0, 1],
                                                      ds_rot.stress_matrix[0, 2],
                                                      ds_rot.stress_matrix[1, 2]]),
                                            coords={'tau': ["upvp_", "upwp_", "vpwp_"],
                                                    'range': ds_avg.range,
                                                    'time': ds_avg.time},
                                            attrs={'units': 'm^2/^2'})
        # Function works in place

    def calc_tke_dissipation(self, psd, U_mag, noise_level, f_range=[1, 2]):
        """Calculate the dissipation rate from the PSD

        Parameters
        ----------
        psd : xarray.DataArray (...,time,f)
          The power spectral density
        U_mag : xarray.DataArray (...,time)
          The bin-averaged horizontal velocity [m/s] (from dataset shortcut)
        f_range : iterable(2)
          The range over which to integrate/average the spectrum, in units 
          of the psd frequency vector (Hz or rad/s)

        Returns
        -------
        epsilon : xarray.DataArray (...,n_time)
          dataArray of the dissipation rate

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
        psd -= noise_level

        idx = np.where((f_range[0] < freq) & (freq < f_range[1]))
        idx = idx[0]

        if freq.units == 'Hz':
            U = U_mag/(2*np.pi)
        else:
            U = U_mag

        a = 0.5
        out = (psd.isel(freq=idx) *
               freq.isel(freq=idx)**(5/3) / a).mean(axis=-1)**(3/2) / U

        out = xr.DataArray(out, name='dissipation_rate',
                           attrs={'units': 'm^2/s^3',
                                  'description': 'Turbulent kinetic energy \
                                                  dissipation rate'})
        return out

    def calc_tke_production(self, ds_avg):
        """Calculate turbulent kinetic energy production rate

        Parameters
        ----------
        ds_avg (xarray.Dataset): 
          Binned dataset containing `tke_vec` and `stress_vec`

        Returns
        -------
        out (xarray_Dataset):
          Production rate with single dimension `time`

        """

        P = -(ds_avg['stress_vec'].sel(tau='upwp_') * self.dudz +
              ds_avg['stress_vec'].sel(tau='vpwp_') * self.dvdz +
              ds_avg['tke_vec'].sel(tau='wpwp_') * self.dwdz)

        out = xr.DataArray(P, name='production_rate',
                           dims=['time'],
                           attrs={'units': 'm^2/s^3',
                                  'description': 'Turbulent kinetic energy \
                                                  production rate'})
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


def calc_turbulence(ds_raw, n_bin, fs, n_fft=None, freq_units='rad/s', window='hann', doppler_noise=0):
    """
    Functional version of `ADVBinner` that computes a suite of turbulence
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
    ds : xarray.Dataset
      Returns an 'binned' (i.e. 'averaged') data object. All
      fields (variables) of the input data object are averaged in n_bin
      chunks. This object also computes the following items over
      those chunks:

      - tke_vec : The energy in each component, each components is
        alternatively accessible as:
        :attr:`upup_ <dolfyn.velocity.Velocity.upup_>`,
        :attr:`vpvp_ <dolfyn.velocity.Velocity.vpvp_>`,
        :attr:`wpwp_ <dolfyn.velocity.Velocity.wpwp_>`)

      - stress : The Reynolds stresses, each component is
        alternatively accessible as:
        :attr:`upwp_ <dolfyn.data.velocity.Velocity.upwp_>`,
        :attr:`vpwp_ <dolfyn.data.velocity.Velocity.vpwp_>`,
        :attr:`upvp_ <dolfyn.data.velocity.Velocity.upvp_>`)

      - U_std : The standard deviation of the horizontal
        velocity `U_mag`.

      - psd : DataArray containing the spectra of the velocity
        in radial frequency units. The data-array contains:
        - vel : the velocity spectra array (m^2/s/rad))
        - omega : the radial frequncy (rad/s)

    """
    calculator = ADPBinner(n_bin, fs, n_fft=n_fft, doppler_noise=doppler_noise)

    return calculator(ds_raw, freq_units=freq_units, window=window)
