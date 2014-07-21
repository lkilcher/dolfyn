#!!!FIXTHIS: Need to update this file.
#from pylab import rcParams # Eventually this can be used for rcParams['text.usetex']:

class labeler(object):

    #def name(

    def __call__(self,meta):
        """
        
        """
        pass
    def get_label(self,form=None,units_style=None):
        """
        Get a formatted label for the variable.
        """
        unit=self.get_units(units_style=units_style)
        if unit is None:
            return '$'+self.get_numer()+'$'
        if form is None:
            form=r'$%s/[\mathrm{%s}]$'
        return form % (self.get_numer(),unit,)
        return 

    def get_units(self,units_style=None,):
        """
        Get the properly formatted units string.  
        """
        if self.scale!=0 and self._scale_place!='top':
            st=r'10^{%d}' % self.scale
        else:
            st=''
        if self._units is None:
            return None
        elif self._units.__class__ is str:
            return self._units
        elif self._units.has_key(None):
            return self._units[None]
        if units_style is None:
            units_style=self._units_style
        if units_style==0:
            ks=np.unique(np.array(self._units.values()))
            ups=np.sort([ks[ks>0]])[0][::-1]
            dns=np.sort([ks[ks<0]])[0]
            st=r''
            for ik in ups:
                for ky,vl in self._units.iteritems():
                    if vl==ik:
                        st+=ky
                        if ik!=1: # If the power is not 1, add an exponent:
                            st+='^{%d}' % ik
            for ik in dns:
                for ky,vl in self._units.iteritems():
                    if vl==ik:
                        st+='%s^{%d}' % (ky,ik)
            return st

class test(object):

    def __str__(self,):
        return 'g'
