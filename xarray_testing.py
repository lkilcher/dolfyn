import numpy as np
import xarray as xr 
import h5py as h5
import datetime as dt

from numpy import array as ar



def mpltime_convert(time):
    return dt.datetime.fromordinal(int(time)) + dt.timedelta(days=time%1)

def check_dims(dims,coords,ori1,ori2,time):

    if dims == ['ori1','ori1']:
        dims = ['ori1','ori2']
        coords = [ori1,ori2]
    elif dims == ['ori1','ori1','time']:
        dims = ['ori1','ori2','time']
        coords = [ori1,ori2,time]
    return dims,coords    

if __name__ == "__main__":

    # File = f'./clean_data'
    # Fname = f'WP_SMB02_star_May2017_clnETU_d112.h5'
    # fname = f'{File}/{Fname}'
    fname = f'dolfyn/test/data/vector_data_imu01.h5'
    
    dsFname = f'tmp/' + f'{fname[:-4]}.nc'.rsplit('/')[-1]

    '''
    # Here I just tried to load a dolfyn hdf5 directly but xarray
    # doesn't know what to do with the whole file unfortunately
    #   - As it turns out xarray cna't handle hdf5 'groups' natively
    #     which are the subsets you mentioned

    ds = xr.load_dataset(fname)
    print(ds)
    '''
    #'''
    # Here this is a bunch of stuff to strip down an HDF5 dataset and
    # rebuild it as an xarray dataset.
    
    # Hopefully gives you an idea of how to set attrs, values, etc
    
    # One thing to note is that a Dataset is built up of multiple 
    # DataArrays (made of a single variable), but both can have 
    # their own attrs associated with them.

    with h5.File(fname,'r') as data:
        time = [mpltime_convert(t) for t in data['mpltime']]
        beams = [1,2,3,4]
        bins = [0]
        if 'range' in list(data.keys()): 
            bins = data['range']
        ori1, ori2 = ['x','y','z'], ['l','m','n']

        Dims = ar(['time','beams','bins','ori1','ori2'])
        Coords = [time,beams,bins,ori1,ori2]
        coorLen = np.array([len(x) for x in Coords])

        da = {}
        for key in data.keys():
            if key in ['mpltime','range']:
                continue
            try:
                if type(data[key]) == h5._hl.dataset.Dataset: #check if this is data
                    coords, dims = [], []
                    for i in data[key].shape: # match coordinates to datashape
                        idx = np.argwhere(i==coorLen)[0,0]
                        coords.append(Coords[idx])
                        dims.append(Dims[idx])
                    dims,coords = check_dims(dims,coords,ori1,ori2,time)
                    x = xr.DataArray(data[key][:],coords=coords,dims=dims) #build array
                    for attr in data[key].attrs:
                        x.attrs[attr] = f'{data[key].attrs[attr]}' 
                    x.name = key
                    da[key] = x
                else:
                    for k in data[key]:
                        if type(data[key][k]) == h5._hl.dataset.Dataset:
                            coords, dims = [], []
                            for i in data[key][k].shape:
                                idx = np.argwhere(i==coorLen)[0,0]
                                coords.append(Coords[idx])
                                dims.append(Dims[idx])
                            dims, coords = check_dims(dims,coords,ori1,ori2,time)
                            x = xr.DataArray(data[key][k][:],coords=coords,dims=dims)
                            for attr in data[key][k].attrs:
                                x.attrs[attr] = f'{data[key][k].attrs[attr]}' 
                            x.name = key
                            da[k] = x
                        else:
                            for kk in data[key][k].keys():
                                coords, dims = [], []
                                for i in data[key][k][kk].shape:
                                    idx = np.argwhere(i==coorLen)[0,0]
                                    coords.append(Coords[idx])
                                    dims.append(Dims[idx])
                                dims,coords = check_dims(dims,coords,ori1,ori2,time)
                                x = xr.DataArray(data[key][k][kk][:],coords=coords,dims=dims)
                                for attr in data[key].attrs:
                                    x.attrs[attr] = f'{data[key][k][kk].attrs[attr]}' 
                                x.name = key
                                da[kk] = x
            except (ValueError,IndexError):
                continue

        ds = xr.Dataset(da)
        ds.attrs['file_name'] = fname
        print(ds)
        ds.to_netcdf(dsFname, format='NETCDF4') # apparently new netcdf formats are based on HDF5
        #'''
    #'''
    ds = xr.open_dataset(dsFname)
    print(ds) # note here nothing has actually been loaded except for dimensionality

    # slicing
    try:
        cutDs = ds.sel(time='2017-05-26',beams=1,bins=slice(7,10))
        print(cutDs) # neat how that works I think, still nothing loaded

        cutDs['vel**2'] = cutDs['vel']**2
        print(cutDs) # now it's loaded since something is calculated
    except ValueError:
        pass
    #'''

    # Here is an example of how we can add specific dolfyn methods
    # to the xarray class 
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
        

    ds = xr.open_dataset(dsFname)
    print(ds.dolfyn.square_vel)
    print(ds.dolfyn.square_btvel)
    
