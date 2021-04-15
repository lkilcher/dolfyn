from __future__ import division
import numpy as np
# xarray should cover TimeData, and FreqData is simply covered by the appropriate coord/dim
#from .base import np, ma, TimeData, FreqData
from .x_binned import TimeBinner
import warnings
#from .time import num2date
from ..rotate import main as rotb
from ..rotate.x_vector import _rotate_head2inst
import xarray as xr


class Velocity():
    """This is the base class for velocity data objects.

    All ADCP and ADV data objects inherit from this base class.

    Indexing
    ........

    You can directly access an item in a subgroup by::

        >> dat['env.c_sound']
        array([1520.9   , 1520.8501, 1520.8501, ..., 1522.3   , 1522.3   ,
               1522.3   ], dtype=float32)

    # And you can test for the presence of a variable by::

        >> 'signal.amp' in dat
        True

    """
    def __init__(self, ds, *args, **kwargs):
        self.ds = ds
        #TimeData.__init__(self, *args, **kwargs)
        #self['props'] = {'coord_sys': '????',
        #                 'fs': -1,
        #                 'inst_type': '?',
        #                 'inst_make': '?',
        #                 'inst_model': '?',
        #                 'has imu': False}


    def set_inst2head_rotmat(self, rotmat):
        """
        Set the instrument to head rotation matrix for the Nortek ADV if it
        hasn't already been set through a '.userdata.json' file.
        """
        if not self._make_model.startswith('nortek vector'):
            raise Exception("Setting 'inst2head_rotmat' is only supported "
                            "for Nortek Vector ADVs.")
        if self.ds.get('inst2head_rotmat', None) is not None:
            # Technically we could support changing this (unrotate with the
            # original, then rotate with the new one), but WHY?!
            # If you REALLY need to change this, simply rotate to
            # beam-coords, change this by
            # `obj.props['inst2head_rotmat'] = rotmat`, then rotate
            # to the coords of your choice.
            raise Exception(
                "You are setting 'inst2head_rotmat' after it has already "
                "been set. You can only set it once.")
        csin = self.ds.coord_sys
        if csin not in ['inst', 'beam']:
            self.rotate2('inst', inplace=True)
        #dict.__setitem__(self.props, 'inst2head_rotmat', np.array(rotmat))
        self.ds['inst2head_rotmat'] = xr.DataArray(np.array(rotmat),
                                                   coords={'ax1':['x1','x2','x3'],
                                                           'ax2':['x1*','x2*','x3*']},
                                                   dims=['ax1','ax2'])
        self.ds.attrs['inst2head_rotmat_was_set'] = True
        # Note that there is no validation that the user doesn't
        # change `ds.attrs['inst2head_rotmat']` after calling this
        # function. I suppose I could do:
        #     self.ds.attrs['inst2head_rotmat_was_set'] = hash(rotmat)
        # But then I'd also have to check for that!? Is it worth it?

        if not csin == 'beam': # csin not 'beam', then we're in inst
            _rotate_head2inst(self.ds)
        if csin not in ['inst', 'beam']:
            self.rotate2(csin, inplace=True)

    
    def set_declination(self, declination):
        """Set the declination of the dataset.

        Parameters
        ----------
        declination : float
           The value of the magnetic declination in degrees (positive
           values specify that Magnetic North is clockwise from True North)

        Notes
        -----
        This method modifies the data object in the following ways:

        - If the data-object is in the *earth* reference frame at the time of
          setting declination, it will be rotated into the "*True-East*,
          *True-North*, Up" (hereafter, ETU) coordinate system

        - ``dat['orient']['orientmat']`` is modified to be an ETU to
          instrument (XYZ) rotation matrix (rather than the magnetic-ENU to
          XYZ rotation matrix). Therefore, all rotations to/from the 'earth'
          frame will now be to/from this ETU coordinate system.

        - The value of the specified declination will be stored in
          ``dat.props['declination']``

        - ``dat['orient']['heading']`` is adjusted for declination
          (i.e., it is relative to True North).

        - If ``dat['props']['principal_heading']`` is set, it is
          adjusted to account for the orientation of the new 'True'
          earth coordinate system (i.e., calling set_declination on a
          data object in the principal coordinate system, then calling
          dat.rotate2('earth') will yield a data object in the new
          'True' earth coordinate system)

        """
        if 'declination' in self.ds.attrs:
            angle = declination - self.ds.attrs.pop('declination')
        else:
            angle = declination
        cd = np.cos(-np.deg2rad(angle))
        sd = np.sin(-np.deg2rad(angle))

        #The ordering is funny here because orientmat is the
        #transpose of the inst->earth rotation matrix:
        Rdec = np.array([[cd, -sd, 0],
                         [sd, cd, 0],
                         [0, 0, 1]])

        #odata = self['orient']

        if self.ds.coord_sys == 'earth':
            rotate2earth = True
            self.ds = self.rotate2('inst', inplace=True)
        else:
            rotate2earth = False

        self.ds['orientmat'].values = np.einsum('kj...,ij->ki...',
                                                self.ds['orientmat'],
                                                Rdec, )
        if 'heading' in self.ds:
            self.ds['heading'] += angle
        if rotate2earth:
            self.ds = self.rotate2('earth', inplace=True)
        if 'principal_heading' in self.ds.attrs:
            self.ds.attrs['principal_heading'] += angle
        # These two lines below were originaly a '_set' subroutine of the h5 
        # object, I didn't check if that was a 'setter'
        self.ds.attrs['declination'] = declination
        self.ds.attrs['declination_in_orientmat'] = True
        
        
    def rotate2(self, out_frame, inplace=False):
        """Rotate the data object into a new coordinate system.

        Parameters
        ----------

        out_frame : string {'beam', 'inst', 'earth', 'principal'}
          The coordinate system to rotate the data into.

        inplace : bool
          Operate on self (True), or return a copy that
          has been rotated (False, default).

        Returns
        -------
        objout : :class:`Velocity`
          The rotated data object. This is `self` if inplace is True.

        See Also
        --------
        :func:`dolfyn.rotate2`

        """
        return rotb.rotate2(self.ds, out_frame=out_frame, inplace=inplace)


    @property
    def n_time(self, ):
        """The number of timesteps in the data object."""
        
        return self.ds.time.shape[0]

    # @property
    # def shape(self,):
    #     """The shape of 'scalar' data in this data object."""
    #     return self.u.shape
    
    @property
    def _make_model(self, ):
        """
        The make and model of the instrument that collected the data
        in this data object.
        """
        return '{} {}'.format(self.ds.inst_make,
                              self.ds.inst_model).lower()

    @property
    def u(self,):
        """
        The first velocity component.

        This is simply a shortcut to self['vel'][0]. Therefore,
        depending on the coordinate system of the data object
        (self['props']['coord_sys']), it is:

        - beam:      beam1
        - inst:      x
        - earth:     east
        - principal: streamwise
        """
        return self.ds['vel'][0]

    @property
    def v(self,):
        """
        The second velocity component.

        This is simply a shortcut to self['vel'][1]. Therefore,
        depending on the coordinate system of the data object
        (self['props']['coord_sys']), it is:

        - beam:      beam2
        - inst:      y
        - earth:     north
        - principal: cross-stream
        """
        return self.ds['vel'][1]

    @property
    def w(self,):
        """
        The third velocity component.

        This is simply a shortcut to self['vel'][2]. Therefore,
        depending on the coordinate system of the data object
        (self['props']['coord_sys']), it is:

        - beam:      beam3
        - inst:      z
        - earth:     up
        - principal: up
        """
        return self.ds['vel'][2]

    @property
    def U(self,):
        """
        Horizontal velocity as a complex quantity
        """
        return xr.DataArray(
                    (self.u + self.v * 1j),
                    attrs={'units':'m/s',
                           'description':'horizontal velocity (complex)'})
    @property
    def U_mag(self,):
        """
        Horizontal velocity magnitude
        """
        return xr.DataArray(
                    np.abs(self.U),
                    attrs={'units':'m/s',
                           'description':'horizontal velocity magnitude'})                            
    @property
    def U_dir(self,):
        """
        Angle of horizontal velocity vector (radians clockwise from
        X/East/streamwise).
        """
        return xr.DataArray(
                    np.angle(self.U),
                    attrs={'units':'rad',
                           'description':'''horizontal velocity flow direction, 
                           CW from X/east/streamwise'''})                            
  
    
