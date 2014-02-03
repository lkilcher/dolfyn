import numpy as np
from ..data.velocity import vel_binner_spec
from .base import adv_binned
from ..tools.misc import slice1d_along_axis
kappa=0.41

class turb_binner(vel_binner_spec):

    def __call__(self,advr,omega_range_epsilon=[6.28,12.57],Itke_thresh=0):
        """
        Compute a suite of turbulence statistics for the input data advr, and
        return a 'binned' data object.

        Parameters
        ----------
        *advr*                : The raw-adv object.
        *omega_range_epsilon* : The radial frequency over which to estimate the
                                dissipation rate 'epsilon'.
        *Itke_thresh*         : The threshold for velocity magnitude for computing
                                the turbulence intensity. Values of Itke where
                                U_mag < Itke_thresh are set to NaN.  (default: 0).
        """
        out=vel_binner_spec.__call__(self,advr,adv_binned)
        out.add_data('tke',self.calc_tke(advr._u,noise=advr.noise),'main')
        out.add_data('stress',self.calc_stress(advr._u),'main')
        out.add_data('sigma_Uh',np.std(self.reshape(advr.U_mag),-1,dtype=np.float64)-(advr.noise[0]+advr.noise[1])/2,'main')
        out.props['Itke_thresh']=Itke_thresh
        out.add_data('Spec',self.calc_vel_psd(advr._u,advr.fs,noise=advr.noise),'spec')
        out.add_data('omega',self.calc_omega(advr.fs),'_essential')
        self.set_bindata(advr,out)
        
        out.add_data('epsilon',self.calc_epsilon_LT83(out.Spec,out.omega,out.U_mag,omega_range=omega_range_epsilon),'main')
        #out.add_data('Cov_u',self.calc_acov(advr._u),'corr')
        #out.add_data('Lint',self.calc_Lint(out.Cov_u,out.U_mag,out.fs),'main')
        return out
        
    def calc_epsilon_LT83(self,spec,omega,U_mag,omega_range=[6.28,12.57]):
        """
        This is the simple S(k)=alpha*\epsilon**(2/3)*k**(-5/3) model for estimating dissipation.
        
        """
        inds=(omega_range[0]<omega) & (omega<omega_range[1])
        a=0.5
        f_shp=[1]*(spec.ndim-1)+[inds.sum()]
        # !!!CHECKTHIS... should U_mag be inside the ()**5/3?
        return np.mean(spec[...,inds]*(omega[inds].reshape(f_shp))**(5./3.)/a,-1,dtype=np.float64)**(3./2.)/U_mag

    def calc_epsilon_SF(self,veldat,umag,fs,freq_rng=[.5,5.]):
        """
        Calculate epsilon using the "structure function" (SF) method.

        Parameters
        ----------
        *veldat*   : The raw velocity signal (last dimension time) upon which to
                     perform the SF technique.
        *umag*     : The bin-averaged horizontal velocity magnitude.
        *fs*       : The sample rate of *veldat* (hz).
        *freq_rng* : The frequency range over which to compute the SF (hz).
        """
        dt=self.reshape(veldat)
        out=np.empty(dt.shape[:-1],dtype=dt.dtype)
        for slc in slice1d_along_axis(dt.shape,-1):
            up=dt[slc]
            lag=umag[slc[:-1]]/fs*np.arange(up.shape[0])
            DAA=np.NaN*lag
            for L in range(int(fs/freq_rng[1]),int(fs/freq_rng[0])):
                DAA[L]=np.mean((up[L:]-up[:-L])**2.,dtype=np.float64)
            cv2=DAA/(lag**(2./3.))
            cv2m=np.median(cv2[np.logical_not(np.isnan(cv2))])
            out[slc[:-1]]=(cv2m/2.1)**(3./2.)
        return out
    
    def up_angle(self,Uh_complex):
        """
        Calculate the angle of the turbulence fluctuations.

        Parameters
        ----------
        Uh_complex  : The complex horizontal velocity (raw/non-binned).
        """
        dt=self.demean(Uh_complex)
        fx=dt.imag<=0
        dt[fx]=dt[fx]*np.exp(1j*np.pi)
        return np.angle(np.mean(dt,-1,dtype=np.complex128))

    def CALC_epsilon_TE01(self,advbin,advraw,omega_range=[6.28,12.57]):
        theta=advbin.U_angle-self.up_angle(advraw.U)
        return self.calc_epsilon_TE01(advbin.Spec,advbin.u_mag,advbin.Itke,theta,advbin.omega,omega_range)
        
        
    def calc_epsilon_TE01(self,spec,u_mag,Itke,theta,omega,omega_range=[6.28,12.57]):
        """
        Calculate epsilon according to:
        Trowbridge, J and Elgar, S, "Turbulence measurements in the Surf Zone" JPO, 2001, 31, 2403-2417.
        hereafter referred to as [TE01].
        """
        # Is the difference between this and epsLT83 due to constant factors???
        alpha=1.5
        intgrl=self._calc_epsTE01_int(Itke,theta)
        inds=(omega_range[0]<omega) & (omega<omega_range[1])
        out=(np.mean((spec[0]+spec[1])[...,inds]*(omega[inds].reshape([1]*(spec.ndim-2)+[sum(inds)]))**(5./3.),-1,dtype=np.float64)/(21./55.*alpha*intgrl))**(3./2.)/U_mag
        out+=(np.mean(velbin.Sww[...,inds]*(velbin.omega[inds].reshape([1]*(spec.ndim-2)+[sum(inds)]))**(5./3.),-1,dtype=np.float64)/(12./55.*alpha*intgrl))**(3./2.)/U_mag
        out*=0.5 # Average the two estimates.
        ## if ma:
        ##     meta=ma.varMeta(None)
        ##     if advr.u.__class__ is ma.marray and advr.u.meta._units=={'m':1,'s':-1}:
        ##         meta=ma.varMeta(r"\epsilon_{%s}",{'W':1,'kg':-1},list(advr.u.meta.dim_names))
        return out

    def _calc_epsTE01_int(self,Itke,theta):
        """
        The integral, equation A13, in [TE01].

        *Itke* (beta in TE01) is the turbulence intensity ratio:
            \sigma_u/V

        *theta* is the angle between the mean flow, and the primary
        axis of velocity fluctuations.
        """
        x=np.arange(-20,20,1e-2) # I think this is a long enough range.
        out=np.empty_like(beta.flatten())
        for i,(b,t) in enumerate(zip(beta.flatten(),theta.flatten())):
            out[i]=np.trapz(cbrt(x**2-2/b*np.cos(t)*x+b**(-2))*np.exp(-0.5*x**2),x)
        return out.reshape(beta.shape)*(2.*np.pi)**(-.5)*beta**(2./3.)

    def calc_Lint(self,corr_vel,U_mag,fs):
        """
        Calculate integral length scales.

        Parameters
        ----------
        *corr_vel*  : The auto-covariance array (i.e. computed using calc_acov).
        *U_mag*     : The velocity magnitude for this bin.
        *fs*        : The raw sample rate.


        Returns
        -------
        *Lint*      : The integral length scale (Tint*U_mag).

        The integral time scale (Tint) is the lag-time at which the auto-covariance
        falls to 1/e.
        """
        corr_vel=(corr_vel/corr_vel[...,n][...,None])<(1./np.e) # corr_vel is now logical.
        out=(corr_vel[...,:n].sum(-1)+corr_vel[...,-n:].sum(-1))/2 # Sum the number of points to get the 'lag time' (this may be slightly different than finding the last non-zero from the middle.
        out[...,0]=corr_vel[...,-n:].sum(-1) # The corr_vel of the first and last bin are contaminated by zero padding in the reshape function.
        out[...,-1]=corr_vel[...,:n].sum(-1)
        out*=U_mag/fs
        return out


    
