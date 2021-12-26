import numpy as np
import xarray as xr
from .binned import TimeBinner


@xr.register_dataset_accessor('Veldata')
class Velocity():
    """All ADCP and ADV xarray datasets wrap this base class.

    The turbulence-related attributes defined within this class 
    assume that the  ``'tke_vec'`` and ``'stress'`` data entries are 
    included in the dataset. These are typically calculated using a
    :class:`VelBinner` tool, but the method for calculating these
    variables can depend on the details of the measurement
    (instrument, it's configuration, orientation, etc.).

    See Also
    ========
    :class:`VelBinner`

    """

    def __init__(self, ds, *args, **kwargs):
        self.ds = ds

    @property
    def u(self,):
        """The first velocity component.

        This is simply a shortcut to self['vel'][0]. Therefore,
        depending on the coordinate system of the data object
        (self.attrs['coord_sys']), it is:

        - beam:      beam1
        - inst:      x
        - earth:     east
        - principal: streamwise
        """
        return self.ds['vel'][0]

    @property
    def v(self,):
        """The second velocity component.

        This is simply a shortcut to self['vel'][1]. Therefore,
        depending on the coordinate system of the data object
        (self.attrs['coord_sys']), it is:

        - beam:      beam2
        - inst:      y
        - earth:     north
        - principal: cross-stream
        """
        return self.ds['vel'][1]

    @property
    def w(self,):
        """The third velocity component.

        This is simply a shortcut to self['vel'][2]. Therefore,
        depending on the coordinate system of the data object
        (self.attrs['coord_sys']), it is:

        - beam:      beam3
        - inst:      z
        - earth:     up
        - principal: up
        """
        return self.ds['vel'][2]

    @property
    def U(self,):
        """Horizontal velocity as a complex quantity
        """
        return xr.DataArray(
            (self.u + self.v * 1j),
            attrs={'units': 'm/s',
                   'description': 'horizontal velocity (complex)'})

    @property
    def U_mag(self,):
        """Horizontal velocity magnitude
        """
        return xr.DataArray(
            np.abs(self.U),
            attrs={'units': 'm/s',
                   'description': 'horizontal velocity magnitude'})

    @property
    def U_dir(self,):
        """Angle of horizontal velocity vector, degrees counterclockwise from
        X/East/streamwise. Direction is 'to', as opposed to 'from'.
        """
        # Convert from radians to degrees
        angle = np.angle(self.U)*(180/np.pi)

        return xr.DataArray(angle,
                            dims=self.U.dims,
                            coords=self.U.coords,
                            attrs={'units': 'deg',
                                   'description': 'horizontal velocity flow direction, CCW from X/East/streamwise'})

    @property
    def tau_ij(self,):
        """Total stress tensor
        """
        n = self.ds.tke_vec
        s = self.ds.stress
        out = np.array([[n[0], s[0], s[1]],
                        [s[0], n[1], s[2]],
                        [s[1], s[2], n[2]]])

        return xr.DataArray(out,
                            dims=["Up", "Up*", 'time'],
                            coords={"Up": ["up", "vp", "wp"],
                                    "Up*": ["up", "vp", "wp"],
                                    'time': self.ds['stress'].time},
                            attrs={'units': self.ds['stress'].units},
                            name='stress tensor')

    @property
    def E_coh(self,):
        """Coherent turbulent energy

        Niel Kelley's 'coherent turbulence energy', which is the RMS
        of the Reynold's stresses.

        See: NREL Technical Report TP-500-52353
        """
        E_coh = (self.upwp_**2 + self.upvp_**2 + self.vpwp_**2) ** (0.5)

        return xr.DataArray(E_coh,
                            coords={'time': self.ds['stress'].time},
                            dims=['time'],
                            attrs={'units': self.ds['stress'].units},
                            name='E_coh')

    @property
    def I_tke(self, thresh=0):
        """Turbulent kinetic energy intensity.

        Ratio of sqrt(tke) to horizontal velocity magnitude.
        """
        I_tke = np.ma.masked_where(self.U_mag < thresh,
                                   np.sqrt(2 * self.tke) / self.U_mag)
        return xr.DataArray(I_tke.data,
                            coords=self.U_mag.coords,
                            dims=self.U_mag.dims,
                            attrs={'units': '% [0,1]'},
                            name='TKE intensity')

    @property
    def I(self, thresh=0):
        """Turbulence intensity.

        Ratio of standard deviation of horizontal velocity std dev
        to horizontal velocity magnitude.
        """
        I = np.ma.masked_where(self.U_mag < thresh,
                               self.ds['U_std'] / self.U_mag)
        return xr.DataArray(I.data,
                            coords=self.U_mag.coords,
                            dims=self.U_mag.dims,
                            attrs={'units': '% [0,1]'},
                            name='turbulence intensity')

    @property
    def tke(self,):
        """Turbulent kinetic energy (sum of the three components)
        """
        tke = self.ds['tke_vec'].sum('tke') / 2
        tke.name = 'TKE'
        tke.attrs['units'] = self.ds['tke_vec'].units
        return tke

    @property
    def upvp_(self,):
        """u'v'bar Reynolds stress
        """
        return self.ds['stress'].sel(tau="upvp_")

    @property
    def upwp_(self,):
        """u'w'bar Reynolds stress
        """
        return self.ds['stress'].sel(tau="upwp_")

    @property
    def vpwp_(self,):
        """v'w'bar Reynolds stress
        """
        return self.ds['stress'].sel(tau="vpwp_")

    @property
    def upup_(self,):
        """u'u'bar component of the tke
        """
        return self.ds['tke_vec'].sel(tke="upup_")

    @property
    def vpvp_(self,):
        """v'v'bar component of the tke
        """
        return self.ds['tke_vec'].sel(tke="vpvp_")

    @property
    def wpwp_(self,):
        """w'w'bar component of the tke
        """
        return self.ds['tke_vec'].sel(tke="wpwp_")

    @property
    def k(self):
        """Wavenumber vector, calculated from psd-frequency vector
        """
        if hasattr(self.ds, 'omega'):
            ky = 'omega'
            c = 1
        else:
            ky = 'f'
            c = 2*np.pi

        k1 = c*self.ds[ky] / abs(self.u)
        k2 = c*self.ds[ky] / abs(self.v)
        k3 = c*self.ds[ky] / abs(self.w)
        # transposes dimensions for some reason
        k = xr.DataArray([k1.T.values, k2.T.values, k3.T.values],
                         coords=self.ds.psd.coords,
                         dims=self.ds.psd.dims,
                         name='wavenumber',
                         attrs={'units': '1/m'})
        return k


