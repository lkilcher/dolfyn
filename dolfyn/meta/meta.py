# from labels import default_labeler
import numpy as np
from six import string_types


class unitsDict(dict):

    """
    A dictionary sub-class for tracking units.

    unitsDict instances support simple math operations (multiply,
    divide, power)

    The *key* of unitsDicts objects are the units, the values
    represent the power of that unit.  For example:
       a unitsDict({'s':-1,'m':1}) object represents units of m/s.
    """

    def copy(self,):
        """
        Return a shallow copy of the present object.
        """
        return unitsDict([(ky, val) for ky, val in list(self.items())])

    def __mul__(self, other):
        """
        Multiple the units in this instance by the units in the *other* object.
        """
        out = self.copy()
        if other.__class__ is unitsDict:
            for u, vl in list(other.items()):
                if u in list(out.keys()):
                    out[u] += vl
                else:
                    out[u] = vl
        return out

    def __pow__(self, other):
        """
        Raise the units in this object to the power of *other*.
        """
        out = self.copy()
        for u in self:
            out[u] *= other
        return out

    def __div__(self, other):
        """
        Divide the units in this instance by the units in the *other* object.
        """
        out = self.copy()
        if other.__class__ is unitsDict:
            for u, vl in list(other.items()):
                if u in list(out.keys()):
                    out[u] -= vl
                else:
                    out[u] = -vl
        return out


class varMeta(object):

    """
    A class for variable metadata.

    In particular, the units and name of the variable are stored here.

    *units_style* specifies how to format the units.
       0: no fractions (e.g. units of acceleration are: ms^{-2})
       1: fractions    (e.g. units of acceleration are: m/s^{2})
       ***Currently only units_style=0 is supported.***
    """
    _units_style = 0
    latex = True
    _scale_place = 'top'
    dim_names = []

    def __eq__(self, other):
        """
        Test for equivalence between varMeta objects.
        """
        if (other.__class__ is varMeta and
            self.name == other.name and
                self._units == other._units):
            return True
        return False

    def __mul__(self, other):
        out = self.copy()
        out.name = self.name + other.name
        out._units = self._units * other._units
        return out

    def __pow__(self, other):
        out = self.copy()
        out.name = self.name + '^%d' % (other)
        out._units = self._units ** other
        return out

    def __div__(self, other):
        out = self.copy()
        if other.name != '':
            out.name = self.name + '/' + other.name
        out._units = self._units / other._units
        return out

    def __init__(self, name, units=None, dim_names=[],
                 units_style=None, scale=0, vecnames={}):
        self.vecnames = vecnames
        self.dim_names = dim_names
        if units.__class__ is not unitsDict:
            self._units = unitsDict(units)
        elif isinstance(units, string_types):
            self._units = unitsDict({units: 1})
        else:
            self._units = units
        self.name = name
        self.xformat = r'$%s/[\mathrm{%s}]$'
        self.scale = scale
        if units_style is not None:
            self._units_style = units_style
        self.yformat = r'$%s/[\mathrm{%s}]$'

    def _copy_rep(self, name=None):
        """
        A copy method for use in constructing new varMeta objects from
        a basic type.

        It behaves as follows:
        1) If self.name is None, it return None.
        2) If the input is None, it returns a copy of itself.
        3) Otherwise, it does a % replace of self.name with the input.
           e.g. this is for use such as:
           vm=varMeta(r"\overline{%s'%s'}",{'m':2,'s':-2})
           vm._copy_rep(('u','u'))
        """
        if self.name is None:
            return None
        if name is None:
            name = self.name
        else:
            name = self.name % name
        return varMeta(name,
                       (self._units and self._units.copy()),
                       list(self.dim_names),
                       self._units_style,
                       self.scale)

    def copy(self, name=None):
        """
        Return a copy of this varMeta object.

        Optional variable *name* may be used to create a copy of these
        units, with a new 'name'.
        """
        if self.name is None and name is None:
            return None
        if name is None:
            name = self.name
        return varMeta(name,
                       (self._units and self._units.copy()),
                       list(self.dim_names),
                       self._units_style,
                       self.scale)

    def __repr__(self,):
        return "<varMeta for %s (%s)>" % (self.name, self.units)

    def get_label(self, form=None, units_style=None):
        """
        Get a formatted label for the variable.
        """
        unit = self.get_units(units_style=units_style)
        if unit is None:
            return '$' + self.get_numer() + '$'
        if form is None:
            form = r'$%s/[\mathrm{%s}]$'
        return form % (self.get_numer(), unit,)

    def get_numer(self,):
        if self.scale != 0 and self._scale_place == 'top':
            return '10^{%d}%s' % (-self.scale, self.name)
        else:
            return self.name

    @property
    def units(self,):
        """
        A shortcut to the units string.
        """
        return self.get_units()

    @property
    def label(self,):
        """
        A shortcut to the label.
        """
        return self.get_label()

    @property
    def ylabel(self,):
        """
        A shortcut to the ylabel.
        """
        return self.get_label(form=self.yformat)

    @property
    def xlabel(self,):
        """
        A shortcut to the xlabel.
        """

        return self.label

    def get_units(self, units_style=None,):
        """
        Get the properly formatted units string.
        """
        if self.scale != 0 and self._scale_place != 'top':
            st = r'10^{%d}' % self.scale
        else:
            st = ''
        if self._units is None:
            return None
        elif self._units.__class__ is str:
            return self._units
        elif None in self._units:
            return self._units[None]
        if units_style is None:
            units_style = self._units_style
        if units_style == 0:
            ks = np.unique(np.array(self._units.values()))
            ups = np.sort([ks[ks > 0]])[0][::-1]
            dns = np.sort([ks[ks < 0]])[0]
            st = r''
            for ik in ups:
                for ky, vl in list(self._units.items()):
                    if vl == ik:
                        st += ky
                        if ik != 1:  # If the power is not 1, add an exponent:
                            st += '^{%d}' % ik
            for ik in dns:
                for ky, vl in list(self._units.items()):
                    if vl == ik:
                        st += '%s^{%d}' % (ky, ik)
            return st
