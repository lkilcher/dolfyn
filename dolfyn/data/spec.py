from .base import SourceDataType, np, ma
from ..OrderedSet import OrderedSet as oset


# In general, these are not savable objects (for now?).
class specobj(SourceDataType):

    @property
    def _data_groups(self,):
        if not hasattr(self, '__data_groups__'):
            self.__data_groups__ = {
                'spec': oset(['Suu', 'Svv', 'Sww']),
                '_essential': oset(['freq'])
            }
        return self.__data_groups__

    def __getitem__(self, ind):
        if ind.__class__ is int:
            return getattr(self, list(self.specvars)[ind])
        return getattr(self, ind)

    @property
    def shape(self,):
        return getattr(self, self.specvars[0]).shape

    def __len__(self,):
        return len(self.specvars)

    def __iter__(self,):
        for nm in self.specvars:
            yield self[nm]

    def iter4axgroup(self,):
        for nm, dat in self.iter_wd:
            if ma.valid and dat.__class__ is ma.marray:
                yield (self.freq, np.rollaxis(dat, dat.getax('freq')))
            else:
                yield (self.freq, np.rollaxis(dat, -1))

    @property
    def specvars(self,):
        # if not self._data_groups.has_key('spec'):
        #    self._data_groups['spec']=oset(['Suu','Svv','Sww'])
        return list(self._data_groups['spec'])

    @specvars.setter
    def specvars(self, val):
        self._data_groups['spec'] = oset(val)

    def __div__(self, other):
        out = self.copy()
        for nm in self.specvars:
            setattr(out, nm, getattr(out, nm) / other)
        return out

    def __isub__(self, other):
        for nm in self.specvars:
            self[nm] -= other
        return self

    def __iadd__(self, other):
        for nm in self.specvars:
            self[nm] += other
        return self

    def __pow__(self, other):
        out = self.copy()
        for nm in self.specvars:
            setattr(out, nm, getattr(out, nm) ** other)
        return out

    def __mul__(self, other):
        out = self.copy()
        for nm in self.specvars:
            if other.__class__ is specobj:
                sdat, odat, dims = out[nm].matchdims(other[nm])
                setattr(out, nm, sdat * odat)
                out[nm].meta.dim_names = dims
            else:
                setattr(out, nm, getattr(out, nm) * other)
        return out

    def trapz(self, inds=slice(None)):
        if inds.__class__ is not dict:
            inds = {nm: inds for nm in self.specvars}
        out = self.copy()
        for nm in out.specvars:
            dims = out[nm].meta.dim_names
            ax = out[nm].getax('freq')
            dims.pop(ax)
            out[nm] = np.trapz(
                out[nm][..., inds[nm]], out.freq[inds[nm]], axis=ax)
            out[nm].meta.dim_names = dims
        return out

    @property
    def iter_wd(self,):
        for nm in self.specvars:
            yield nm, getattr(self, nm)

    def __repr__(self,):
        return ("<specobj: " + len(self.specvars) * '%s, ' + '(%s)>') % \
            tuple(self.specvars + [self.freq.meta.name])

    def mean(self, axis='time'):
        out = self.copy()
        for nm, dat in self.iter_wd:
            setattr(out, nm, dat.mean(axis))
        return out


class cohereobj(specobj):

    @property
    def _data_groups(self,):
        if not hasattr(self, '__data_groups__'):
            self.__data_groups__ = {
                'spec': oset(['Coh_uu', 'Coh_vv', 'Coh_ww']),
                '_essential': oset(['freq'])
            }
        return self.__data_groups__

rad_per_cyc = ma.marray(
    2 * np.pi, meta=ma.varMeta('', {'hz': -1, 's': -1}, []))


def specobj_hz2rad(obj):
    for val in obj:
        val *= rad_per_cyc ** -1
    obj.freq *= rad_per_cyc
    if ma.valid and obj.freq.__class__ is ma.marray:
        obj.freq.meta._name = '\omega'
    return obj


def specobj_rad2hz(obj):
    for val in obj:
        val *= rad_per_cyc
    obj.freq *= rad_per_cyc ** -1
    if ma.valid and obj.freq.__class__ is ma.marray:
        obj.freq.meta._name = 'f'
    return obj


def denoise_specobj(obj, vals, renoise=False):
    sgn = 1
    if renoise:
        sgn = -1
    if dict in vals.__class__.__mro__:
        vals = [vals['u'], vals['v'], vals['w']]
    if not hasattr(vals, '__len__'):
        vals = [vals]
    if len(vals) < len(obj) and len(vals) == 1:
        vals *= len(obj)
    for nm, val in zip(obj.specvars, vals):
        setattr(obj, nm, getattr(obj, nm) - sgn * val ** 2 / obj.freq[-1])
    return obj


def ind_specobj(dat, inds=slice(None), typeobj=specobj,
                names=None, freqvar='omega', dflt_ax=0):
    """
    A specobj constructor.

    The object *dat* must contain the attributes in *names*, and the *freqvar*.

    It takes the indices from *dat* along the "time" axis to include in the
    returned *specobj*.

    """
    out = typeobj()
    tup = False

    if names is None:
        # This pulls the defaults from the chosen specobj.
        names = out.specvars
        nms = names
    else:
        if names[0].__class__ is tuple:
            tup = True
            nms = []
            for idx, (nm, indxs) in enumerate(names):
                nms += [nm + '%d' % (idx)]
        else:
            nms = names
        out.specvars = nms

    if dflt_ax.__class__ is not dict:
        dflt_ax = {nm: dflt_ax for nm in out.specvars}

    if np.ndarray in inds.__class__.__mro__ and inds.dtype == 'bool':
        inds = np.nonzero(inds)[0]

    for nm, nmo in zip(names, nms):
        if freqvar == 'freq':
            nm += '_f'
        if tup:
            dnow = dat[nm[0]][nm[1]]
            nm = nm[0]
        else:
            dnow = dat[nm]

        if ma.valid and dnow.__class__ is ma.marray:
            ax = dnow.getax('time', None)
        else:
            ax = dflt_ax[nmo]

        if ax is None or (inds.__class__ is slice and inds == slice(None)):
            out.add_data(nmo, dnow)
        else:
            out.add_data(nmo, dnow.take(inds, ax))

    out.freq = dat[freqvar]
    out._data_groups['_essential'] |= ['freq']
    return out


def mean_specobj(dat, inds=slice(None), *args, **kwargs):
    """
    A specobj constructor, that returns an average over the *inds*.

    See also:
    ind_specobj

    """
    a = ind_specobj(dat, inds, *args, **kwargs)
    out = a.mean()
    del a
    return out
