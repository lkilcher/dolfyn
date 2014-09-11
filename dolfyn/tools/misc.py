import numpy as np
from scipy.signal import medfilt2d


class delta(object):

    """
    delta objects are for creating boolean 'index' arrays. For an input data.
    """

    @property
    def shape(self,):
        return self.data.shape

    def __init__(self, data, delta):
        """
        Creat a delta object for *data* with delta *delta*.
        """
        self.data = data
        self.delta = delta

    def __call__(self, val):
        """
        Return the indices of `data` that fall within `val`- delta to
        `val` + delta.
        """
        return (val - self.delta < self.data) & (self.data < val + self.delta)

    def abs(self, val):
        return ((val - self.delta < np.abs(self.data)) &
                (np.abs(self.data) < val + self.delta))


def slice1d_along_axis(arr_shape, axis=0):
    """
    Return an iterator object for looping over 1-D slices, along *axis*, of
    an array of shape arr_shape.

    Parameters
    ----------
    arr_shape : tuple,list
        Shape of the array over which the slices will be made.
    axis : integer
        Axis along which `arr` is sliced.

    Returns
    -------
    Iterator object.
    The iterator object returns slice objects which slices arrays of
    shape arr_shape into 1-D arrays.

    See Also
    --------
    apply_over_axis : Apply a function to 1-D slices along the given axis.
    apply_over_axes : Apply a function repeatedly over multiple axes.

    Examples
    --------

    >>> out=np.empty(replace(arr.shape,0,1))
    >>> for slc in slice1d_along_axis(arr.shape,axis=0):
            out[slc]=my_1d_function(arr[slc])

    """
    nd = len(arr_shape)
    if axis < 0:
        axis += nd
    ind = [0] * (nd - 1)
    i = np.zeros(nd, 'O')
    indlist = range(nd)
    indlist.remove(axis)
    i[axis] = slice(None)
    itr_dims = np.asarray(arr_shape).take(indlist)
    Ntot = np.product(itr_dims)
    i.put(indlist, ind)
    k = 0
    while k < Ntot:
        # increment the index
        n = -1
        while (ind[n] >= itr_dims[n]) and (n > (1 - nd)):
            ind[n - 1] += 1
            ind[n] = 0
            n -= 1
        i.put(indlist, ind)
        yield tuple(i)
        ind[-1] += 1
        k += 1


def fillgaps(a, maxgap=np.inf, dim=0, extrapFlg=False):
    """
    out=fillgaps(A,MAXGAP,DIM) Fills gaps in A by linear
    interpolation along dimension DIM.  The maximum gap width
    to be filled is specified by MAXGAP.

    MAXGAP defualts to fill gaps of any width.

    DIM defaults to 0."""

    # If this is a multi-dimensional array, operate along axis dim.
    if a.ndim > 1:
        for inds in slice1d_along_axis(a.shape, dim):
            fillgaps(a[inds], maxgap, 0, extrapFlg)
        return

    a = np.asarray(a)
    nd = a.ndim
    if dim < 0:
        dim += nd
    if (dim >= nd):
        raise ValueError("dim must be less than a.ndim; dim=%d, rank=%d."
                         % (dim, nd))
    ind = [0] * (nd - 1)
    i = np.zeros(nd, 'O')
    indlist = range(nd)
    indlist.remove(dim)
    i[dim] = slice(None, None)
    # outshape = np.asarray(a.shape).take(indlist)
    # Ntot = np.product(outshape)
    i.put(indlist, ind)
    # k = 0

    gd = np.nonzero(~np.isnan(a))[0]

    # Here we extrapolate the ends, if necessary:
    if extrapFlg and gd.__len__() > 0:
        if gd[0] != 0 and gd[0] <= maxgap:
            a[:gd[0]] = a[gd[0]]
        if gd[-1] != a.__len__() and (a.__len__() - (gd[-1] + 1)) <= maxgap:
            a[gd[-1]:] = a[gd[-1]]

    # Here is the main loop
    if gd.__len__() > 1:
        inds = np.nonzero((1 < np.diff(gd)) & (np.diff(gd) <= maxgap + 1))[0]
        for i2 in range(0, inds.__len__()):
            ii = range(gd[inds[i2]] + 1, gd[inds[i2] + 1])
            a[ii] = (np.diff(a[gd[[inds[i2], inds[i2] + 1]]]) *
                     (np.arange(0, ii.__len__()) + 1) /
                     (ii.__len__() + 1) + a[gd[inds[i2]]]).astype(a.dtype)


def medfiltnan(a, kernel, thresh=0):
    """
    Do a running median filter of the data.

    Regions where more than *thresh* fraction of the points NaN, are
    set to NaN.

    Currently only work for vectors.
    """
    nans = np.isnan(a)
    nans = np.convolve(nans, np.ones(kernel) / kernel, 'same')
    bds = nans > thresh
    out = medfilt2d(a[None, :], (1, kernel))[0]
    out[bds] = np.NaN
    return out


def degN2cartDeg(angN,):
    out = 90 - angN
    out[out < -180] += 360
    return out
