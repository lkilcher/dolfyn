from ..data import velocity as dbvel
import numpy as np
import warnings
import xarray as xr


def diffz_first(dat, z, axis=0):
    return np.diff(dat, axis=0) / (np.diff(z)[:, None])

# def diffz_centered(dat,z,axis=0):
#    return np.diff(dat,axis=0)/(np.diff(z)[:,None])


#@xr.register_dataset_accessor('ADPdata')
class ADPdata(dbvel.Velocity):
    """The acoustic Doppler profiler (ADP) data type.

    See Also
    ========
    :class:`dolfyn.Velocity`

    """
    diff_style = 'first'

    def _diff_func(self, nm):
        if self.diff_style == 'first':
            return diffz_first(getattr(self, nm), self['range'])
        # else:
        #     pass
        #     #!!!FIXTHIS. Need the diffz_centered operator.
        #     # return diffz_centered(getattr(self, nm), self.z)

    @property
    def range_diff(self,):
        if self.diff_style == 'first':
            return self['range'][0:-1] + np.diff(self['range']) / 2
        else:
            return self['range']

    @property
    def dudz(self,):
        """The shear in the first velocity component.

        Notes
        =====
        The derivative direction is along the profiler's 'z'
        coordinate ('dz' is actually diff(self['range'])), not necessarily the
        'true vertical' direction.

        """
        return self._diff_func('u')

    @property
    def dvdz(self,):
        """The shear in the second velocity component.

        Notes
        =====
        The derivative direction is along the profiler's 'z'
        coordinate ('dz' is actually diff(self['range'])), not necessarily the
        'true vertical' direction.

        """
        return self._diff_func('v')

    @property
    def dwdz(self,):
        """The shear in the third velocity component.

        Notes
        =====
        The derivative direction is along the profiler's 'z'
        coordinate ('dz' is actually diff(self['range'])), not necessarily the
        'true vertical' direction.

        """
        return self._diff_func('w')

    @property
    def S2(self,):
        """The horizontal shear-squared.

        Notes
        =====
        This is actually (dudz)^2 + (dvdz)^2. So, if those variables
        are not actually vertical derivatives of the horizontal
        velocity, then this is not the 'horizontal shear-squared'.

        See Also
        ========
        :meth:`dvdz`, :meth:`dudz`

        """
        return self.dudz ** 2 + self.dvdz ** 2

