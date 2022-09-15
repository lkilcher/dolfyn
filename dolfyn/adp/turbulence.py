import numpy as np
import xarray as xr
import warnings
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

    def __call___(self, ds, diff_func='centered', out_type=None,
                  window='hann', doppler_noise=[0, 0, 0, 0, 0]):
        self.nm = ds
        self.diff_style = diff_func

        out = type(ds)()
        out = self.do_avg(ds, out)

        out['doppler_noise'] = xr.DataArray(
            doppler_noise, coords={'beam': ['1', '2', '3', '4', '5']}, dims='beam')

        # out['auto_spectra_b5'] = self.calc_psd(ds['vel_b5'].isel(range=5),
        #                                        window=window,
        #                                        freq_units='rad/s',
        #                                        noise=doppler_noise)

        # out['tke_b5'] = self.calc_tke(ds['vel_b5'], noise=doppler_noise)

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

    def calc_stress_4beam(self, ds, doppler_noise, beam_angle=None, orientation=None):
        """
        Calculate the stresses from the difference in the beam variances.
        Assumes zero mean pitch and roll

        Stacey, Monosmith and Burau, (1999) JGR [104]
        "Measurements of Reynolds stress profiles in unstratified tidal flow"

        """
        if 'beam' not in ds.coord_sys:
            raise Exception("Data must be in 'beam' coordinate system")

        b_angle = getattr(ds, 'beam_angle', beam_angle)
        beam_vel = ds['vel'].values

        # Note: Stacey defines the beams incorrectly for Workhorse ADCPs.
        #       According to the workhorse coordinate transformation
        #       documentation, the instrument's:
        #                        x-axis points from beam 1 to 2, and
        #                        y-axis points from beam 4 to 3.
        # Nortek Signature x-axis points from beam 3 to 1
        #                  y-axis points from beam 2 to 4
        if 'Signature' in ds.inst_model:
            beams = [2, 0, 3, 1]  # this order for down-facing Norteks
        elif 'TRDI' in ds.inst_make:
            # this order is correct given the note above (for down-looking)
            beams = [0, 1, 2, 3]

        # beam_vel prime squared bar
        bp2_ = np.empty((5, len(ds.range), len(beam_vel)))*np.nan
        for i in beams:
            bp2_[i] = np.nanvar(self.reshape(beam_vel[i]), axis=-1)

        # Remove doppler_noise
        # TODO Remove based on velocity
        bp2_ -= doppler_noise

        denm = 4 * np.sin(np.deg2rad(b_angle)) * np.cos(np.deg2rad(b_angle))
        upwp_ = (bp2_[0] - bp2_[1]) / denm
        vpwp_ = (bp2_[2] - bp2_[3]) / denm

        if getattr(ds, 'orientation').lower() == 'up' or orientation == 'up' or orientation == 'AHRS':
            if 'RDI' in ds.inst_make:
                # When the ADCP is 'up', the u and w velocities need to be
                # multiplied by -1 (equivalent to adding pi to the roll).
                # See the coordinate transformation documentation for more info.
                #
                # The uw component has two minus signs, but the vw
                # component only has one, therefore:
                vpwp_ *= -1
            elif 'Signature' in ds.inst_model:
                # Similarly for Nortek roll axis
                upwp_ *= -1
        else:
            warnings.warn('Orientation not taken into accout. Assuming '
                          'instrument is facing down')

        #!!!
        # - Stress rotations should be **tensor rotations**.
        # - These should be handled by rotate2.
        warnings.warn("The calc_stress function does not yet "
                      "properly handle the coordinate system.")

        upvp_ = np.empty(upwp_[0].shape)*np.nan  # Set as None

        time = self._mean(ds.vel.time.values)
        stress = xr.DataArray(np.stack([upvp_, upwp_, vpwp_]), name='stress_vec',
                              coords={'tke': ["upvp_", "upwp_", "vpwp_"],
                                      'range': ds.range,
                                      'time': time},
                              attrs={'units': 'm^2/^2',
                                     'rotate_vars': 1})

        return stress

    def calc_stress_5beam(self, ds, doppler_noise, beam_angle=25):
        """
        Calculate the stresses from the difference in the beam variances.
        Assumes small-angle approximation is applicable

        Dewey, R., and S. Stringer. "Reynolds stresses and turbulent kinetic 
        energy estimates from various ADCP beam configurations: Theory." J. of 
        Phys. Ocean (2007): 1-35.

        Guerra, Thomson (2017) "Turbulence measurements from five-beam acoustic
        Doppler current profilers", JTech, vol34, pp1267-1284.

        """
        if 'beam' not in ds.coord_sys:
            raise Exception("Data must be in 'beam' coordinate system")
        if 'vel_b5' not in ds.data_vars:
            raise Exception("Must have 5th beam data")

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

        # beam_vel prime squared bar
        bp2_ = np.empty((5, len(ds.range), len(phi2)))*np.nan
        for i in beams:
            bp2_[i] = np.nanvar(self.reshape(beam_vel[i]), axis=-1)

        # Remove doppler_noise
        # TODO Remove based on velocity
        bp2_ -= doppler_noise

        th = np.deg2rad(b_angle)
        sin = np.sin
        cos = np.cos
        denm = -4 * sin(th)**6 * cos(th)**2

        # calc'd from covariance of up and vp
        upvp_ = np.empty(bp2_[0].shape)*np.nan

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

        # - Stress rotations should be **tensor rotations**.
        # - These should be handled by rotate2.
        warnings.warn("The calc_stress function does not yet "
                      "properly handle the coordinate system.")

        time = self.mean(ds.time.values)
        tke = xr.DataArray(np.stack([upup_, vpvp_, wpwp_]), name='tke_vec',
                           coords={'tke': ["upup_", "vpvp_", "wpwp_"],
                                   'range': ds.range,
                                   'time': time},
                           attrs={'units': 'm^2/^2',
                                  'rotate_vars': 1})
        stress = xr.DataArray(np.stack([upvp_, upwp_, vpwp_]), name='stress_vec',
                              coords={'tke': ["upvp_", "upwp_", "vpwp_"],
                                      'range': ds.range,
                                      'time': time},
                              attrs={'units': 'm^2/^2',
                                     'rotate_vars': 1})
        return tke, stress

    def calc_ustar_fit(self, ds, upwp_, d_inds=slice(None), H=None):
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
            H = self._mean(ds.d_range.values)
        z = ds['range'].values
        upwp_ = upwp_.values

        sign = np.nanmean(np.sign(upwp_[d_inds, :]), axis=0)
        ustar = np.nanmean(sign * upwp_[d_inds, :] /
                           (1 - z[d_inds, None] / H[None, :]), axis=0) ** 0.5

        return ustar

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
    #     # only analyze r on "flat" part of curve (select r values to estimate slope)
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
