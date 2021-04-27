from __future__ import division
import numpy as np
from ..tools.psd import psd_freq, cohere, psd, cpsd_quasisync, \
    cpsd, phase_angle
from ..tools.misc import slice1d_along_axis, detrend
#from .base import ma, TimeData
#import copy
#import warnings
#import six
import xarray as xr

class TimeBinner:
    def __init__(self, n_bin, fs, n_fft=None, n_fft_coh=None, noise=[0, 0, 0]):
        """
        Initialize an averaging object.

        Parameters
        ----------
        n_bin : int
          the number of data points to include in a 'bin' (average).
        n_fft : int
          the number of data points to use for fft (`n_fft`<=`n_bin`).
          Default: `n_fft`=`n_bin`
        n_fft_coh : int
          the number of data points to use for coherence and cross-spectra ffts
          (`n_fft_coh`<=`n_bin`). Default: `n_fft_coh`=`n_bin`/6
        noise : list or ndarray
          instrument's doppler noise in same units as velocity
        """
        
        self.n_bin = n_bin
        self.fs = fs
        self.n_fft = n_fft
        self.n_fft_coh = n_fft_coh
        self.noise =  noise
        if n_fft is None:
            self.n_fft = n_bin
        elif n_fft > n_bin:
            self.n_fft = n_bin
            print("n_fft larger than n_bin \
            doesn't make sense, setting n_fft=n_bin")
        if n_fft_coh is None:
            self.n_fft_coh = int(self.n_bin // 6)
        elif n_fft_coh >= n_bin:
            self.n_fft_coh = int(n_bin // 6)
            print("n_fft_coh must be smaller than n_bin, "
                  "setting n_fft_coh=n_bin / 6")

    def _outshape(self, inshape, n_pad=0, n_bin=None):
        """
        Returns `outshape` (the 'reshape'd shape) for an `inshape` array.
        """
        n_bin = int(self._parse_nbin(n_bin))
        return list(inshape[:-1]) + [int(inshape[-1] // n_bin), int(n_bin + n_pad)]

    def _outshape_fft(self, inshape, n_fft=None, n_bin=None):
        """
        Returns `outshape` (the fft 'reshape'd shape) for an `inshape` array.
        """
        n_fft = self._parse_nfft(n_fft)
        n_bin = self._parse_nbin(n_bin)
        return list(inshape[:-1]) + [int(inshape[-1] // n_bin), int(n_fft // 2)]

    def _parse_fs(self, fs=None):
        if fs is not None:
            return fs
        return self.fs

    def _parse_nbin(self, n_bin=None):
        if n_bin is None:
            return self.n_bin
        return n_bin

    def _parse_nfft(self, n_fft=None):
        if n_fft is None:
            return self.n_fft
        return n_fft
    
    def _parse_nfft_coh(self, n_fft_coh=None):
        if n_fft_coh is None:
            return self.n_fft_coh
        return n_fft_coh


    def _reshape(self, arr, n_pad=0, n_bin=None):
        """
        Reshape the array `arr` to shape (...,n,n_bin+n_pad).

        Parameters
        ----------
        arr : np.ndarray
        n_pad : int
          Is used to add `n_pad`/2 points from the end of the previous
          ensemble to the top of the current, and `n_pad`/2 points
          from the top of the next ensemble to the bottom of the
          current.  Zeros are padded in the upper-left and lower-right
          corners of the matrix (beginning/end of timeseries).  In
          this case, the array shape will be (...,`n`,`n_pad`+`n_bin`)
        n_bin : float, int (optional)
          Override this binner's n_bin.

        Notes
        -----
        `n_bin` can be non-integer, in which case the output array
        size will be `n_pad`+`n_bin`, and the decimal will
        cause skipping of some data points in `arr`.  In particular,
        every mod(`n_bin`,1) bins will have a skipped point. For
        example:
        - for n_bin=2048.2 every 1/5 bins will have a skipped point.
        - for n_bin=4096.9 every 9/10 bins will have a skipped point.

        """
        n_bin = self._parse_nbin(n_bin)
        npd0 = int(n_pad // 2)
        npd1 = int((n_pad + 1) // 2)
        shp = self._outshape(arr.shape, n_pad=0, n_bin=n_bin)
        out = np.zeros(
            self._outshape(arr.shape, n_pad=n_pad, n_bin=n_bin),
            dtype=arr.dtype)
        if np.mod(n_bin, 1) == 0:
            # n_bin needs to be int
            n_bin = int(n_bin)
            # If n_bin is an integer, we can do this simply.
            out[..., npd0: n_bin + npd0] = (
                arr[..., :(shp[-2] * shp[-1])]).reshape(shp, order='C')
        else:
            inds = (np.arange(np.prod(shp[-2:])) * n_bin // int(n_bin)
                    ).astype(int)
            n_bin = int(n_bin)
            out[..., npd0:n_bin + npd0] = (arr[..., inds]
                                                ).reshape(shp, order='C')
            n_bin = int(n_bin)
        if n_pad != 0:
            out[..., 1:, :npd0] = out[..., :-1, n_bin:n_bin + npd0]
            out[..., :-1, -npd1:] = out[..., 1:, npd0:npd0 + npd1]

        return out

    def _detrend(self, dat, n_pad=0, n_bin=None):
        """
        Reshape the array `dat` and remove the best-fit trend line.

        ... Need to fix this to deal with NaNs...
        """
        return detrend(self._reshape(dat, n_pad=n_pad, n_bin=n_bin), axis=-1)


    def _demean(self, dat, n_pad=0, n_bin=None):
        """
        Reshape the array `dat` and remove the mean from each ensemble.
        """
        dt = self._reshape(dat, n_pad=n_pad, n_bin=n_bin)
        return dt - (np.nanmean(dt,-1)[..., None])


    def _mean(self, dat, axis=-1, n_bin=None):
        """
        Takes the average of binned data

        Parameters
        ----------
        dat : numpy.ndarray
        
        n_bin : int (default is self.n_bin)

        """
        # Can I turn this 'swapaxes' stuff into a decorator?
        if axis != -1:
            dat = np.swapaxes(dat, axis, -1)
        n_bin = self._parse_nbin(n_bin)
        tmp = self._reshape(dat, n_bin=n_bin)
        
        return np.nanmean(tmp,-1)


    # def mean_angle(self, dat, axis=-1, units='radians',
    #                 n_bin=None, mask_thresh=None):
    #     """Average an angle array.

    #     Parameters
    #     ----------
    #     units : {'radians' | 'degrees'}

    #     n_bin : int (default is self.n_bin)

    #     mask_thresh : float (between 0 and 1)
    #         if the input data is a masked array, and mask_thresh is
    #         not None mask the averaged values where the fraction of
    #         bad points is greater than mask_thresh
    #     """
    #     if units.lower().startswith('deg'):
    #         dat = dat * np.pi / 180
    #     elif units.lower().startswith('rad'):
    #         pass
    #     else:
    #         raise ValueError("Units must be either 'rad' or 'deg'.")
    #     return np.angle(self._mean(np.exp(1j * dat)))


    def _var(self, dat, n_bin=None):
        '''
        Takes the variance of binned data
        
        Returns a numpy.ndarray
        '''
        return self._reshape(dat, n_bin=n_bin).var(-1)


    def _std(self, dat, n_bin=None):
        '''
        Takes the standard deviation of binned data
        
        Returns a numpy.ndarray
        '''
        return self._reshape(dat, n_bin=n_bin).std(-1)
    
    def _new_coords(self, array):
        '''
        Surely xarray has a built-in way to do this but I can't find it.
        Function for setting up a new data-array irregardless of how many 
        dimensions the input data-array has
        '''
        dims = array.dims
        dims_list = []
        coords_dict = {}
        if len(array.shape)==1 & ('orient' in array.coords):
            array = array.drop('orient')
        for ky in dims:
            dims_list.append(ky)
            if 'time' in ky:
                coords_dict[ky] = self._mean(array.time.values)
            else:
                coords_dict[ky] = array.coords[ky].values
                
        return dims_list, coords_dict


    def do_avg(self, rawdat, outdat=None, names=None, 
               n_time=None, noise=[0,0,0]):
        """Average data into bins/ensembles

        Parameters
        ----------
        rawdat : raw_data_object
           The raw data structure to be binned
        outdat : avg_data_object
           The bin'd (output) data object to which averaged data is added.
        names : list of strings
           The names of variables to be averaged.  If `names` is None,
           all data in `rawdat` will be binned.
        noise : list or ndarray
          instrument's doppler noise in same units as velocity
        """
        props = {}

        # if n_time is None:
        #     n_time = rawdat.n_time
        if outdat is None:
            outdat = type(rawdat)()
            props['description'] = 'Binned averages calculated from ' \
                                    'ensembles of size "n_bin"'
            props['fs'] = self.fs
            props['n_bin'] = self.n_bin
            props['n_fft'] = self.n_fft
        if names is None:
            names = rawdat.data_vars
            
        for ky in names:
            # set up dimensions and coordinates for Dataset
            dims_list = rawdat[ky].dims
            coords_dict = {}
            for nm in dims_list:
                if 'time' in nm:
                    coords_dict[nm] = self._mean(rawdat[ky][nm].values)
                else:
                    coords_dict[nm] = rawdat[ky][nm].values
                    
            # create Dataset
            try:
                outdat[ky] = xr.DataArray(self._mean(rawdat[ky].values),
                                          coords=coords_dict,
                                          dims=dims_list,
                                          attrs=rawdat[ky].attrs)
            except:
                pass
            
            # +1 for standard deviation
            std = (np.std(self._reshape(rawdat.Veldata.U_mag.values), axis=-1,
                          dtype=np.float64) - (noise[0] + noise[1])/2)
            outdat['U_std'] = xr.DataArray(
                        std,
                        dims=rawdat.vel.dims[1:],
                        attrs={'units':'m/s',
                               'description':'horizontal velocity std dev'})
        
        outdat.attrs = props
        return outdat


    def do_var(self, rawdat, outdat=None, names=None, suffix='_var'):
        """Calculate the variance of data attributes.

        Parameters
        ----------
        rawdat : raw_data_object
           The raw data structure to be binned.

        outdat : avg_data_object
           The bin'd (output) data object to which variance data is added.

        names : list of strings
           The names of variables of which to calculate variance.  If
           `names` is None, all data in `rawdat` will be binned.

        """
        props = {}
        # if n_time is None:
        #     n_time = rawdat.n_time
        if outdat is None:
            outdat = type(rawdat)()
            props['description'] = 'Variances calculated from ensembles '\
                                    'of size "n_bin"'
            props['n_bin'] = self.n_bin          
        if names is None:
            names = rawdat.data_vars
            
        for ky in names:
            # set up dimensions and coordinates for dataarray
            dims_list = rawdat[ky].dims
            coords_dict = {}
            for nm in dims_list:
                if 'time' in nm:
                    coords_dict[nm] = self._mean(rawdat[ky][nm].values)
                else:
                    coords_dict[nm] = rawdat[ky][nm].values
                    
            # create dataarray
            try:
                outdat[ky] = xr.DataArray(self._var(rawdat[ky].values),
                                          coords=coords_dict,
                                          dims=dims_list,
                                          attrs=rawdat[ky].attrs)
            except:
                pass
        
        outdat.attrs = props
        return outdat

    # def _check_indata(self, rawdat):
    #     if np.any(np.array(rawdat.shape) == 0):
    #         raise RuntimeError(
    #             "The input data cannot be averaged "
    #             "because it is empty.")
    #     if 'DutyCycle_NBurst' in rawdat.props and \
    #        rawdat.props['DutyCycle_NBurst'] < self.n_bin:
    #         warnings.warn(
    #             "The averaging interval (n_bin = {}) is "
    #             "larger than the burst interval (NBurst = {})!"
    #             .format(self.n_bin, rawdat.props['DutyCycle_NBurst']))
    #     if rawdat['props']['fs'] != self.fs:
    #         raise Exception(
    #             "The input data sample rate (dat.fs) does not "
    #             "match the sample rate of this binning-object!")
    
    def _calc_lag(self, npt=None, one_sided=False):
        if npt is None:
            npt = self.n_bin
        if one_sided:
            return np.arange(int(npt // 2), dtype=np.float32)
        else:
            return np.arange(npt, dtype=np.float32) - int(npt // 2)
    

    def calc_coh(self, veldat1, veldat2, window='hann', debias=True,
               noise=(0, 0), n_fft=None, n_bin1=None, n_bin2=None,):
        """
        Calculate coherence between `veldat1` and `veldat2`.
        
        Parameters
        ----------
        veldat1 : |xr.DataArray|
          The first raw-data array of which to calculate coherence
        veldat2 : |xr.DataArray|
          The second raw-data array of which to calculate coherence
        window : string
          String indicating the window function to use (default: 'hanning')
        noise  : float
          The white-noise level of the measurement (in the same units
          as `veldat`).

        """
        dat1 = veldat1.values
        dat2 = veldat2.values
        
        if n_fft is None:
            n_fft = self.n_fft_coh
        n_bin1 = self._parse_nbin(n_bin1)
        n_bin2 = self._parse_nbin(n_bin2)
        oshp = self._outshape_fft(dat1.shape, n_fft=n_fft, n_bin=n_bin1)
        oshp[-2] = np.min([oshp[-2], int(dat2.shape[-1] // n_bin2)])
        out = np.empty(oshp, dtype=dat1.dtype)
        # The data is detrended in psd, so we don't need to do it here.
        dat1 = self._reshape(dat1, n_pad=n_fft, n_bin=n_bin1)
        dat2 = self._reshape(dat2, n_pad=n_fft, n_bin=n_bin2)
        for slc in slice1d_along_axis(out.shape, -1):
            out[slc] = cohere(dat1[slc], dat2[slc],
                              n_fft, debias=debias, noise=noise)
            
        freq = self.calc_freq(self.fs, coh=True)

        dims_list, coords_dict = self._new_coords(veldat1)
        # tack on new coordinate
        dims_list.append('f')
        coords_dict['f'] = freq
        
        da =  xr.DataArray(out, name='coherence',
                            coords=coords_dict,         
                            dims=dims_list)
        da['f'].attrs['units'] = 'Hz'
            
        return da
    
    
    def calc_phase_angle(self, veldat1, veldat2, window='hann',
                    n_fft=None, n_bin1=None, n_bin2=None,):
        """
        Calculate the phase difference between two signals as a
        function of frequency (complimentary to coherence).

        Parameters
        ----------
        veldat1 : |xr.DataArray|
          The first 1D raw-data array of which to calculate phase angle
        veldat2 : |xr.DataArray|
          The second 1D raw-data array of which to calculate phase angle
        window : string
          String indicating the window function to use (default: 'hanning').

        Returns
        -------
        out : xr.DataArray
          The phase difference between signal veldat1 and veldat2.
          
        """
        dat1 = veldat1.values
        dat2 = veldat2.values
        
        if n_fft is None:
            n_fft = self.n_fft_coh
        n_bin1 = self._parse_nbin(n_bin1)
        n_bin2 = self._parse_nbin(n_bin2)
        oshp = self._outshape_fft(dat1.shape, n_fft=n_fft, n_bin=n_bin1)
        oshp[-2] = np.min([oshp[-2], int(dat2.shape[-1] // n_bin2)])
        # The data is detrended in psd, so we don't need to do it here:
        dat1 = self._reshape(dat1, n_pad=n_fft)
        dat2 = self._reshape(dat2, n_pad=n_fft)
        out = np.empty(oshp, dtype='c{}'.format(dat1.dtype.itemsize * 2))
        for slc in slice1d_along_axis(out.shape, -1):
            # PSD's are computed in radian units:
            out[slc] = phase_angle(dat1[slc], dat2[slc], n_fft,
                                   window=window)
        
        freq = self.calc_freq(self.fs, coh=True)
        
        da =  xr.DataArray(out, name='phase_angle',
                            coords={'time':self._mean(veldat1.time.values),
                                    'f':freq},                 
                            dims=['time','f'])
        da['f'].attrs['units'] = 'Hz'
            
        return da
    
    
    def calc_acov(self, veldat, n_bin=None):
        """
        Calculate the auto-covariance of the raw-signal `veldat`.

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
        dt1 = self._reshape(indat, n_pad=n_bin / 2 - 2)
        # Here we de-mean only on the 'valid' range:
        dt1 = dt1 - dt1[..., :, int(n_bin // 4):
                                int(-n_bin // 4)].mean(-1)[..., None]
        dt2 = self._demean(indat)  # Don't pad the second variable.
        dt2 = dt2 - dt2.mean(-1)[..., None]
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
        dims_list.append('dt')
        coords_dict['dt'] = np.arange(n_bin//4)
    
        da = xr.DataArray(out, name='auto-covariance',
                          coords=coords_dict,
                          dims=dims_list,)
        da['dt'].attrs['units'] = 'timestep'
        
        return da


    def calc_xcov(self, veldat1, veldat2, npt=1,
                  n_bin1=None, n_bin2=None, normed=False):
        """
        Calculate the cross-covariance between arrays veldat1 and veldat2
        for each bin
        
        Parameters
        ----------
        veldat1 : |xr.DataArray|
          The first raw-data array of which to calculate coherence
        veldat2 : |xr.DataArray|
          The second raw-data array of which to calculate coherence
        npt : number of timesteps (lag) to calculate covariance
        
        """
        indt1 = veldat1.values
        indt2 = veldat2.values
        
        n_bin1 = self._parse_nbin(n_bin1)
        n_bin2 = self._parse_nbin(n_bin2)
        shp = self._outshape(indt1.shape, n_bin=n_bin1)
        shp[-2] = min(shp[-2], self._outshape(indt2.shape, n_bin=n_bin2)[-2])
        
        # reshape indt1 to be the same size as indt2
        out = np.empty(shp[:-1] + [npt], dtype=indt1.dtype)
        tmp = int(n_bin2) - int(n_bin1) + npt
        dt1 = self._reshape(indt1, n_pad=tmp-1, n_bin=n_bin1)
        
        # Note here I am demeaning only on the 'valid' range:
        dt1 = dt1 - dt1[..., :, int(tmp // 2):int(-tmp // 2)].mean(-1)[..., None]
        # Don't need to pad the second variable:
        dt2 = self._demean(indt2, n_bin=n_bin2)
        dt2 = dt2 - dt2.mean(-1)[..., None]
        
        for slc in slice1d_along_axis(shp, -1):
            out[slc] = np.correlate(dt1[slc], dt2[slc], 'valid')
        if normed:
            out /= (self._std(indt1, n_bin=n_bin1)[..., :shp[-2]] *
                    self._std(indt2, n_bin=n_bin2)[..., :shp[-2]] *
                    n_bin2)[..., None]
        
        dims_list, coords_dict = self._new_coords(veldat1)
        # tack on new coordinate
        dims_list.append('dt')
        coords_dict['dt'] = np.arange(npt)
        
        da =  xr.DataArray(out, name='cross-covariance',
                           coords=coords_dict,            
                           dims=dims_list)
        return da
    
        
    def _psd(self, dat, fs=None, window='hann', noise=0,
            n_bin=None, n_fft=None, step=None, n_pad=None):
        """
        Calculate 'power spectral density' of `dat`.

        Parameters
        ----------
        dat    : data_object
          The raw-data array of which to calculate the psd.
        window : string
          String indicating the window function to use (default: 'hanning').
        noise  : float
          The white-noise level of the measurement (in the same units
          as `dat`).

        """
        fs = self._parse_fs(fs)
        n_bin = self._parse_nbin(n_bin)
        n_fft = self._parse_nfft(n_fft)
        if n_pad is None:
            n_pad = min(n_bin - n_fft, n_fft)
        out = np.empty(self._outshape_fft(dat.shape, n_fft=n_fft, n_bin=n_bin))
        # The data is detrended in psd, so we don't need to do it here.
        dat = self._reshape(dat, n_pad=n_pad)
        
        for slc in slice1d_along_axis(dat.shape, -1):
            # PSD's are computed in radian units: - set prior to function
            out[slc] = psd(dat[slc], n_fft, fs,
                           window=window, step=step)
        if noise != 0:
            # # the two in 2*np.pi cancels with the two in 'self.fs/2':
            # out -= noise**2 / (np.pi * fs)
            out -= noise**2 / (fs/2)
            # Make sure all values of the PSD are >0 (but still small):
            out[out < 0] = np.min(np.abs(out)) / 100
        return out
    

    def _cpsd(self, dat1, dat2, fs=None, window='hann',
             n_fft=None, n_bin1=None, n_bin2=None,):
        """
        Calculate the 'cross power spectral density' of `dat`.

        Parameters
        ----------
        dat1    : np.ndarray
          The first raw-data array of which to calculate the cpsd.
        dat2    : np.ndarray
          The second raw-data array of which to calculate the cpsd.
        window : string
          String indicating the window function to use (default: 'hanning').

        Returns
        -------
        out : np.ndarray
          The cross-spectral density of `dat1` and `dat2`

        """
        fs = self._parse_fs(fs)
        if n_fft is None:
            n_fft = self.n_fft_coh
        n_bin1 = self._parse_nbin(n_bin1)
        n_bin2 = self._parse_nbin(n_bin2)
        
        oshp = self._outshape_fft(dat1.shape, n_fft=n_fft, n_bin=n_bin1)
        oshp[-2] = np.min([oshp[-2], int(dat2.shape[-1] // n_bin2)])
        
        # The data is detrended in psd, so we don't need to do it here:
        dat1 = self._reshape(dat1, n_pad=n_fft)
        dat2 = self._reshape(dat2, n_pad=n_fft)
        out = np.empty(oshp, dtype='c{}'.format(dat1.dtype.itemsize * 2))
        if dat1.shape == dat2.shape:
            cross = cpsd
        else:
            cross = cpsd_quasisync
        for slc in slice1d_along_axis(out.shape, -1):
            # PSD's are computed in radian units: - set prior to function
            out[slc] = cross(dat1[slc], dat2[slc], n_fft,
                             #2 * np.pi * fs, window=window)
                             fs, window=window)
        return out
    
    
    def calc_freq(self, fs=None, units='Hz', n_fft=None, coh=False):    
        """
        Calculate the ordinary or radial frequency vector for the PSD's.

        Parameters
        ----------
        fs : float (optional)
          The sample rate (Hz).
        units : string
          Frequency units in either Hz or rad/s (f or omega)
        coh : bool
          Calculate the frequency vector for coherence/cross-spectra
          (default: False) i.e. use self.n_fft_coh instead of
          self.n_fft.
          
        """
        if n_fft is None:
            n_fft = self.n_fft
            if coh:
                n_fft = self.n_fft_coh
            
        fs = self._parse_fs(fs)
        
        if ('Hz' not in units) and ('rad' not in units):
            raise Exception('Valid fft frequency vector units are Hz \
                            or rad/s')
        
        if 'rad' in units:
            return psd_freq(n_fft, 2*np.pi*fs)
        else:
            return psd_freq(n_fft, fs)


    # def calc_omega(self, fs=None, coh=False):
    #     """
    #     Calculate the radial-frequency vector for the PSD's.

    #     Parameters
    #     ----------
    #     fs : float (optional)
    #       The sample rate (Hz).
    #     coh : bool
    #       Calculate the frequency vector for coherence/cross-spectra
    #       (default: False) i.e. use self.n_fft_coh instead of
    #       self.n_fft.
    #     """
    #     n_fft = self.n_fft
    #     freq_dim = 'freq'
    #     fs = self._parse_fs(fs)
    #     if coh:
    #         n_fft = self.n_fft_coh
    #         freq_dim = 'coh_freq'
            
    #     return psd_freq(n_fft, fs*2*np.pi)
    