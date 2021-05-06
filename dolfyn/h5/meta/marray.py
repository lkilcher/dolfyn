import numpy as np
from .meta import varMeta
"""
marray.py is a module for adding meta data to numpy's array objects.
In particular, the meta data tracked by this package is:
    units     - The units of a variable
    dim_names - The names of the dimensions of an array.
    name      - A string that is used in labels for the data in the array.  This is a
                math-mode LaTeX string (dollar signs are added).
    vecnames  - A list of strings that are different names for specific indices of an axis.
                e.g. for the 'xyz' dimension, you could define vecnames={'xyz'=['u','v','w']}
"""


class marray(np.ndarray):

    # def cat(self,other,axis=0):
    # """
    # Catenate two arrays.
    # """
    # return marray(np.concatenate((self,other),axis),self.meta)

    def __getitem__(self, slc):
        out = super(marray, self).__getitem__(slc)
        if np.ndarray in out.__class__.__mro__ and (out.ndim > 0 and out.ndim < self.ndim):
            # Get data from an array, with care for removing dims from
            # meta.dim_names when this operation reduces the dimension of the
            # array.
            if slc.__class__ is not tuple:
                out.meta.dim_names = out.meta.dim_names[1:]
            else:
                dms = []
                for idx, val in enumerate(slc):
                    if int not in val.__class__.__mro__:
                        try:
                            dms += [self.meta.dim_names[idx]]
                        except:
                            pass
                out.meta.dim_names = dms
            # print( out.ndim,self.ndim,slc # This code causes print statements
            # when the _variable_ is printed because the print statement calls
            # __getitem__. )
        return out

    def var(self, axis=None, dtype=None, out=None, ddof=0):
        if axis is None:
            dims = []
        else:
            dims = list(self.meta.dim_names)
            dims.pop(axis)
        return marray(np.ndarray.var(self, axis=axis,
                                     dtype=dtype, out=out, ddof=ddof),
                      varMeta(2 * (self.meta._name + "'"),
                              units=self.meta._units**2, dim_names=dims))

    def matchdims(self, other):
        dims = self.meta.dim_names
        dimo = other.meta.dim_names
        shps = [None] * len(np.unique(dims + dimo))
        shpo = [None] * len(np.unique(dims + dimo))
        dmo = []
        print((dims, dimo, ))
        for d in dims:
            if d in dimo:
                ind = dimo.index(d) + 1
                dmo += dimo[:ind]
                shps[len(dmo) - 1] = slice(None)
                shpo[len(dmo) - ind:len(dmo)] = [slice(None)] * ind
                dimo = dimo[ind:]
            else:
                dmo += [d]
                shps[len(dmo)] = [slice(None)]
        dmo += dimo
        if len(dimo):
            shpo[-len(dimo):] = [slice(None)] * len(dimo)
        shpo = tuple(shpo)
        shps = tuple(shps)
        return self[shps], other[shpo], dmo

    def getdim(self, name, dflt=None):
        """
        Get the axis number with meta.dim_name *name*.

        If meta.dim_names does not contain *name*, None is returned.
        Use the optional input *dflt* to specify a different output in this case.
        if *dflt*=='__error__', this will raise a ValueError.
        """
        if dflt != '__error__':
            try:
                return self.meta.dim_names.index(name)
            except ValueError:
                return dflt
        else:
            return self.meta.dim_names.index(name)

    def mean(self, axis=None, dtype=None, out=None):
        """
        *axis* can be a string indicating the dim_name (in meta.dim_names).

        If *axis* is a string, and it is not in dim_names, a copy of the array is returned.

        Refer to `numpy.mean` for full documentation
        """
        if axis.__class__ is str:
            axis = self.getdim(axis, None)
            if axis is None:
                return self.copy()
        if out is not None:
            super(marray, self,).mean(axis, dtype, out)
        else:
            out = super(marray, self,).mean(axis, dtype)
        if axis is None:
            out.meta.dim_names = []
        else:
            out.meta.dim_names.pop(axis)
        return out

    def std(self, axis=None, dtype=None, out=None, ddof=0):
        """
        The axis along which the mean is taken can be a string
        indicating the dim_name (in meta.dim_names).

        Refer to `numpy.std` for full documentation
        """
        if axis.__class__ is str:
            axis = self.getdim(axis, '__error__')
        if out is not None:
            super(marray, self,).std(axis, dtype, out, ddof)
        else:
            out = super(marray, self,).std(axis, dtype, out, ddof)
        if axis is None:
            out.meta.dim_names = []
        else:
            out.meta.dim_names.pop(axis)
        return out

    def __repr__(self,):
        if self.ndim == 0 or len(self) <= 1:
            return ("marray(%s, <%s[%s], %s%s:%s>)" %
                    (self.__str__(), self.meta.name, self.units,
                     self.dtype, self.shape, self.meta.dim_names))
        return ("marray(%s, <%s[%s], %s%s:%s>)" %
                (self.__str__(), self.meta.name, self.units,
                 self.dtype, self.shape, self.meta.dim_names))

    @property
    def name(self,):
        return self.meta.name

    @property
    def unit_label(self,):
        return '$\mathrm{[' + self.units + ']}$'

    @property
    def units(self,):
        return self.meta.units

    @property
    def label(self,):
        return self.meta.label

    def __imul__(self, other):
        super(marray, self).__imul__(other)
        if hasattr(other, 'meta') and other.meta.__class__ is varMeta:
            self.meta = self.meta * other.meta
        return self

    def __rmul__(self, other):
        if other.__class__ is not marray:
            # Cast to normal array if the first object is not an marray:
            return np.array(self).__mul__(other)
        return self.__mul__(other)

    def __rdiv__(self, other):
        if other.__class__ is not marray:
            # Cast to normal array if the first object is not an marray:
            return np.array(self).__rdiv__(other)
        return super(marray, self).__rdiv__(other)

    def __mul__(self, other):
        # if other.__class__ is marray:
        # sdat,odat,dims=self.matchdims(other)
        # out=super(marray,sdat).__mul__(odat)
        # out.meta=self.meta*other.meta
        # out.meta.dim_names=dims
        # return out
        # else:
        out = super(marray, self).__mul__(other)
        if other.__class__ is marray:
            out.meta = self.meta * other.meta
        return out

    def __div__(self, other):
        out = super(marray, self).__div__(other)
        if hasattr(other, 'meta') and other.meta.__class__ is varMeta:
            out.meta = self.meta / other.meta
        return out

    def __pow__(self, *args):
        out = super(marray, self).__pow__(*args)
        out.meta = self.meta**args[0]
        return out

    def __new__(cls, input_array, meta=varMeta('None')):
        # Input array is an already formed ndarray instance
        # We first cast it to be our class type
        obj = np.asarray(input_array).view(cls)
        # add the new attribute to the created instance
        obj.meta = meta
        # Finally, we must return the newly created object:
        return obj

    def __array_finalize__(self, obj):
        # see InfoArray.__array_finalize__ for comments
        if obj is None:
            return
        tmp = getattr(obj, 'meta', None)
        if tmp.__class__ is varMeta:
            self.meta = tmp.copy()
        else:
            self.meta = tmp
