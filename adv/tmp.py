import numpy as np
import __init__ as avm

class bin_advm(avm.adv_binned):
        
    def reshape(self,arr,n_pad=0):
        """
        Reshape the array *arr* to shape (...,n,n_bin).

        n_bin is specified in the adv_binned object.  Create a different adv_binned object to use a different n_bin.
        n is fix(len(arr)/n_bin)
        
        *n_pad* may be used to add *n_pad*/2 points from the end of the next ensemble
        to the top of the current, and *n_pad*/2 points from the top of the previous ensemble
        to the bottom of the current.  Zeros are padded in the upper-left and lower-right corners
        of the matrix (beginning/end of timeseries).
        In this case, the array shape will be (*n_pad*+n_bin),*n*
        
        """
        out=arr[...,:(self.n*self.n_bin)].reshape((self.n_inst,self.n,self.n_bin,),order='C')
        if n_pad==0:
            return out
        else:
            ndim=arr.ndim
            npd0=n_pad/2
            npd1=(n_pad+1)/2
            shp0=list(arr.shape[:-1]).extend([1,npd0])
            shp1=list(arr.shape[:-1]).extend([1,npd1])
            return np.concatenate((np.conconatenate((np.zeros(shp0),out[...,:-1,-npd0:]),ndim-1),out,np.concatenate((out[...,1:,:npd1],np.zeros(shp1)),ndim-1)),ndim)