class VelBinner(TimeBinner):
    """This is the base binning (averaging) tool.
    All |dlfn| binning tools derive from this base class.

    Examples
    ========
    The VelBinner class is used to compute averages and turbulence
    statistics from 'raw' (not averaged) ADV or ADP measurements, for
    example::

        # First read or load some data.
        rawdat = dlfn.read_example('BenchFile01.ad2cp')

        # Now initialize the averaging tool:
        binner = dlfn.VelBinner(n_bin=600, fs=rawdat.fs)

        # This computes the basic averages
        avg = binner.do_avg(rawdat)

    """
    # This defines how cross-spectra and stresses are computed.
    _cross_pairs = [(0, 1), (0, 2), (1, 2)]

    def do_tke(self, dat, out_ds=None):
        """Calculate the tke (variances of u,v,w) and stresses 
        (cross-covariances of u,v,w)

        Parameters
        ----------
        dat : xarray.Dataset
            Xarray dataset containing raw velocity data
        out_ds : xarray.Dataset
            Averaged dataset to save tke and stress dataArrays to, 
            nominally dataset output from `do_avg()`.

        Returns
        -------
        ds : xarray.Dataset
            Dataset containing tke and stress dataArrays

        """
        props = {}
        if out_ds is None:
            out_ds = type(dat)()
            props['fs'] = self.fs
            props['n_bin'] = self.n_bin
            props['n_fft'] = self.n_fft
            out_ds.attrs = props

        out_ds['tke_vec'] = self.calc_tke(dat['vel'])
        out_ds['stress'] = self.calc_stress(dat['vel'])

        return out_ds

    def calc_tke(self, veldat, noise=[0, 0, 0], detrend=True):
        """Calculate the tke (variances of u,v,w).

        Parameters
        ----------
        veldat : xarray.DataArray
            a velocity data array. The last dimension is assumed
            to be time.
        noise : float
            a three-element vector of the noise levels of the
            velocity data for ach component of velocity.
        detrend : bool (default: False)
            detrend the velocity data (True), or simply de-mean it
            (False), prior to computing tke. Note: the psd routines
            use detrend, so if you want to have the same amount of
            variance here as there use ``detrend=True``.

        Returns
        -------
        ds : xarray.DataArray
            dataArray containing u'u'_, v'v'_ and w'w'_

        """
        if 'dir' in veldat.dims:
            vel = veldat[:3].values
        else:  # for single beam input
            vel = veldat.values

        if detrend:
            vel = self._detrend(vel)
        else:
            vel = self._demean(vel)

        if 'b5' in veldat.name:
            time = self._mean(veldat.time_b5.values)
        else:
            time = self._mean(veldat.time.values)

        out = np.nanmean(vel**2, -1,
                         dtype=np.float64,
                         ).astype('float32')

        out[0] -= noise[0] ** 2
        out[1] -= noise[1] ** 2
        out[2] -= noise[2] ** 2

        da = xr.DataArray(out, name='tke_vec',
                          dims=veldat.dims,
                          attrs={'units': 'm^2/^2'})

        if 'dir' in veldat.dims:
            da = da.rename({'dir': 'tke'})
            da = da.assign_coords({'tke': ["upup_", "vpvp_", "wpwp_"],
                                   'time': time})
        else:
            if 'b5' in veldat.name:
                da = da.assign_coords({'time_b5': time})
            else:
                da = da.assign_coords({'time': time})

        return da

    def calc_stress(self, veldat, detrend=True):
        """Calculate the stresses (cross-covariances of u,v,w)

        Parameters
        ----------
        veldat : xr.DataArray
            A velocity data array. The last dimension is assumed
            to be time.
        detrend : bool (default: True)
            detrend the velocity data (True), or simply de-mean it
            (False), prior to computing stress. Note: the psd routines
            use detrend, so if you want to have the same amount of
            variance here as there use ``detrend=True``.

        Returns
        -------
        ds : xarray.DataArray

        """
        time = self._mean(veldat.time.values)
        vel = veldat.values

        out = np.empty(self._outshape(vel[:3].shape)[:-1],
                       dtype=np.float32)

        if detrend:
            vel = self._detrend(vel)
        else:
            vel = self._demean(vel)

        for idx, p in enumerate(self._cross_pairs):
            out[idx] = np.nanmean(vel[p[0]] * vel[p[1]],
                                  -1, dtype=np.float64
                                  ).astype(np.float32)

        da = xr.DataArray(out, name='stress',
                          dims=veldat.dims,
                          attrs={'units': 'm^2/^2'})
        da = da.rename({'dir': 'tau'})
        da = da.assign_coords({'tau': ["upvp_", "upwp_", "vpwp_"],
                               'time': time})
        return da

    def calc_psd(self, veldat,
                 freq_units='Hz',
                 fs=None,
                 window='hann',
                 noise=[0, 0, 0],
                 n_bin=None, n_fft=None, n_pad=None,
                 step=None):
        """Calculate the power spectral density of velocity.

        Parameters
        ----------
        veldat : xr.DataArray
          The raw velocity data (of dims 'dir' and 'time').
        freq_units : string
          Frequency units of the returned spectra in either Hz or rad/s 
          (`f` or :math:`\\omega`)
        fs : float (optional)
          The sample rate (default: from the binner).
        window : string or array
          Specify the window function.
        noise : list(3 floats) (optional)
          Noise level of each component's velocity measurement
          (default 0).
        n_bin : int (optional)
          The bin-size (default: from the binner).
        n_fft : int (optional)
          The fft size (default: from the binner).
        n_pad : int (optional)
          The number of values to pad with zero (default: 0)
        step : int (optional)
          Controls amount of overlap in fft (default: the step size is
          chosen to maximize data use, minimize nens, and have a
          minimum of 50% overlap.).

        Returns
        -------
        psd : xarray.DataArray (3, M, N_FFT)
          The spectra in the 'u', 'v', and 'w' directions.

        """
        try:
            time = self._mean(veldat.time.values)
        except:
            time = self._mean(veldat.time_b5.values)
        fs = self._parse_fs(fs)
        n_fft = self._parse_nfft(n_fft)
        veldat = veldat.values

        # Create frequency vector, also checks whether using f or omega
        freq = self.calc_freq(units=freq_units)
        if 'rad' in freq_units:
            fs = 2*np.pi*fs
            freq_units = 'rad/s'
            units = 'm^2/s/rad'
            f_key = 'omega'
        else:
            freq_units = 'Hz'
            units = 'm^2/s^2/Hz'
            f_key = 'f'

        # Spectra, if input is full velocity or a single array
        if len(veldat.shape) == 2:
            out = np.empty(self._outshape_fft(veldat[:3].shape),
                           dtype=np.float32)
            for idx in range(3):
                out[idx] = self._psd(veldat[idx], fs=fs, noise=noise[idx],
                                     window=window, n_bin=n_bin,
                                     n_pad=n_pad, n_fft=n_fft, step=step)
            coords = {'S': ['Sxx', 'Syy', 'Szz'], 'time': time, f_key: freq}
            dims = ['S', 'time', f_key]
        else:
            out = self._psd(veldat, fs=fs, noise=noise[0], window=window,
                            n_bin=n_bin, n_pad=n_pad, n_fft=n_fft, step=step)
            coords = {'time': time, f_key: freq}
            dims = ['time', f_key]

        da = xr.DataArray(out,
                          name='psd',
                          coords=coords,
                          dims=dims,
                          attrs={'units': units, 'n_fft': n_fft})
        da[f_key].attrs['units'] = freq_units

        return da

    def calc_csd(self, veldat,
                 freq_units='Hz',
                 fs=None,
                 window='hann',
                 n_bin=None,
                 n_fft_coh=None):
        """Calculate the cross-spectral density of velocity components.

        Parameters
        ----------
        veldat   : xarray.DataArray
          The raw 3D velocity data.
        freq_units : string
          Frequency units of the returned spectra in either Hz or rad/s 
          (`f` or :math:`\\omega`)
        fs : float (optional)
          The sample rate (default: from the binner).
        window : string or array
          Specify the window function.
        n_bin : int (optional)
          The bin-size (default: from the binner).
        n_fft_coh : int (optional)
          The fft size (default: n_fft_coh from the binner).

        Returns
        -------
        csd : xarray.DataArray (3, M, N_FFT)
          The first-dimension of the cross-spectrum is the three
          different cross-spectra: 'uv', 'uw', 'vw'.

        """
        fs = self._parse_fs(fs)
        n_fft = self._parse_nfft_coh(n_fft_coh)
        time = self._mean(veldat.time.values)
        veldat = veldat.values

        out = np.empty(self._outshape_fft(veldat[:3].shape, n_fft=n_fft),
                       dtype='complex')

        # Create frequency vector, also checks whether using f or omega
        coh_freq = self.calc_freq(units=freq_units, coh=True)
        if 'rad' in freq_units:
            fs = 2*np.pi*fs
            freq_units = 'rad/s'
            units = 'm^2/s/rad'
            f_key = 'omega'
        else:
            freq_units = 'Hz'
            units = 'm^2/s^2/Hz'
            f_key = 'f'

        for ip, ipair in enumerate(self._cross_pairs):
            out[ip] = self._cpsd(veldat[ipair[0]],
                                 veldat[ipair[1]],
                                 n_bin=n_bin,
                                 n_fft=n_fft,
                                 window=window)

        da = xr.DataArray(out,
                          name='csd',
                          coords={'C': ['Cxy', 'Cxz', 'Cyz'],
                                  'time': time,
                                  f_key: coh_freq},
                          dims=['C', 'time', f_key],
                          attrs={'units': units, 'n_fft_coh': n_fft})
        da[f_key].attrs['units'] = freq_units

        return da
