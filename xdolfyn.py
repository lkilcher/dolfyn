import xarray as xr 
import numpy as np
from numpy import argmax, unique
from tqdm import tqdm

@xr.register_dataarray_accessor('dolfyn')
class covariance:
    
    def __init__(self,xr_DA):
        self._obj = xr_DA
        self._timesync = None
    
    def correlation(self,corr,group='1H',lags=20,multi=-1):

        def crosscorr(x,y,lag=0,multi=-1):
            return x.to_series().corr(y.to_series().shift(multi*lag))

        times, corrs = [], []
        print('Begin -- Cross Correlation Calculation --')
        for time,da in tqdm(self._obj.resample(time=group)):
            Slice = slice(da.time[0],da.time[-1])
            idxLag = argmax([crosscorr(da,corr.sel(time=Slice),
                                lag=lag,multi=multi) 
                                for lag in range(lags)])
            corrs.append((da.time[idxLag]-da.time[0]).values)
            times.append(time)
        print('Finished -- Cross Correlation Calculation --')
        return xr.DataArray(corrs,coords=[('timeDelta_Bin',times)])

    def time_sync(self,correction):

        ntimes = []
        times = self._obj.time
        for c in range(correction.timeDelta_Bin.shape[0]):
            try:
                start,stop = (correction.coords['timeDelta_Bin'][c],
                                correction.coords['timeDelta_Bin'][c+1])
                timeGroup = times.sel(time=slice(start.values,stop.values))
                ntimes.append(timeGroup.values-2*correction[c].values)
            except IndexError:
                start,stop = (correction.coords['timeDelta_Bin'][c-1],
                                correction.coords['timeDelta_Bin'][c])
                Tdiff = stop-start
                start = stop+Tdiff
                timeGroup = times.sel(time=slice(stop.values,start.values))
                ntimes.append(timeGroup.values-2*correction[c].values)

        self._timesync = np.hstack(ntimes)
        return self._timesync

@xr.register_dataset_accessor('dolfyn')
class square:
    
    def __init__(self,xr_DS):
        self._obj = xr_DS
        self._square = None
        self._btsquare = None
    
    @property
    def square_vel(self):
        if self._square is None:
            self._square = self._obj['vel']**2
        return self._square

    @property
    def square_btvel(self):
        if self._btsquare is None:
            self._btsquare = self._obj['bt_vel']**2
        return self._btsquare