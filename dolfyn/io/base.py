"""
The base module for the io package.
"""

from os.path import expanduser
import numpy as np
from ..data import base as db


class DataFactory(object):

    """
    An abstract base class for writing :class:`main.Saveable` objects.
    """
    closefile = True

    def __enter__(self,):
        """
        Allow data_factory objects to use python's 'with' statement.
        """
        return self

    def __exit__(self, type, value, trace):
        """
        Close the file at the end of the with statement.
        """
        if self.closefile:
            self.close()
            if hasattr(self, '_extrafiles'):
                for fl in self._extrafiles:
                    fl.close()

    @property
    def filename(self, ):
        return self._filename

    @filename.setter
    def filename(self, filename):
        self._filename = expanduser(filename)


class VarAtts(object):

    """
    A data variable attributes class.

    Parameters
    ----------

    dims : (list, optional)
        The dimensions of the array other than the 'time'
        dimension. By default the time dimension is appended to the
        end. To specify a point to place it, place 'n' in that
        location.

    dtype : (type, optional)
        The data type of the array to create (default: float32).

    group : (string, optional)
        The data group to which this variable should be a part
        (default: 'main').

    view_type : (type, optional)
        Specify a numpy view to cast the array into.

    default_val : (numeric, optional)
        The value to initialize with (default: use an empty array).

    offset : (numeric, optional)
        The offset, 'b', by which to adjust the data when converting to
        scientific units.

    factor : (numeric, optional)
        The factor, 'm', by which to adjust the data when converting to
        scientific units.

    title_name : (string, optional)
        The name of the variable\*\*.

    units : (:class:`<ma.unitsDict>`, optional)
        The units of this variable\*\*.

    dim_names : (list, optional)
        A list of names for each dimension of the array\*\*.

    Notes
    -----

    \*\*: These variables are only used when meta-arrays are being
    used by DOLfYN (meta-arrays are currently sidelined).

    """

    def __init__(self, dims=[], dtype=None, group='main',
                 view_type=None, default_val=None,
                 offset=0, factor=1,
                 title_name=None, units=None, dim_names=None,
                 ):
        self.dims = list(dims)
        if dtype is None:
            dtype = np.float32
        self.dtype = dtype
        self.group = group
        self.view_type = view_type
        self.default_val = default_val
        self.offset = offset
        self.factor = factor
        self.title_name = title_name
        self.units = units
        self.dim_names = dim_names

    def shape(self, n):
        if 'n' in self.dims:
            a = list(self.dims)
            a[self.dims.index('n')] = n
        else:
            return self.dims + [n]

    def _empty_array(self, n):
        out = np.empty(self.shape(n), dtype=self.dtype)
        if self.view_type is not None:
            out = out.view(self.view_type)
        if self.default_val is not None:
            out[:] = self.default_val
        return out

    def sci_func(self, data):
        """Scale the data to scientific units.

        Parameters
        ----------
        data : :class:`<numpy.ndarray>`
            The data to scale.

        Returns
        -------
        retval : {None, data}
          If this funciton modifies the data in place it returns None,
          otherwise it returns the new data object.
        """
        if self.offset != 0:
            data += self.offset
        if self.factor != 1:
            data *= self.factor
        if db.ma.valid:
            data = db.ma.marray(data,
                                db.ma.varMeta(self.title_name,
                                              self.units,
                                              self.dim_names)
                                )
            return data


if __name__ == '__main__':
    # filename='/home/lkilcher/data/eastriver/advb_10m_6_09.h5'
    filename = '/home/lkilcher/data/ttm_dem_june2012/\
    TTM_Vectors/TTM_NRELvector_Jun2012_b5m.h5'
    import adv
    ldr = adv.loader(filename, adv.type_map)
    dat = ldr.load()
