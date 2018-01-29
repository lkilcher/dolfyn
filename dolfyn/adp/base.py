from ..data import velocity as dbvel
from ..data.time import num2date
import numpy as np
from . import rotate

deg2rad = np.pi / 180


def diffz_first(dat, z, axis=0):
    return np.diff(dat, axis=0) / (np.diff(z)[:, None])

# def diffz_centered(dat,z,axis=0):
#    return np.diff(dat,axis=0)/(np.diff(z)[:,None])


class adcp_raw(dbvel.Velocity):

    """
    The base 'adcp' class.

    """
    diff_style = 'first'

    def _diff_func(self, nm):
        if self.diff_style == 'first':
            return diffz_first(getattr(self, nm), self.z)
        # else:
        #     pass
        #     #!!!FIXTHIS. Need the diffz_centered operator.
        #     # return diffz_centered(getattr(self, nm), self.z)

    @property
    def z(self, ):
        return self['range']

    @property
    def zd(self,):
        if self.diff_style == 'first':
            return self.z[0:-1] + np.diff(self.z) / 2
        else:
            return self.z

    @property
    def dudz(self,):
        return self._diff_func('u')

    @property
    def dvdz(self,):
        return self._diff_func('v')

    @property
    def dwdz(self,):
        return self._diff_func('w')

    @property
    def S2(self,):
        return self.dudz ** 2 + self.dvdz ** 2

    @property
    def _repr_header(self, ):
        if (not hasattr(self, 'mpltime')) or self.mpltime[0] < 1:
            print('Warning: no time information!')
            dt = num2date(693596)
            tm = np.array([0, 0])
        else:
            tm = [self.mpltime[0], self.mpltime[-1]]
            dt = num2date(tm[0])
        return ("<ADP data object>\n"
                "  . %0.2f hours (started: %s)\n"
                "  . %s-frame\n"
                "  . (%s bins, %s pings)\n" %
                ((tm[-1] - tm[0]) * 24,
                 dt.strftime('%b %d, %Y %H:%M'),
                 self.props['coord_sys'],
                 self.shape[0],
                 self.shape[1]))


class adcp_binned(dbvel.VelBindatTke, adcp_raw):
    inds = slice(None)


class binner(dbvel.VelBinnerTke):

    def __call__(self, indat, out_type=adcp_binned):
        out = dbvel.VelBinnerTke.__call__(self, indat, out_type=out_type)
        self.do_avg(indat, out)
        out.add_data('tke_vec',
                     self.calc_tke(indat['vel'], noise=indat.noise),
                     'main')
        out.add_data('sigma_Uh',
                     np.sqrt(np.var(
                         self.reshape(indat.U_mag), -1, dtype=np.float64) -
                         (indat.noise[0] ** 2 + indat.noise[1] ** 2) / 2),
                     'main')
        # This means it is a workhorse, created with adcp.readbin.  Need to
        # generalize this...
        # Currently this doesn't happen because the functions below
        # need beamvel and angles.
        #if hasattr(indat.config, 'beam_angle') and hasattr(indat, 'beam1vel'):
        if False:
            out.calc_stresses(indat)
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

    # def _calc_eps_sfz(self, adpr):
    #     """

    #     """
    #     # !!!FIXTHIS: Currently, this function is in a debugging state,
    #     # and is non-functional.

    #     # It seems that it might work over a couple bins at most, but in
    #     # general I think the structure functions must be done in time
    #     # (just as in advs), rather than depth.

    #     self.epsilon_sfz = np.empty(self.shape, dtype='float32')
    #     D = np.empty((self.shape[0], self.shape[0]))
    #     inds = range(adpr.shape[0])
    #     for idx, (bm1,) in enumerate(adpr.iter_n(['beam1vel'],
    #                                              self.props['n_bin'])):
    #         bm1 -= self.beam1vel[:, idx][:, None]
    #         for ind in inds:
    #             D[ind, :] = np.nanmean((bm1[ind, :] - bm1) ** 2, axis=1)
    #             # r = np.abs(adpr.ranges[ind] - adpr.ranges)
    #             # pti = inds.copyind
    #             # # plb.plot(D[pti, :], r ** (2. / 3.))
    #             if ind == 10:
    #                 raise Exception('Too many loops')

    def calc_ustar_fitstress(self, dinds=slice(None), H=None):
        if H is None:
            H = self.depth_m[:][None, :]
        sgn = np.sign(self.upwp_[dinds].mean(0))
        self.ustar = (sgn * self.upwp_[dinds] / (
            1 - self.z[dinds][:, None] / H)).mean(0) ** 0.5
        # p=polyfit(self.hab[dinds],sgn*self.upwp_[dinds],1)
        # self.ustar=p[1]**(0.5)
        # self.hbl_fit=p[0]/p[1]

    def calc_stresses(self, beamvel, beamAng):
        """
        Calculate the stresses from the difference in the beam variances.

        Reference: Stacey, Monosmith and Burau; (1999) JGR [104]
        "Measurements of Reynolds stress profiles in unstratified
        tidal flow"
        """
        fac = 4 * np.sin(self.config.beam_angle * deg2rad) * \
            np.cos(self.config.beam_angle * deg2rad)
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
        stress *= rotate.inst2earth_heading(self)
        if self.props['coord_sys'] == 'principal':
            stress *= np.exp(-1j * self.props['principal_angle'])
        return stress.real, stress.imag
        # self.add_data('upwp_',stress.real,'stress')
        # self.add_data('vpwp_',stress.imag,'stress')
        # self.meta['upwp_']=db.varMeta("u'w'",{2:'m',-2:'s'})
        # self.meta['vpwp_']=db.varMeta("v'w'",{2:'m',-2:'s'})
