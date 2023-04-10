import numpy as np
import xarray as xr
from .binned import TimeBinner
from .time import dt642epoch, dt642date
from .rotate.api import rotate2, set_declination, set_inst2head_rotmat
from .io.api import save
from .tools.psd import coherence, phase_angle
from .tools.misc import slice1d_along_axis, convert_degrees


@xr.register_dataset_accessor('velds')  # 'velocity dataset'
class Velocity():
    """All ADCP and ADV xarray datasets wrap this base class.
    The turbulence-related attributes defined within this class 
    assume that the  ``'tke_vec'`` and ``'stress_vec'`` data entries are 
    included in the dataset. These are typically calculated using a
    :class:`VelBinner` tool, but the method for calculating these
    variables can depend on the details of the measurement
    (instrument, it's configuration, orientation, etc.).

    See Also
    ========
    :class:`VelBinner`
    """

    ########
    # Major components of the dolfyn-API

    def rotate2(self, out_frame='earth', inplace=True):
        """Rotate the dataset to a new coordinate system.

        Parameters
        ----------
        out_frame : string {'beam', 'inst', 'earth', 'principal'}
          The coordinate system to rotate the data into.
        inplace : bool (default: True)
          When True the existing data object is modified. When False
          a copy is returned.

        Returns
        -------
        ds : xarray.Dataset or None
          Returns the rotated dataset **when ``inplace=False``**, otherwise
          returns None.

        Notes
        -----
        - This function rotates all variables in ``ds.attrs['rotate_vars']``.

        - To rotate to the 'principal' frame, a value of
          ``ds.attrs['principal_heading']`` must exist. The function
          :func:`calc_principal_heading <dolfyn.calc_principal_heading>`
          is recommended for this purpose, e.g.::

              ds.attrs['principal_heading'] = dolfyn.calc_principal_heading(ds['vel'].mean(range))

          where here we are using the depth-averaged velocity to calculate
          the principal direction.
        """

        return rotate2(self.ds, out_frame, inplace)

    def set_declination(self, declin, inplace=True):
        """Set the magnetic declination

        Parameters
        ----------
        declination : float
          The value of the magnetic declination in degrees (positive
          values specify that Magnetic North is clockwise from True North)
        inplace : bool (default: True)
          When True the existing data object is modified. When False
          a copy is returned.

        Returns
        -------
        ds : xarray.Dataset or None
          Returns the rotated dataset **when ``inplace=False``**, otherwise
          returns None.

        Notes
        -----
        This method modifies the data object in the following ways:

        - If the dataset is in the *earth* reference frame at the time of
        setting declination, it will be rotated into the "*True-East*,
        *True-North*, Up" (hereafter, ETU) coordinate system

        - ``dat['orientmat']`` is modified to be an ETU to
        instrument (XYZ) rotation matrix (rather than the magnetic-ENU to
        XYZ rotation matrix). Therefore, all rotations to/from the 'earth'
        frame will now be to/from this ETU coordinate system.

        - The value of the specified declination will be stored in
        ``dat.attrs['declination']``

        - ``dat['heading']`` is adjusted for declination
        (i.e., it is relative to True North).

        - If ``dat.attrs['principal_heading']`` is set, it is
        adjusted to account for the orientation of the new 'True'
        earth coordinate system (i.e., calling set_declination on a
        data object in the principal coordinate system, then calling
        dat.rotate2('earth') will yield a data object in the new
        'True' earth coordinate system)
        """

        return set_declination(self.ds, declin, inplace)

    def set_inst2head_rotmat(self, rotmat, inplace=True):
        """Set the instrument to head rotation matrix for the Nortek ADV if it
        hasn't already been set through a '.userdata.json' file.

        Parameters
        ----------
        rotmat : float
            3x3 rotation matrix
        inplace : bool (default: True)
            When True the existing data object is rotated. When False
            a copy is returned that is rotated.

        Returns
        -------
        ds : xarray.Dataset or None
          Returns the rotated dataset **when ``inplace=False``**, otherwise
          returns None.

        Notes
        -----
        If the data object is in earth or principal coords, it is first
        rotated to 'inst' before assigning inst2head_rotmat, it is then
        rotated back to the coordinate system in which it was input. This
        way the inst2head_rotmat gets applied correctly (in inst
        coordinate system).
        """

        return set_inst2head_rotmat(self.ds, rotmat, inplace)

    def save(self, filename, **kwargs):
        """Save the data object (underlying xarray dataset) as netCDF (.nc).

        Parameters
        ----------
        filename : str
            Filename and/or path with the '.nc' extension
        **kwargs : these are passed directly to :func:`xarray.Dataset.to_netcdf`.

        Notes
        -----
        See |dlfn|'s :func:`save <dolfyn.io.api.save>` function for
        additional details.
        """

        save(self.ds, filename, **kwargs)

    ########
    # Magic methods of the API

    def __init__(self, ds, *args, **kwargs):
        self.ds = ds

    def __getitem__(self, key):
        return self.ds[key]

    def __contains__(self, val):
        return val in self.ds

    def __repr__(self, ):
        time_string = '{:.2f} {} (started: {})'
        if ('time' not in self or dt642epoch(self['time'][0]) < 1):
            time_string = '-->No Time Information!<--'
        else:
            tm = self['time'][[0, -1]].values
            dt = dt642date(tm[0])[0]
            delta = (dt642epoch(tm[-1]) -
                     dt642epoch(tm[0])) / (3600 * 24)  # days
            if delta > 1:
                units = 'days'
            elif delta * 24 > 1:
                units = 'hours'
                delta *= 24
            elif delta * 24 * 60 > 1:
                delta *= 24 * 60
                units = 'minutes'
            else:
                delta *= 24 * 3600
                units = 'seconds'
            try:
                time_string = time_string.format(delta, units,
                                                 dt.strftime('%b %d, %Y %H:%M'))
            except AttributeError:
                time_string = '-->Error in time info<--'

        p = self.ds.attrs
        t_shape = self['time'].shape
        if len(t_shape) > 1:
            shape_string = '({} bins, {} pings @ {}Hz)'.format(
                t_shape[0], t_shape, p.get('fs'))
        else:
            shape_string = '({} pings @ {}Hz)'.format(
                t_shape[0], p.get('fs', '??'))
        _header = ("<%s data object>: "
                   " %s %s\n"
                   "  . %s\n"
                   "  . %s-frame\n"
                   "  . %s\n" %
                   (p.get('inst_type'),
                    self.ds.attrs['inst_make'], self.ds.attrs['inst_model'],
                    time_string,
                    p.get('coord_sys'),
                    shape_string))
        _vars = '  Variables:\n'

        # Specify which variable show up in this view here.
        # * indicates a wildcard
        # This list also sets the display order.
        # Only the first 12 matches are displayed.
        show_vars = ['time*', 'vel*', 'range', 'range_echo',
                     'orientmat', 'heading', 'pitch', 'roll',
                     'temp', 'press*', 'amp*', 'corr*',
                     'accel', 'angrt', 'mag', 'echo',
                     ]
        n = 0
        for v in show_vars:
            if n > 12:
                break
            if v.endswith('*'):
                v = v[:-1]  # Drop the '*'
                for nm in self.variables:
                    if n > 12:
                        break
                    if nm.startswith(v):
                        n += 1
                        _vars += '  - {} {}\n'.format(nm, self.ds[nm].dims)
            elif v in self.ds:
                _vars += '  - {} {}\n'.format(v, self.ds[v].dims)
        if n < len(self.variables):
            _vars += '  ... and others (see `<obj>.variables`)\n'
        return _header + _vars

    ######
    # Duplicate valuable xarray properties here.
    @property
    def variables(self, ):
        """A sorted list of the variable names in the dataset."""
        return sorted(self.ds.variables)

    @property
    def attrs(self, ):
        """The attributes in the dataset."""
        return self.ds.attrs

    @property
    def coords(self, ):
        """The coordinates in the dataset."""
        return self.ds.coords

    ######
    # A bunch of DOLfYN specific properties
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
        return self.ds['vel'][0].drop('dir')

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
        return self.ds['vel'][1].drop('dir')

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
        return self.ds['vel'][2].drop('dir')

    @property
    def U(self,):
        """Horizontal velocity as a complex quantity
        """
        return xr.DataArray(
            (self.u + self.v * 1j).astype('complex64'),
            attrs={'units': 'm s-1',
                   'long_name': 'Horizontal Water Velocity'})

    @property
    def U_mag(self,):
        """Horizontal velocity magnitude
        """
        return xr.DataArray(
            np.abs(self.U).astype('float32'),
            attrs={'units': 'm s-1',
                   'long_name': 'Water Speed',
                   'standard_name': 'sea_water_speed'})

    @property
    def U_dir(self,):
        """Angle of horizontal velocity vector. Direction is 'to', 
        as opposed to 'from'. This function calculates angle as 
        "degrees CCW from X/East/streamwise" and then converts it to 
        "degrees CW from X/North/streamwise".
        """
        def convert_to_CW(angle):
            if self.ds.coord_sys == 'earth':
                # Convert "deg CCW from East" to "deg CW from North" [0, 360]
                angle = convert_degrees(angle, tidal_mode=False)
                relative_to = self.ds.dir[1].values
            else:
                # Switch to clockwise and from [-180, 180] to [0, 360]
                angle *= -1
                angle[angle < 0] += 360
                relative_to = self.ds.dir[0].values
            return angle, relative_to

        # Convert from radians to degrees
        angle, rel = convert_to_CW(np.angle(self.U)*(180/np.pi))

        return xr.DataArray(
            angle.astype('float32'),
            dims=self.U.dims,
            coords=self.U.coords,
            attrs={'units': 'degrees_CW_from_' + str(rel),
                   'long_name': 'Water Direction',
                   'standard_name': 'sea_water_to_direction'})

    @property
    def E_coh(self,):
        """Coherent turbulence energy

        Niel Kelley's 'coherent turbulence energy', which is the RMS
        of the Reynold's stresses.

        See: NREL Technical Report TP-500-52353
        """
        E_coh = (self.upwp_**2 + self.upvp_**2 + self.vpwp_**2) ** (0.5)

        return xr.DataArray(
            E_coh.astype('float32'),
            coords={'time': self.ds['stress_vec'].time},
            dims=['time'],
            attrs={'units': self.ds['stress_vec'].units,
                   'long_name': 'Coherent Turbulence Energy',
                   'standard_name': 'coherent_turbulence_energy_of_sea_water'})

    @property
    def I_tke(self, thresh=0):
        """Turbulent kinetic energy intensity.

        Ratio of sqrt(tke) to horizontal velocity magnitude.
        """
        I_tke = np.ma.masked_where(self.U_mag < thresh,
                                   np.sqrt(2 * self.tke) / self.U_mag)
        return xr.DataArray(
            I_tke.data.astype('float32'),
            coords=self.U_mag.coords,
            dims=self.U_mag.dims,
            attrs={'units': '% [0,1]',
                   'long_name': 'TKE Intensity',
                   'standard_name': 'specific_turbulent_kinetic_energy_intensity_of_sea_water'})

    @property
    def I(self, thresh=0):
        """Turbulence intensity.

        Ratio of standard deviation of horizontal velocity
        to horizontal velocity magnitude.
        """
        I = np.ma.masked_where(self.U_mag < thresh,
                               self.ds['U_std'] / self.U_mag)
        return xr.DataArray(
            I.data.astype('float32'),
            coords=self.U_mag.coords,
            dims=self.U_mag.dims,
            attrs={'units': '% [0,1]',
                   'long_name': 'Turbulence Intensity',
                   'standard_name': 'turbulence_intensity_of_sea_water'})

    @property
    def tke(self,):
        """Turbulent kinetic energy (sum of the three components)
        """
        tke = self.ds['tke_vec'].sum('tke') / 2
        tke.name = 'TKE'
        tke.attrs['units'] = self.ds['tke_vec'].units
        tke.attrs['long_name'] = 'TKE'
        tke.attrs['standard_name'] = 'specific_turbulent_kinetic_energy_of_sea_water'
        return tke

    @property
    def upvp_(self,):
        """u'v'bar Reynolds stress
        """
        return self.ds['stress_vec'].sel(tau="upvp_").drop('tau')

    @property
    def upwp_(self,):
        """u'w'bar Reynolds stress
        """
        return self.ds['stress_vec'].sel(tau="upwp_").drop('tau')

    @property
    def vpwp_(self,):
        """v'w'bar Reynolds stress
        """
        return self.ds['stress_vec'].sel(tau="vpwp_").drop('tau')

    @property
    def upup_(self,):
        """u'u'bar component of the tke
        """
        return self.ds['tke_vec'].sel(tke="upup_").drop('tke')

    @property
    def vpvp_(self,):
        """v'v'bar component of the tke
        """
        return self.ds['tke_vec'].sel(tke="vpvp_").drop('tke')

    @property
    def wpwp_(self,):
        """w'w'bar component of the tke
        """
        return self.ds['tke_vec'].sel(tke="wpwp_").drop('tke')