@xr.register_dataset_accessor('Veldata')
class data(Velocity):
    """
    Xarray accessors return a warning if one accessor class inherits from
    another. This is my workaround.
    """
                              
@xr.register_dataset_accessor('TKEdata')
class TKE(Velocity):
    """This is the base class for turbulence data objects.

    The attributes and methods defined for this class assume that the
    ``'tke_vec'`` and ``'stress'`` data entries are included in the
    data object. These are typically calculated using a
    :class:`VelBinner` tool, but the method for calculating these
    variables can depend on the details of the measurement
    (instrument, it's configuration, orientation, etc.).

    See Also
    ========
    :class:`VelBinner`

    """
    # @property
    # def shape(self,):
    #     return self.ds.tke_vec[0].shape

    @property
    def tau_ij(self,):
        """Total stress tensor
        """
        n = self.ds.tke_vec
        s = self.ds.stress
        return np.array([[n[0], s[0], s[1]],
                         [s[0], n[1], s[2]],
                         [s[1], s[2], n[2]]])

    def _rotate_tau(self, rmat, cs_from, cs_to):
        # Transpose second index of rmat for rotation
        t = rotb.rotate_tensor(self.ds.tau_ij, rmat)
        self.ds['tke_vec'] = np.stack((t[0, 0], t[1, 1], t[2, 2]), axis=0)
        self.ds['stress'] = np.stack((t[0, 1], t[0, 2], t[1, 2]), axis=0)

    def _tau_is_pd(self, ):
        rotb.is_positive_definite(self.tau_ij)

    @property
    def E_coh(self,):
        """Coherent turbulent energy

        Niel Kelley's 'coherent turbulence energy', which is the RMS
        of the Reynold's stresses.

        See: NREL Technical Report TP-500-52353
        """
        # Why did he do it this way, instead of the sum of the magnitude of the
        # stresses?
        E_coh = (self.upwp_**2 + self.upvp_**2 + self.vpwp_**2) ** (0.5)
        
        return xr.DataArray(E_coh, 
                            coords={'time':self.ds['stress_vec'].time}, 
                            dims=['time'],
                            attrs={'units':self.ds['stress_vec'].units},
                            name='E_coh')
    @property
    def I_tke(self, thresh=0):
        """Turbulent kinetic energy intensity.

        Ratio of sqrt(tke) to velocity magnitude.
        """
        I_tke = np.ma.masked_where(self.U_mag < thresh,
                                   np.sqrt(2 * self.tke) / self.U_mag)
        return xr.DataArray(I_tke.data, 
                            coords={'time':self.U_mag.time}, 
                            dims=['time'],
                            attrs={'units':'% [0,1]'},
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
                            coords={'time':self.U_mag.time}, 
                            dims=['time'],
                            attrs={'units':'% [0,1]'},
                            name='turbulence intensity')
    @property
    def tke(self,):
        """
        Turbulent kinetic energy (sum of the three components)
        """
        tke = self.ds['tke_vec'].sum('tke') / 2
        tke.name = 'TKE'
        tke.attrs['units'] = self.ds['tke_vec'].units
        return tke

    @property
    def upvp_(self,):
        """
        u'v'bar Reynolds stress
        """
        return self.ds['stress_vec'].sel(stress="u'v'_")

    @property
    def upwp_(self,):
        """
        u'w'bar Reynolds stress
        """
        return self.ds['stress_vec'].sel(stress="u'w'_")

    @property
    def vpwp_(self,):
        """
        v'w'bar Reynolds stress
        """
        return self.ds['stress_vec'].sel(stress="v'w'_")

    @property
    def upup_(self,):
        """
        u'u'bar component of the tke
        """
        return self.ds['tke_vec'].sel(tke="u'u'_")

    @property
    def vpvp_(self,):
        """
        v'v'bar component of the tke
        """
        return self.ds['tke_vec'].sel(tke="v'v'_")

    @property
    def wpwp_(self,):
        """
        w'w'bar component of the tke
        """
        return self.ds['tke_vec'].sel(tke="w'w'_")
    
    @property
    def k(self):
        """
        wavenumber vector, calculated from psd-frequency vector
        """
        if hasattr(self.ds, 'omega'):
            ky = 'omega'
            c = 1
        else:
            ky = 'f'
            c = 2*np.pi
        
        k1 = c*self.ds[ky] / self.u
        k2 = c*self.ds[ky] / self.v
        k3 = c*self.ds[ky] / self.w
        # transposes dimensions for some reason
        k = xr.DataArray([k1.T.values, k2.T.values, k3.T.values],
                         coords = self.ds.psd.coords,
                         dims = self.ds.psd.dims,
                         name = 'wavenumber',
                         attrs={'units':'1/m'})
        return k