# Bother updating this?, because TurbBinner does the same things
class ADPbinner(dbvel.VelBinner):
    """An ADP binning (averaging) tool.

    """
    def __call__(self, adpr):
        out = type(adpr)()
        out = self.do_avg(adpr, out)

        noise = adpr.get('doppler_noise', [0, 0, 0])
        
        # Currently this doesn't happen because the functions below
        # need beamvel and angles.
        #if hasattr(indat.config, 'beam_angle') and hasattr(indat, 'beam1vel'):
        if False: # also note there are calc_tke and calc_stress in VelBinner
            out['tke_vec'] = self.calc_tke(adpr['vel'], noise=noise)
            out.calc_stress(adpr)
            
        out.attrs['n_bin'] = self.n_bin
        out.attrs['n_fft'] = self.n_fft
        out.attrs['n_fft_coh'] = self.n_fft_coh
            
        return out

    # def calc_tke(self, advr):
    #     """
    #     Calculate the variance of the velocity vector.
    #     """
    #     self.tke_vec = np.nanmean(self.demean(advr['vel']) ** 2, axis=-1)
    #     # These are the beam rotation constants, multiplied by
    #     # sqrt(num_beams_in_component), to give the error (we are
    #     # adding/subtracting 2,2 and 4 beams in u,v, and w.
    #     if 'doppler_noise' in self.props.keys:
    #         if dict not in self.props['doppler_noise'].__class__.__mro__:
    #             erruv = self.props['doppler_noise'] / 2 / np.sin(
    #                 self.config.beam_angle * np.pi / 180) * 2 ** 0.5
    #             errw = self.props['doppler_noise'] / 4 / np.cos(
    #                 self.config.beam_angle * np.pi / 180) * 2
    #             self.upup_ -= erruv ** 2
    #             self.vpvp_ -= erruv ** 2
    #             self.wpwp_ -= errw ** 2
    #         else:
    #             self.upup_ -= self.props['doppler_noise']['u'] ** 2
    #             self.vpvp_ -= self.props['doppler_noise']['v'] ** 2
    #             self.wpwp_ -= self.props['doppler_noise']['w'] ** 2
    #     # self.meta['upup_']=db.varMeta("u'u'",{2:'m',-2:'s'})
    #     # self.meta['vpvp_']=db.varMeta("v'v'",{2:'m',-2:'s'})
    #     # self.meta['wpwp_']=db.varMeta("w'w'",{2:'m',-2:'s'})


    def calc_epsilon_SFz(self, vel_raw, vel_avg, r=2, noise=0):
        """
        Calculate dissipation rate using the "structure function" (SF) method.
        Currently limited to caculating off a single beam at a time
        
        Parameters
        ----------
        
        vel_raw : |xr.DataArray|
          The raw beam velocity data (last dimension time) upon 
          which to perform the SF technique. 

        vel_avg : |xr.DataArray|
          The bin-averaged beam velocity (calc'd from 'do_avg')
                                          
        r: 
            Vertical dist [m] to calc dissipation from structure function
        
        noise:
            Dopper noise [m/s]
        
        Returns
        -------

        epsilon : |xr.DataArray|
          The dissipation rate
        
        Notes
        -----
               
        Wiles, et al, "A novel technique for measuring the rate of 
        turbulent dissipation in the marine environment"
        GRL, 2006, 33, L21608.
        
        """        
        # self.ds here is binned averaged velocity (from do_avg)
        e = np.empty(vel_avg.shape, dtype='float32')
        D = np.empty(vel_avg.shape) # should be [beam, [range, time]
        
        # bm shape is [range, ensemble time, 'data within ensemble']
        bm = self.reshape(vel_raw.values) # will fail if not in beam coord
        bm -= vel_avg.values[:,:,None] # take out the ensemble mean

        #for ind in range(veldat.shape[0]-1): # one beam at a time
        # should be velocity variance
        #bm = self._reshape(veldat.sel(orient=ind+1).values) # will fail if not in beam coord
        #bm -= self.ds.vel.isel(orient=ind+1).values[:,:,None] # take out the ensemble mean

        for idx in range(len(vel_avg.time)): # for each ensemble
            # subtract the var of adjacent depth cells and avg each ensemble
            # the '1' in d should be a variable of r, r/np.diff(range) or something?
            d = np.nanmean((bm[:-1,idx,:] - bm[1:,idx,:]) ** 2, axis=-1)
            # have to insert 0 in first bin to match length
            #D[ind,:,idx] = np.insert(tmp, obj=0, values=0)
            D[:,idx] = np.insert(d, obj=0, values=0) + noise
        
            # plt.plot(D[:,idx], r**(2/3))

        #e[ind,...] = (2.1 * D[ind] * r**(3/2)) ** (3/2)
        e = (1/2.1 * D * r**(-2/3)) ** (3/2)
        
        return xr.DataArray(e, coords=vel_avg.coords,
                            dims=vel_avg.dims,
                            attrs={'units':'m^2/s^3',
                                  'method':'structure function'})
            

    def calc_ustar_fitstress(self, dinds=slice(None), H=None):
        if H is None:
            H = self.depth_m[:][None, :]
        sgn = np.sign(self.upwp_[dinds].mean(0))
        self.ustar = (sgn * self.upwp_[dinds] / (
            1 - self['range'][dinds][:, None] / H)).mean(0) ** 0.5
        # p=polyfit(self.hab[dinds],sgn*self.upwp_[dinds],1)
        # self.ustar=p[1]**(0.5)
        # self.hbl_fit=p[0]/p[1]
        

    def calc_stress(self, beamvel, beamAng):
        """
        Calculate the stresses from the difference in the beam variances.

        Reference: Stacey, Monosmith and Burau; (1999) JGR [104]
        "Measurements of Reynolds stress profiles in unstratified
        tidal flow"
        """
        fac = 4 * np.sin(np.deg2rad(self.config.beam_angle)) * \
            np.cos(np.deg2rad(self.config.beam_angle))
        # Note: Stacey defines the beams incorrectly for Workhorse ADCPs.
        #       According to the workhorse coordinate transformation
        #       documentation, the instrument's:
        #                        x-axis points from beam 1 to 2, and
        #                        y-axis points from beam 4 to 3.
        #       Therefore:
        stress = ((np.nanvar(self.reshape(beamvel[0]), axis=-1) -
                   np.nanvar(self.reshape(beamvel[1]), axis=-1)) + 1j *
                  (np.nanvar(self.reshape(beamvel[2]), axis=-1) -
                   np.nanvar(self.reshape(beamvel[3]), axis=-1))
                  ) / fac
        if self.config.orientation == 'up':
            # This comes about because, when the ADCP is 'up', the u
            # and w velocities need to be multiplied by -1 (equivalent
            # to adding pi to the roll).  See the coordinate
            # transformation documentation for more info.
            #
            # The uw (real) component has two minus signs, but the vw (imag)
            # component only has one, therefore:
            stress.imag *= -1

        # !FIXTHIS!:
        # - Stress rotations should be **tensor rotations**.
        # - These should be handled by rotate2.
        warnings.warn("The calc_stresses function does not yet "
                      "properly handle the coordinate system.")
        return stress.real, stress.imag