class VelBinner(TimeBinner):
    """This is the base binning (averaging) tool.
    All |dlfn| binning tools derive from this base class.

    Examples
    ========
    The VelBinner class is used to compute averages and turbulence
    statistics from 'raw' (not averaged) ADV or ADP measurements, for
    example::

        # First read or load some data.
        rawdat = dolfyn.read_example('BenchFile01.ad2cp')

        # Now initialize the averaging tool:
        binner = dolfyn.VelBinner(n_bin=600, fs=rawdat.fs)

        # This computes the basic averages
        avg = binner.do_avg(rawdat)
    """

    # This defines how cross-spectra and stresses are computed.
    _cross_pairs = [(0, 1), (0, 2), (1, 2)]

    tke = xr.DataArray(["upup_", "vpvp_", "wpwp_"],
                       dims=['tke'],
                       name='tke',
                       attrs={'units': '1',
                              'long_name': 'Turbulent Kinetic Energy Vector Components',
                              'coverage_content_type': 'coordinate'})

    tau = xr.DataArray(["upvp_", "upwp_", "vpwp_"],
                       dims=['tau'],
                       name='tau',
                       attrs={'units': '1',
                              'long_name': 'Reynolds Stress Vector Components',
                              'coverage_content_type': 'coordinate'})

    S = xr.DataArray(['Sxx', 'Syy', 'Szz'],
                     dims=['S'],
                     name='S',
                     attrs={'units': '1',
                            'long_name': 'Power Spectral Density Vector Components',
                            'coverage_content_type': 'coordinate'})

    C = xr.DataArray(['Cxy', 'Cxz', 'Cyz'],
                     dims=['C'],
                     name='C',
                     attrs={'units': '1',
                            'long_name': 'Cross-Spectral Density Vector Components',
                            'coverage_content_type': 'coordinate'})

    def do_avg(self, raw_ds, out_ds=None, names=None):
        """Bin the dataset and calculate the ensemble averages of each 
        variable.

        Parameters
        ----------
        raw_ds : xarray.Dataset
           The raw data structure to be binned
        out_ds : xarray.Dataset
           The bin'd (output) data object to which averaged data is added.
        names : list of strings
           The names of variables to be averaged.  If `names` is None,
           all data in `raw_ds` will be binned.

        Returns
        -------
        out_ds : xarray.Dataset
          The new (or updated when out_ds is not None) dataset
          with the averages of all the variables in raw_ds.

        Raises
        ------
        AttributeError : when out_ds is supplied as input (not None)
        and the values in out_ds.attrs are inconsistent with
        raw_ds.attrs or the properties of this VelBinner (n_bin,
        n_fft, fs, etc.)

        Notes
        -----
        raw_ds.attrs are copied to out_ds.attrs. Inconsistencies
        between the two (when out_ds is specified as input) raise an
        AttributeError.
        """

        out_ds = self._check_ds(raw_ds, out_ds)

        if names is None:
            names = raw_ds.data_vars

        for ky in names:
            # set up dimensions and coordinates for Dataset
            dims_list = raw_ds[ky].dims
            coords_dict = {}
            for nm in dims_list:
                if 'time' in nm:
                    coords_dict[nm] = self.mean(raw_ds[ky][nm].values)
                else:
                    coords_dict[nm] = raw_ds[ky][nm].values

            # create Dataset
            if 'ensemble' not in ky:
                try:  # variables with time coordinate
                    out_ds[ky] = xr.DataArray(self.mean(raw_ds[ky].values),
                                              coords=coords_dict,
                                              dims=dims_list,
                                              attrs=raw_ds[ky].attrs
                                              ).astype('float32')
                except:  # variables not needing averaging
                    pass
            # Add standard deviation
            std = self.std(raw_ds.velds.U_mag.values)
            out_ds['U_std'] = xr.DataArray(
                std.astype('float32'),
                dims=raw_ds.vel.dims[1:],
                attrs={'units': 'm s-1',
                       'long_name': 'Water Velocity Standard Deviation',
                       'standard_name': 'sea_water_velocity_standard_deviation'})

        return out_ds

    def do_var(self, raw_ds, out_ds=None, names=None, suffix='_var'):
        """Bin the dataset and calculate the ensemble variances of each 
        variable. Complementary to `do_avg()`.

        Parameters
        ----------
        raw_ds : xarray.Dataset
           The raw data structure to be binned.
        out_ds : xarray.Dataset
           The binned (output) dataset to which variance data is added,
           nominally dataset output from `do_avg()`
        names : list of strings
           The names of variables of which to calculate variance.  If
           `names` is None, all data in `raw_ds` will be binned.

        Returns
        -------
        out_ds : xarray.Dataset
          The new (or updated when out_ds is not None) dataset
          with the variance of all the variables in raw_ds.

        Raises
        ------
        AttributeError : when out_ds is supplied as input (not None)
        and the values in out_ds.attrs are inconsistent with
        raw_ds.attrs or the properties of this VelBinner (n_bin,
        n_fft, fs, etc.)

        Notes
        -----
        raw_ds.attrs are copied to out_ds.attrs. Inconsistencies
        between the two (when out_ds is specified as input) raise an
        AttributeError.
        """

        out_ds = self._check_ds(raw_ds, out_ds)

        if names is None:
            names = raw_ds.data_vars

        for ky in names:
            # set up dimensions and coordinates for dataarray
            dims_list = raw_ds[ky].dims
            coords_dict = {}
            for nm in dims_list:
                if 'time' in nm:
                    coords_dict[nm] = self.mean(raw_ds[ky][nm].values)
                else:
                    coords_dict[nm] = raw_ds[ky][nm].values

            # create Dataset
            if 'ensemble' not in ky:
                try:  # variables with time coordinate
                    out_ds[ky+suffix] = xr.DataArray(self.var(raw_ds[ky].values),
                                                     coords=coords_dict,
                                                     dims=dims_list,
                                                     attrs=raw_ds[ky].attrs
                                                     ).astype('float32')
                except:  # variables not needing averaging
                    pass

        return out_ds

    def calc_coh(self, veldat1, veldat2, window='hann', debias=True,
                 noise=(0, 0), n_fft_coh=None, n_bin=None):
        """Calculate coherence between `veldat1` and `veldat2`.

        Parameters
        ----------
        veldat1 : xarray.DataArray
          The first (the longer, if applicable) raw dataArray of which to 
          calculate coherence
        veldat2 : xarray.DataArray
          The second (the shorter, if applicable) raw dataArray of which to 
          calculate coherence
        window : str
          String indicating the window function to use (default: 'hanning')
        noise : float
          The white-noise level of the measurement (in the same units
          as `veldat`).
        n_fft_coh : int
          n_fft of veldat2, number of elements per bin if 'None' is taken 
          from VelBinner
        n_bin : int
          n_bin of veldat2, number of elements per bin if 'None' is taken 
          from VelBinner

        Returns
        -------
        da : xarray.DataArray
          The coherence between signal veldat1 and veldat2.

        Notes
        -----
        The two velocity inputs do not have to be perfectly synchronized, but 
        they should have the same start and end timestamps.
        """

        if veldat1.size < veldat2.size:
            raise Exception(
                "veldat1 is shorter than veldat2. Please switch these inputs.")

        dat1 = veldat1.values
        dat2 = veldat2.values

        if n_fft_coh is None:
            n_fft = self.n_fft_coh
        else:
            n_fft = int(n_fft_coh)

        # want each slice to carry the same timespan
        n_bin2 = self._parse_nbin(n_bin)  # bins for shorter array
        n_bin1 = int(dat1.shape[-1]/(dat2.shape[-1]/n_bin2))

        oshp = self._outshape_fft(dat1.shape, n_fft=n_fft, n_bin=n_bin1)
        oshp[-2] = np.min([oshp[-2], int(dat2.shape[-1] // n_bin2)])
        out = np.empty(oshp, dtype=dat1.dtype)

        # The data is detrended in psd, so we don't need to do it here.
        dat1 = self.reshape(dat1, n_pad=n_fft, n_bin=n_bin1)
        dat2 = self.reshape(dat2, n_pad=n_fft, n_bin=n_bin2)

        for slc in slice1d_along_axis(out.shape, -1):
            out[slc] = coherence(dat1[slc], dat2[slc], n_fft,
                                 window=window, debias=debias,
                                 noise=noise)

        freq = self.calc_freq(self.fs, units='Hz', coh=True)

        # Get time from shorter vector
        dims_list, coords_dict = self._new_coords(veldat2)
        # tack on new coordinate
        dims_list.append('f')
        coords_dict['f'] = freq

        da = xr.DataArray(out.astype('float32'),
                          coords=coords_dict,
                          dims=dims_list)
        da['f'].attrs['units'] = 'Hz'

        return da

    def calc_phase_angle(self, veldat1, veldat2, window='hann',
                         n_fft_coh=None, n_bin=None):
        """Calculate the phase difference between two signals as a
        function of frequency (complimentary to coherence).

        Parameters
        ----------
        veldat1 : xarray.DataArray
          The first (the longer, if applicable) raw dataArray of which to 
          calculate phase angle
        veldat2 : xarray.DataArray
          The second (the shorter, if applicable) raw dataArray of which 
          to calculate phase angle
        window : str
          String indicating the window function to use (default: 'hanning').
        n_fft : int
          Number of elements per bin if 'None' is taken from VelBinner
        n_bin : int
          Number of elements per bin from veldat2 if 'None' is taken 
          from VelBinner

        Returns
        -------
        da : xarray.DataArray
          The phase difference between signal veldat1 and veldat2.

        Notes
        -----
        The two velocity inputs do not have to be perfectly synchronized, but 
        they should have the same start and end timestamps.
        """

        if veldat1.size < veldat2.size:
            raise Exception(
                "veldat1 is shorter than veldat2. Please switch these inputs.")

        dat1 = veldat1.values
        dat2 = veldat2.values

        if n_fft_coh is None:
            n_fft = self.n_fft_coh
        else:
            n_fft = int(n_fft_coh)

        # want each slice to carry the same timespan
        n_bin2 = self._parse_nbin(n_bin)  # bins for shorter array
        n_bin1 = int(dat1.shape[-1]/(dat2.shape[-1]/n_bin2))

        oshp = self._outshape_fft(dat1.shape, n_fft=n_fft, n_bin=n_bin1)
        oshp[-2] = np.min([oshp[-2], int(dat2.shape[-1] // n_bin2)])

        # The data is detrended in psd, so we don't need to do it here:
        dat1 = self.reshape(dat1, n_pad=n_fft, n_bin=n_bin1)
        dat2 = self.reshape(dat2, n_pad=n_fft, n_bin=n_bin2)
        out = np.empty(oshp, dtype='c{}'.format(dat2.dtype.itemsize * 2))

        for slc in slice1d_along_axis(out.shape, -1):
            # PSD's are computed in radian units:
            out[slc] = phase_angle(dat1[slc], dat2[slc], n_fft,
                                   window=window)

        freq = self.calc_freq(self.fs, units='Hz', coh=True)

        # Get time from shorter vector
        dims_list, coords_dict = self._new_coords(veldat2)
        # tack on new coordinate
        dims_list.append('f')
        coords_dict['f'] = freq

        da = xr.DataArray(out,
                          coords=coords_dict,
                          dims=dims_list)
        da['f'].attrs['units'] = 'Hz'

        return da

    def calc_acov(self, veldat, n_bin=None):
        """Calculate the auto-covariance of the raw-signal `veldat`

        Parameters
        ----------
        veldat : xarray.DataArray
          The raw dataArray of which to calculate auto-covariance
        n_bin : float
          Number of data elements to use

        Returns
        -------
        da : xarray.DataArray
          The auto-covariance of veldat

        Notes
        -----
        As opposed to calc_xcov, which returns the full
        cross-covariance between two arrays, this function only
        returns a quarter of the full auto-covariance. It computes the
        auto-covariance over half of the range, then averages the two
        sides (to return a 'quartered' covariance).

        This has the advantage that the 0 index is actually zero-lag.
        """

        indat = veldat.values

        n_bin = self._parse_nbin(n_bin)
        out = np.empty(self._outshape(indat.shape, n_bin=n_bin)[:-1] +
                       [int(n_bin // 4)], dtype=indat.dtype)
        dt1 = self.reshape(indat, n_pad=n_bin / 2 - 2)
        # Here we de-mean only on the 'valid' range:
        dt1 = dt1 - dt1[..., :, int(n_bin // 4):
                        int(-n_bin // 4)].mean(-1)[..., None]
        dt2 = self.demean(indat)
        se = slice(int(n_bin // 4) - 1, None, 1)
        sb = slice(int(n_bin // 4) - 1, None, -1)
        for slc in slice1d_along_axis(dt1.shape, -1):
            tmp = np.correlate(dt1[slc], dt2[slc], 'valid')
            # The zero-padding in reshape means we compute coherence
            # from one-sided time-series for first and last points.
            if slc[-2] == 0:
                out[slc] = tmp[se]
            elif slc[-2] == dt2.shape[-2] - 1:
                out[slc] = tmp[sb]
            else:
                # For the others we take the average of the two sides.
                out[slc] = (tmp[se] + tmp[sb]) / 2

        dims_list, coords_dict = self._new_coords(veldat)
        # tack on new coordinate
        dims_list.append('lag')
        coords_dict['lag'] = np.arange(n_bin//4)

        da = xr.DataArray(out.astype('float32'),
                          coords=coords_dict,
                          dims=dims_list,)
        da['lag'].attrs['units'] = 'timestep'

        return da

    def calc_xcov(self, veldat1, veldat2, npt=1,
                  n_bin=None, normed=False):
        """Calculate the cross-covariance between arrays veldat1 and veldat2

        Parameters
        ----------
        veldat1 : xarray.DataArray
          The first raw dataArray of which to calculate cross-covariance
        veldat2 : xarray.DataArray
          The second raw dataArray of which to calculate cross-covariance
        npt : int
          Number of timesteps (lag) to calculate covariance
        n_fft : int
          n_fft of veldat2, number of elements per bin if 'None' is taken 
          from VelBinner
        n_bin : int
          n_bin of veldat2, number of elements per bin if 'None' is taken 
          from VelBinner

        Returns
        -------
        da : xarray.DataArray
          The cross-covariance between signal veldat1 and veldat2.

        Notes
        -----
        The two velocity inputs must be the same length
        """

        dat1 = veldat1.values
        dat2 = veldat2.values

        # want each slice to carry the same timespan
        n_bin2 = self._parse_nbin(n_bin)
        n_bin1 = int(dat1.shape[-1]/(dat2.shape[-1]/n_bin2))

        shp = self._outshape(dat1.shape, n_bin=n_bin1)
        shp[-2] = min(shp[-2], self._outshape(dat2.shape, n_bin=n_bin2)[-2])

        # reshape dat1 to be the same size as dat2
        out = np.empty(shp[:-1] + [npt], dtype=dat1.dtype)
        tmp = int(n_bin2) - int(n_bin1) + npt
        dt1 = self.reshape(dat1, n_pad=tmp-1, n_bin=n_bin1)

        # Note here I am demeaning only on the 'valid' range:
        dt1 = dt1 - dt1[..., :, int(tmp // 2)
                                    :int(-tmp // 2)].mean(-1)[..., None]
        # Don't need to pad the second variable:
        dt2 = self.demean(dat2, n_bin=n_bin2)

        for slc in slice1d_along_axis(shp, -1):
            out[slc] = np.correlate(dt1[slc], dt2[slc], 'valid')
        if normed:
            out /= (self.std(dat1, n_bin=n_bin1)[..., :shp[-2]] *
                    self.std(dat2, n_bin=n_bin2)[..., :shp[-2]] *
                    n_bin2)[..., None]

        dims_list, coords_dict = self._new_coords(veldat1)
        # tack on new coordinate
        dims_list.append('dt')
        coords_dict['dt'] = np.arange(npt)

        da = xr.DataArray(out.astype('float32'),
                          coords=coords_dict,
                          dims=dims_list)
        da['dt'].attrs['units'] = 'timestep'

        return da

    def calc_tke(self, veldat, noise=None, detrend=True):
        """Calculate the turbulent kinetic energy (TKE) (variances 
        of u,v,w).

        Parameters
        ----------
        veldat : xarray.DataArray
          Velocity data array from ADV or single beam from ADCP. 
          The last dimension is assumed to be time.
        noise : float or array-like
          A vector of the noise levels of the velocity data with 
          the same first dimension as the velocity vector.
        detrend : bool (default: False)
          Detrend the velocity data (True), or simply de-mean it
          (False), prior to computing tke. Note: the psd routines
          use detrend, so if you want to have the same amount of
          variance here as there use ``detrend=True``.

        Returns
        -------
        tke_vec : xarray.DataArray
          dataArray containing u'u'_, v'v'_ and w'w'_
        """

        if 'xarray' in type(veldat).__module__:
            vel = veldat.values
        if 'xarray' in type(noise).__module__:
            noise = noise.values

        if len(np.shape(vel)) > 2:
            raise Exception("This function is only valid for calculating TKE using "
                            "velocity from an ADV or a single ADCP beam.")

        # Calc TKE
        if detrend:
            out = np.nanmean(self.detrend(vel)**2, axis=-1)
        else:
            out = np.nanmean(self.demean(vel)**2, axis=-1)

        if 'dir' in veldat.dims:
            # Subtract noise
            if noise is not None:
                if np.shape(noise)[0] != 3:
                    raise Exception(
                        'Noise should have same first dimension as velocity')
                out[0] -= noise[0] ** 2
                out[1] -= noise[1] ** 2
                out[2] -= noise[2] ** 2
            # Set coords
            dims = ['tke', 'time']
            coords = {'tke': self.tke,
                      'time': self.mean(veldat.time.values)}
        else:
            # Subtract noise
            if noise is not None:
                if np.shape(noise) > np.shape(vel):
                    raise Exception(
                        'Noise should have same or fewer dimensions as velocity')
                out -= noise ** 2
            # Set coords
            dims = veldat.dims
            coords = {}
            for nm in veldat.dims:
                if 'time' in nm:
                    coords[nm] = self.mean(veldat[nm].values)
                else:
                    coords[nm] = veldat[nm].values

        return xr.DataArray(
            out.astype('float32'),
            dims=dims,
            coords=coords,
            attrs={'units': 'm2 s-2',
                   'long_name': 'TKE Vector',
                   'standard_name': 'specific_turbulent_kinetic_energy_of_sea_water'})

    def calc_psd(self, veldat,
                 freq_units='rad/s',
                 fs=None,
                 window='hann',
                 noise=None,
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
          Options: 1, None, 'hann', 'hamm'
        noise : float or array-like
          A vector of the noise levels of the velocity data with 
          the same first dimension as the velocity vector.
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

        fs_in = self._parse_fs(fs)
        n_fft = self._parse_nfft(n_fft)
        if 'xarray' in type(veldat).__module__:
            vel = veldat.values
        if 'xarray' in type(noise).__module__:
            noise = noise.values

        # Create frequency vector, also checks whether using f or omega
        if 'rad' in freq_units:
            fs = 2*np.pi*fs_in
            freq_units = 'rad s-1'
            units = 'm2 s-1 rad-1'
        else:
            fs = fs_in
            freq_units = 'Hz'
            units = 'm2 s-2 Hz-1'
        freq = xr.DataArray(self.calc_freq(fs=fs_in, units=freq_units, n_fft=n_fft),
                            dims=['freq'],
                            name='freq',
                            attrs={'units': freq_units,
                                   'long_name': 'FFT Frequency Vector',
                                   'coverage_content_type': 'coordinate'}
                            ).astype('float32')

        # Spectra, if input is full velocity or a single array
        if len(vel.shape) == 2:
            assert vel.shape[0] == 3, "Function can only handle 1D or 3D arrays." \
                " If ADCP data, please select a specific depth bin."
            if (noise is not None) and (np.shape(noise)[0] != 3):
                raise Exception(
                    'Noise should have same first dimension as velocity')
            else:
                noise = np.array([0, 0, 0])
            out = np.empty(self._outshape_fft(vel[:3].shape, n_fft=n_fft, n_bin=n_bin),
                           dtype=np.float32)
            for idx in range(3):
                out[idx] = self.calc_psd_base(vel[idx],
                                              fs=fs,
                                              noise=noise[idx],
                                              window=window,
                                              n_bin=n_bin,
                                              n_pad=n_pad,
                                              n_fft=n_fft,
                                              step=step)
            coords = {'S': self.S,
                      'time': self.mean(veldat['time'].values),
                      'freq': freq}
            dims = ['S', 'time', 'freq']
        else:
            if (noise is not None) and (len(np.shape(noise)) > 1):
                raise Exception(
                    'Noise should have same first dimension as velocity')
            else:
                noise = np.array(0)
            out = self.calc_psd_base(vel,
                                     fs=fs,
                                     noise=noise,
                                     window=window,
                                     n_bin=n_bin,
                                     n_pad=n_pad,
                                     n_fft=n_fft,
                                     step=step)
            coords = {veldat.dims[-1]: self.mean(veldat[veldat.dims[-1]].values),
                      'freq': freq}
            dims = [veldat.dims[-1], 'freq']

        return xr.DataArray(
            out.astype('float32'),
            coords=coords,
            dims=dims,
            attrs={'units': units,
                   'n_fft': n_fft,
                   'long_name': 'Power Spectral Density',
                   'standard_name': 'power_spectral_density_of_sea_water_velocity'})