class VelBinner(TimeBinner):
    """This is the base binning (averaging) tool.

    All DOLfYN binning tools derive from this base class.

    Examples
    ========
    The VelBinner class is used to compute averages and turbulence
    statistics from 'raw' (unaveraged) ADV or ADP measurements, for
    example::

        # First read or load some data.
        rawdat = dlfn.read_example('BenchFile01.ad2cp')

        # Now initialize the averaging tool:
        binner = dlfn.VelBinner(n_bin=600, fs=rawdat['props']['fs'])

        # This computes the basic averages
        avg = binner.do_avg(rawdat)

    """
    # This defines how cross-spectra and stresses are computed.
    _cross_pairs = [(0, 1), (0, 2), (1, 2)]

    def do_tke(self, indat, out=None):
        props = {}
        if out is None:
            out = type(indat)()
            props['fs'] = self.fs
            props['n_bin'] = self.n_bin
            props['n_fft'] = self.n_fft
            
        out['tke_vec'] = self.calc_tke(indat['vel'])
        out['stress_vec'] = self.calc_stress(indat['vel'])
        
        out.attrs = props
        return out
    

    def calc_tke(self, veldat, noise=[0, 0, 0]):
        """Calculate the tke (variances of u,v,w).

        Parameters
        ----------
        veldat : a velocity data array. The last dimension is assumed
                 to be time.

        noise : a three-element vector of the noise levels of the
                velocity data for ach component of velocity.

        Returns
        -------
        An xr.DataArray of tke values.
        """
        out = np.mean(self._demean(veldat[:3].values) ** 2, # originally self.detrend
                      -1, dtype=np.float64).astype('float32')
        time = self._mean(veldat.time.values)
        
        out[0] -= noise[0] ** 2
        out[1] -= noise[1] ** 2
        out[2] -= noise[2] ** 2
        
        return xr.DataArray(out, name='tke_vec',
                            coords={'tke':["u'u'_", "v'v'_", "w'w'_"],
                                    'time':time},
                            dims=['tke','time'],
                            attrs={'units':'m^2/^2'})


    def calc_stress(self, veldat):
        """Calculate the stresses (cross-covariances of u,v,w), i.e.
        Reynold's stresses assuming constant density.

        Parameters
        ----------
        veldat : a velocity data array. The last dimension is assumed
                 to be time.

        Returns
        -------
        An xr.DataArray of stress values.
        
        """
        time = self._mean(veldat.time.values)
        veldat = veldat.values
        
        out = np.empty(self._outshape(veldat[:3].shape)[:-1],
                       dtype=np.float32)
        
        for idx, p in enumerate(self._cross_pairs):
            out[idx] = np.mean(
                self._demean(veldat[p[0]]) * # originally self.detrend
                self._demean(veldat[p[1]]),  # originally self.detrend
                -1, dtype=np.float64
            ).astype(np.float32)
        
        return xr.DataArray(out, name='stress_vec',
                            coords={'stress':["u'v'_", "u'w'_", "v'w'_"],
                                    'time':time},
                            dims=['stress','time'],
                            attrs={'units':'m^2/^2'})
    

    def calc_vel_psd(self, veldat,
                     rotate_u=False,
                     fs=None,
                     window='hann', 
                     freq_units='Hz',
                     noise=[0, 0, 0],
                     n_bin=None, n_fft=None, n_pad=None,
                     step=None):
        """
        Calculate the power spectral density of velocity.

        Parameters
        ----------
        veldat : xr.DataArray
          The raw velocity data.
        rotate_u : bool (optional)
          If True, each 'bin' of horizontal velocity is rotated into
          its principal axis prior to calculating the psd.  (default:
          False).
        fs : float (optional)
          The sample rate (default: from the binner).
        window : string or array
          Specify the window function.
        freq_units : string
          Frequency units in either Hz or rad/s (f or omega)
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
        psd : xr.DataArray (3, M, N_FFT)
          The first-dimension of the spectrum is the three
          different spectra: 'uu', 'vv', 'ww'.
          
        """
        fs = self._parse_fs(fs)
        n_fft = self._parse_nfft(n_fft)
        time = self._mean(veldat.time.values)
        veldat = veldat.values
        
        if rotate_u:
            tmpdat = self._reshape(veldat[0] + 1j * veldat[1])
            tmpdat *= np.exp(-1j * np.angle(tmpdat.mean(-1)))
            veldat[0] = tmpdat.real
            veldat[1] = tmpdat.imag
            if noise[0] != noise[1]:
                warnings.warn(
                    'Noise levels different for u,v. This means '
                    'noise-correction cannot be done here when '
                    'rotating velocity.')
                noise[0] = noise[1] = 0
        out = np.empty(self._outshape_fft(veldat[:3].shape, ),
                       dtype=np.float32)
        
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
        
        for idx in range(3):
            out[idx] = self._psd(veldat[idx], fs=fs, noise=noise[idx],
                                window=window, n_bin=n_bin,
                                n_pad=n_pad, n_fft=n_fft, step=step)
        
        da =  xr.DataArray(out, name='psd',
                            coords={'spectra':['Suu','Svv','Sww'],
                                    'time':time,
                                    f_key:freq},                              
                            dims=['spectra','time',f_key],
                            attrs={'units':units,
                                   'n_fft':n_fft})
        da[f_key].attrs['units'] = freq_units
        
        return da
    

    def calc_vel_csd(self, veldat,
                     rotate_u=False,
                     fs=None,
                     window='hann',
                     freq_units='Hz',
                     n_bin=None, n_fft=None, n_pad=None,
                     step=None):
        """
        Calculate the cross-spectral density of velocity components.

        Parameters
        ----------
        veldat   : np.ndarray
          The raw velocity data.
        rotate_u : bool (optional)
          If True, each 'bin' of horizontal velocity is rotated into
          its principal axis prior to calculating the psd.  (default:
          False).
        fs : float (optional)
          The sample rate (default: from the binner).
        window : string or array
          Specify the window function.
        freq_units : string
          Frequency units in either Hz or rad/s (f or omega)
        n_bin : int (optional)
          The bin-size (default: from the binner).
        n_fft : int (optional)
          The fft size (default: n_fft_coh from the binner).
        n_pad : int (optional)
          The number of values to pad with zero (default: 0)
        step : int (optional)
          Controls amount of overlap in fft (default: the step size is
          chosen to maximize data use, minimize nens, and have a
          minimum of 50% overlap.).

        Returns
        -------
        csd : xr.DataArray (3, M, N_FFT)
          The first-dimension of the cross-spectrum is the three
          different cross-spectra: 'uv', 'uw', 'vw' (in that order).
          
        """
        fs = self._parse_fs(fs)
        n_fft = self._parse_nfft_coh(n_fft)
        time = self._mean(veldat.time.values)
        veldat = veldat.values
        
        if rotate_u:
            tmpdat = self._reshape(veldat[0] + 1j * veldat[1])
            tmpdat *= np.exp(-1j * np.angle(tmpdat.mean(-1)))
            veldat[0] = tmpdat.real
            veldat[1] = tmpdat.imag
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
                                 n_fft=n_fft)

        da = xr.DataArray(out, name='csd',
                          coords={'cross-spectra':['Suv','Suw','Svw'],
                                  'time':time,
                                  f_key:coh_freq},
                          dims=['cross-spectra','time',f_key],
                          attrs={'units':units,
                                 'n_fft':n_fft})
        da[f_key].attrs['units'] = freq_units

        return da
