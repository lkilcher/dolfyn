import numpy as np
import data as db
reload(db)
import data.velocity as dbvel
import tools as tbx
reload(tbx)
from scipy.special import cbrt
import copy
from OrderedSet import OrderedSet as oset
kappa=0.41
#from tke import kappa
ma=db.ma

#f_fac=1
f_fac=ma.marray(2*np.pi,ma.varMeta('',{'s':-1,'hz':-1}))

class adv_config(db.config):
    def __init__(self,config_type='ADV'):
        self.config_type=config_type

def check_marray(obj,name,meta=None):
    if meta is not None and getattr(obj,name).__class__ is not ma.marray:
        setattr(obj,name,ma.marray(getattr(obj,name),meta))

class adv_raw(dbvel.velocity):
    props={'fs':None,
           'n_bin':2048,
           'inds':slice(4000),
           'coord_sys':'earth',
           }
    sax_params={'h':[.18,.94,.05],'v':[.14,.9,.05]}

    ## def __postload__(self,):
    ##     check_marray(self,'u',ma.varMeta('u',{'m':1,'s':-1},['time']))
    ##     check_marray(self,'v',ma.varMeta('v',{'m':1,'s':-1},['time']))
    ##     check_marray(self,'w',ma.varMeta('w',{'m':1,'s':-1},['time']))
    @property
    def len(self,):
        return self.u.shape[-1]
    
    @property
    def shape(self,):
        return self.u.shape
    @property
    def n(self,):
        return self.u.shape[-1]
        
    @property
    def rotmat_beam(self,):
        """
        Returns the beam rotation matrix.
        (Stored in the adv config.)
        """
        return self.config.transformation_matrix
        
    @property
    def inds(self,):
        return self.props['inds']
    @inds.setter
    def inds(self,val):
        self.props['inds']=val

    @property
    def n_bin(self,):
        return self.props['n_bin']
    @n_bin.setter
    def n_bin(self,val):
        self.props['n_bin']=val
    
    # _data_groups is used to place the data in "groups" in the hdf5 file,
    # as well as for specifying subsets of the data to save/load.
    _data_groups={'main':oset(['u','v','w','pressure','temp']),
                  '_essential':oset(['mpltime']),
                  'orient':oset(['heading','pitch','roll']),
                  'signal':oset(['Amp1','Amp2','Amp3','SNR1','SNR2','SNR3','corr1','corr2','corr3']),
                  'index':oset(['burst','ensemble','checksum']),# Checksum,c_sound might not fit here, but...
                  }

    def __init__(self,npoints=None,names=[],**kwargs):
        self._data_groups={}
        self._update_props()
        if npoints is not None:
            for ky in names:
                self.init_data(npoints,ky,dtype=data_defs.get(ky,np.float32))
        #super(adv_raw,self).__init__(**kwargs)
        
    def __repr__(self,):
        mmstr=''
        if self.mpltime.__class__ is db.h5._hl.dataset.Dataset:
            mmstr='mm'
        if (not hasattr(self,'mpltime')) or self.mpltime[0]<1:
            print 'Warning: no time information!'
            dt=tbx.num2date(693596)
            tm=np.array([0,0])
        else:
            tm=[self.mpltime[0],self.mpltime[-1]]
            dt=tbx.num2date(tm[0])
        return "%0.2fh %sADV record, started: %s" % ((tm[-1]-tm[0])*24,mmstr,dt.strftime('%b %d, %Y %H:%M'))

    def get_slice_time(self,trange):
        """
        Return a slice object for trange.
        """
        pass # Need to add this, but wait until I have time data.
    
    def _get_inds(self,inds=None):
        if inds is None:
            return self.inds
        elif inds=='all':
            return slice(len(self.u))
        return inds

class msadv_raw(adv_raw):
    """
    Micro-sense ADV class.
    """
    pass #For now this is a place holder.

    
    
def merge_lag(avds,lag=[0]):
    """
    Merge a set of adv objects based on a predefined lag.
    """
    out=multi_sync()
    mx=np.inf
    ndat=len(avds)
    for avd,l in zip(avds,lag):
        mx=np.min([len(avd)-l,mx])
    for nm,dat,grpnm in avd.iter_wg():
        out.init_data((ndat,mx),nm,dtype=dat.dtype,group=grpnm,meta=getattr(dat,'meta',None))
        if hasattr(dat,'meta'):
            getattr(out,nm).meta.dim_names=['inst']+dat.meta.dim_names
    for idx,(avd,l) in enumerate(zip(avds,lag)):
        for nm,dat in avd:
            getattr(out,nm)[idx,:]=dat[l:mx+l]
    avd._copy_props(out)
    avd.props['DeltaT']=np.diff(out.mpltime,axis=0).mean()
    out.mpltime=out.mpltime.mean(0)
    return out


def merge_syncd(avds,sync_on='ensemble'):
    """
    Merge a list of adv objects
    """
    out=multi_sync()
    mn=0
    mx=np.inf
    ndat=len(avds)
    if not sync_on=='straight':
        for avd in avds:
            # First find the min and max indices that are consistent across all data sets:
            mn=np.max((mn,np.min(getattr(avd,sync_on))))
            mx=np.min((mx,np.max(getattr(avd,sync_on))))
    else:
        for avd in avds:
            mx=np.min((mx,len(avd.mpltime)))
    
    # Now initialize the data object.
    for nm,dat,grpnm in avd.iter_wg():
        out.init_data((ndat,mx-mn),nm,dtype=dat.dtype,group=grpnm)
    for idx,avd in enumerate(avds):
        if not sync_on=='straight':
            inds=getattr(avd,sync_on)
            i0=np.nonzero(mn==inds)[0]
            ie=np.nonzero(mx==inds)[-1]
        else:
            i0=mn
            ie=mx
        # Now join the data sets:
        for nm,dat in avd:
            getattr(out,nm)[idx,:]=dat[i0:ie]
    if not sync_on=='straight':
        setattr(out,sync_on,getattr(out,sync_on)[0])
    avd._copy_props(out)
    return out
            
            

class multi_sync(adv_raw):
    """
    A base class for multiple, sync'd advs.
    """
    @property
    def n_inst(self,):
        return self.u.shape[0]
        
    def __repr__(self,):
        if (not hasattr(self,'time')) or self.time[0]<1:
            print 'Warning: no time information!'
            dt=tbx.num2date(693596)
            tm=np.array([0,0])
        else:
            dt=tbx.num2date(self.mpltime[0])
            tm=[self.mpltime[0],self.mpltime[-1]]
        return "%0.2fh sync'd %d-ADV record, started: %s" % ((tm[-1]-tm[0])*24,self.n_inst,dt.strftime('%b %d, %Y %H:%M'))


class adv_binned(dbvel.binned_velocity,adv_raw):
    @property
    def n(self,):
        return self.props['n']
    @n.setter
    def n(self,val):
        self.props['n']=val

    fig={}
    figsize=(8,5)
    props={'inds':slice(None),
           'n_fft':None,
           }

    @property
    def Ecoh(self,):
        """
        Niel Kelley's "coherent energy", i.e. the rms of the stresses.
        Why did he do it this way, instead of the sum of the magnitude of the stresses?
        """
        return (self.upwp_**2+self.upvp_**2+self.vpwp_**2)**(0.5)

    @property
    def Etke(self,):
        """
        Turbulent kinetic energy.
        """
        return self.upup_+self.vpvp_+self.wpwp_

    @property
    def k(self,):
        """
        Wavenumber.
        """
        return self.omega[:,None]/self.U_mag

    @property
    def Itke(self,):
        """
        Turbulence intensity.
        Ratio of standard deviation of velocity magnitude to velocity magnitude.
        """
        return np.ma.masked_where(self.U_mag<0.3,self.sigma_Uh/self.U_mag)

    @property
    def ustar_eps(self,):
        return (self.epsilon/kappa/self.props['hab'])**(1./3.)
    

    @property
    def phi_epsilon(self,):
        return kappa*self.epsilon*10./(self.ustar**3.)

    @property
    def epsilon(self,):
        return self.eps_LT83

    @property
    def Suu_f(self,):
        return self.Suu*f_fac
    @property
    def Svv_f(self,):
        return self.Svv*f_fac
    @property
    def Sww_f(self,):
        return self.Sww*f_fac

    def calc_prod(self,dudz=None,dvdz=None):
        if dudz is None:
            dudz=self.dudz
        if dvdz is None:
            dvdz=self.dvdz
        self.add_data('prod',-self.upwp_*dudz-self.vpwp_*dvdz,'epsilon')
        return self.prod
        
    def calc_xcov(self,indt1,indt2):
        shp=list(self.shape[:-1])
        shp.extend([self.n,self.n_bin])
        out=np.empty(shp)
        dt1=self.reshape(indt1,n_pad=self.n_bin-1)
        dt1=dt1-dt1[...,:,self.n_bin/2:-self.n_bin/2].mean(-1)[...,None] # Note here I am demeaning only on the 'valid' range.
        dt2=self.reshape(indt2) # Don't need to pad the second variable this variable.
        dt2=dt2-dt2.mean(-1)[...,None]
        for slc in tbx.slice1d_along_axis(dt1.shape,-1):
            out[slc]=np.correlate(dt1[slc],dt2[slc],'valid')
        return out

    def do_acov(self,advd):
        self.add_data('Cuu',self.calc_xcov(advd.u,advd.u),'corr')
        self.add_data('Cvv',self.calc_xcov(advd.v,advd.v),'corr')
        self.add_data('Cww',self.calc_xcov(advd.w,advd.w),'corr')

    def do_Lint(self,advd=None):
        """
        Calculate integral length scales.
        """
        self.add_data('Lint_uvw',np.ma.empty((3,self.n)),'main')
        if not hasattr(self,'Cuu'):
            if advd is None:
                raise db.DataError(r'This instance does not contain the correlation data necessary to calculate Lint.\n   Try calling the function with the raw data.')
            self.do_acov(advd)
        self.Lint_uvw[0,:]=self.calc_Lint('u')
        self.Lint_uvw[1,:]=self.calc_Lint('v')
        self.Lint_uvw[2,:]=self.calc_Lint('w')

    @property
    def Lint(self,):
        return np.median(self.Lint_uvw,axis=1)

    def calc_Lint(self,advd,var='u'):
        """
        The integral time scale is the lag-time at which the lagged auto-covariance falls to 1/e.
        The integral length scale is the time scale times the mean velocity.
        """
        dat=self.get_data('C'+var+var)
        n=self.n_bin/2
        dat=dat/dat[n,:]<1./np.e
        Lint=np.empty((self.n,2))*np.NaN
        for idx in range(self.n):
            inds=np.nonzero(dat[:n,idx])[0]
            if len(inds):
                Lint[idx,0]=n-inds[-1]
            inds=np.nonzero(dat[n:,idx])[0]
            if len(inds):
                Lint[idx,1]=inds[0]
        Lint[0,0]=np.NaN # Throw these values away b/c they are contaminate by zero padding in the reshape function.
        Lint[-1,-1]=np.NaN
        Lint=np.ma.masked_where(np.isnan(Lint),Lint)
        Lint=Lint.mean(1)/self.fs*self.U_mag
        return Lint

    def calc_epsLT83(self,f_range=[1.,2.]):
        """
        This is the simple S(k)=alpha*\epsilon*k**(-5/3) model of estimating dissipation.
        """
        meta=ma.varMeta(None)
        if self.u.__class__ is ma.marray and self.u.meta._units=={'m':1,'s':-1}:
            meta=ma.varMeta(r"\epsilon_{LT83%s}",{'W':1,'kg':-1},list(self.u.meta.dim_names))
        inds=tbx.within(self.freq,f_range)
        a=0.5
        shp=[1]*self.Suu.ndim
        shp[-1]=inds.sum()
        self.add_data('eps_LT83u',np.mean(self.Suu[...,inds]*(self.omega[inds].reshape(shp))**(5./3.)/a,-1,dtype=np.float64)**(3./2.)/self.U_mag,'epsilon',meta._copy_rep(('u',)))
        self.add_data('eps_LT83v',np.mean(self.Svv[...,inds]*(self.omega[inds].reshape(shp))**(5./3.)/a,-1,dtype=np.float64)**(3./2.)/self.U_mag,'epsilon',meta._copy_rep(('v',)))
        self.add_data('eps_LT83w',np.mean(self.Sww[...,inds]*(self.omega[inds].reshape(shp))**(5./3.)/a,-1,dtype=np.float64)**(3./2.)/self.U_mag,'epsilon',meta._copy_rep(('w',)))
        self.add_data('eps_LT83',(self.eps_LT83u+self.eps_LT83v+self.eps_LT83w)/3.,'epsilon',meta._copy_rep(('',)))

    def calc_epsSF(self,advr,freq_rng=[1.,2.]):
        meta=ma.varMeta(None)
        if advr.u.__class__ is ma.marray and advr.u.meta._units=={'m':1,'s':-1}:
            meta=ma.varMeta(r"\epsilon_{SF%s}",{'W':1,'kg':-1},list(self.u.meta.dim_names))
        for nm in ['u','v','w']:
            self.add_data('eps_SF'+nm,self.comp_struct_func(advr,nm,freq_rng=freq_rng),'epsilon',meta._copy_rep((nm,)))
        self.add_data('eps_SF',(self.eps_SFu+self.eps_SFv+self.eps_SFw)/3.,'epsilon',meta._copy_rep(('',)))

    def comp_struct_func(self,advr,nm,freq_rng=[.5,5.]):
        """
        Calculate epsilon using the "structure function" method.
        """
        dt=self.reshape(advr.get_data(nm))
        out=np.empty_like(self.u)
        for slc in tbx.slice1d_along_axis(dt.shape,-1):
            up=dt[slc]
            lag=self.U_mag[slc[:-1]]/self.fs*np.arange(up.shape[0])
            DAA=np.NaN*lag
            for L in range(int(self.fs/freq_rng[1]),int(self.fs/freq_rng[0])):
                DAA[L]=np.mean((up[L:]-up[:-L])**2.,dtype=np.float64)
            cv2=DAA/(lag**(2./3.))
            cv2m=np.median(cv2[np.logical_not(np.isnan(cv2))])
            out[slc[:-1]]=(cv2m/2.1)**(3./2.)
        return out
        

    def calc_epsTE01(self,advr,f_range=[1,2],f_noise=3):
        """
        Calculate epsilon according to:
        Trowbridge, J and Elgar, S, "Turbulence measurements in the Surf Zone" JPO, 2001, 31, 2403-2417.
        hereafter referred to as [TE01].
        """
        alpha=1.5
        beta=np.sqrt(self.upup_+self.vpvp_)/self.U_mag
        theta=self.U_angle-self.up_angle(advr)
        intgrl=self._calc_epsTE01_int(beta,theta)
        meta=ma.varMeta(None)
        if advr.u.__class__ is ma.marray and advr.u.meta._units=={'m':1,'s':-1}:
            meta=ma.varMeta(r"\epsilon_{%s}",{'W':1,'kg':-1},list(advr.u.meta.dim_names))
        self.add_data('eps_TE01uv',(self._calc_epsTE01_uv(f_range=f_range,f_noise=f_noise)/(21./55.*alpha*intgrl))**(3./2.)/self.U_mag,'epsilon',meta._copy_rep(('TE01uv',)))
        self.add_data('eps_TE01w',(self._calc_epsTE01_w(f_range=f_range)/(12./55.*alpha*intgrl))**(3./2.)/self.U_mag,'epsilon',meta._copy_rep(('TE01w',)))
        self.add_data('eps_TE01',(self.eps_TE01uv+self.eps_TE01w)/2.,'epsilon',meta._copy_rep(('TE01',))) # Difference between this and epsLT83 is due to constant factors... ???
        
    def _calc_epsTE01_uv(self,f_range=[1.,2.],f_noise=3.):
        """
        See calc_epsTE01.  This implements the uv estimate of PSD amplitude.

        *f_range* is the frequency range over which to estimate the
        amplitude of the PSD.

        The noise level is estimated from frequencies greater than *f_noise*. 

        TE01 uses *f_range*=[1,2](hz), and *f_noise*=3(hz).  These are the
        defaults.
        """
        inds=self.freq>f_noise # in hz.
        Stot=self.Suu+self.Svv
        #noise=np.mean(Stot[inds,:],0) # Here I estimate the noise level for each bin.  Should this be estimated in total?
        if Stot.ndim>2:
            shp=[1]*Stot.ndim
            shp[0]=Stot.shape[0]
            noise=np.empty(shp)
            for iin in range(shp[0]):
                noise[iin]=np.mean(Stot[iin,...,inds],dtype=np.float64)
        else:
            noise=np.mean(Stot[...,inds],dtype=np.float64) # Estimate a single noise level.
        inds=tbx.within(self.freq,f_range) # in hz.
        shp=[1]*Stot.ndim
        shp[-1]=sum(inds)
        return np.mean((Stot[...,inds]-noise)*(self.omega[inds].reshape(shp))**(5./3.),-1,dtype=np.float64)

    def _calc_epsTE01_w(self,f_range=[1,2]):
        """
        See calc_epsTE01.  This implements the w estimate of PSD amplitude.

        *f_range* is the frequency range over which to estimate the
        amplitude of the PSD.

        TE01 uses *f_range*=[1,2](hz).  This is the default.
        """
        inds=tbx.within(self.freq,f_range) # in hz.
        shp=[1]*self.Sww.ndim
        shp[-1]=sum(inds)
        return np.mean(self.Sww[...,inds]*(self.omega[inds].reshape(shp))**(5./3.),-1,dtype=np.float64)
    
    def _calc_epsTE01_int(self,beta,theta):
        """
        The integral, equation A13, in [TE01].
        
        *beta* is the turbulence ratio:
           \sigma_u/V
        The magnitude of the velocity standard deviation over the
        velocity magnitude.

        *theta* is the angle between the mean flow, and the primary
        axis of velocity fluctuations.
        """
        x=np.arange(-20,20,1e-2) # I think this is a long enough range.
        out=np.empty_like(beta.flatten())
        for i,(b,t) in enumerate(zip(beta.flatten(),theta.flatten())):
            out[i]=np.trapz(cbrt(x**2-2/b*np.cos(t)*x+b**(-2))*np.exp(-0.5*x**2),x)
        return out.reshape(beta.shape)*(2.*np.pi)**(-.5)*beta**(2./3.)

    def up_angle(self,advr):
        dt=self.reshape(advr.u+1j*advr.v)
        ang=np.angle(dt)
        fx=ang<=0
        dt[fx]=dt[fx]*np.exp(1j*np.pi)
        return np.angle(np.mean(dt,-1,dtype=np.complex128))
    
    def __init__(self,advr=None,n_bin=None,n_fft=512,denoise=False,**kwargs):
        """
        n_bin and n_fft can not change, a new adv_binned object must be created to use a different n_bin or n_fft.
        """
        self._update_props(advr)
        #if advr is not None:
        #    self._units.update(advr._units)
        self.props['inds']=slice(None)
        if n_bin is not None:
            self.n_bin=n_bin
        self.n_fft=n_fft
        super(adv_binned,self).__init__(**kwargs)
        if advr is not None:
            self._data_groups.update(**copy.deepcopy(advr._data_groups))
            self.add_data('freq',tbx.psd_freq(self.n_fft,self.fs),'_essential')
            self.n=n=int(advr.time.size/self.n_bin)
            flds=['mpltime','u','v','w','pressure','temp','heading','pitch','roll']
            for fld in flds:
                if hasattr(advr,fld):
                    dtmp=self.reshape(advr.get_data(fld))
                    self.add_data(fld,np.mean(dtmp,-1,dtype=np.float64).astype(dtmp.dtype))
            self.calc_avar(advr,denoise=denoise)
            self.calc_xvar(advr,denoise=denoise)
            self.calc_psd(advr,denoise=denoise)
            self.add_data('sigma_Uh',np.std(self.reshape(advr.U_mag),-1,dtype=np.float64),meta=(getattr(self.u,'meta',None) and self.u.meta.copy(r'\sigma_{Uh}')))
            if hasattr(advr,'config'):
                self.add_data('config',advr.config,'_essential')
            self.calc_epsTE01(advr)
            self.calc_epsLT83()
            self.calc_epsSF(advr)


type_map=db.get_typemap(__name__) # Get the data classes in the current namespace.

def load(fname,data_groups=None):
    """
    A function for loading ADV objects.

    'data_groups' specifies which groups to load.  It can be:
        None  - Load default groups (those not starting with a '#')
        [...] - A list of groups to load (plus 'essential' groups, ie those starting with '_')
        'ALL' - Load all groups.
    """
    with db.loader(fname,type_map) as ldr:
        return ldr.load(data_groups)

def mmload(fname,data_groups=None):
    with db.loader(fname,type_map) as ldr:
        return ldr.mmload(data_groups)

def load_old(fname,data_groups=None):
    with db.loader_old(fname,type_map) as ldr:
        return ldr.load(data_groups)

def load_old2(fname,data_groups=None):
    """
    Load ADV data from an hdf5 file.
    """
    if data_groups.__class__ is str:
        data_groups=[data_groups]
    out=adv_raw()
    with tbl.openFile(fname,mode='r') as h5f:
        for prop in out._save_props:
            try:
                out.add_prop(prop,h5f.getNodeAttr('/',prop)) # Need to check this.
            except:
                pass
        for grp_nm in data_groups or out._data_groups:
            dt_nms=out._data_groups[grp_nm]
            for dt_nm in dt_nms:
                out.add_data(dt_nm,h5f.getNode('/'+grp_nm,dt_nm).read())
    return out


data_defs = {'burst':np.uint16,
             'ensemble':np.uint32,
             'u':np.float32,
             'v':np.float32,
             'w':np.float32,
             'Amp1':np.uint8,
             'Amp2':np.uint8,
             'Amp3':np.uint8,
             'SNR1':np.float32,
             'SNR2':np.float32,
             'SNR3':np.float32,
             'corr1':np.uint8,
             'corr2':np.uint8,
             'corr3':np.uint8,
             'pressure':np.float32,
             'mpltime':np.float64,
             'c_sound':np.float32,
             'heading':np.float32,
             'pitch':np.float32,
             'roll':np.float32,
             'temp':np.float32,
             'checksum':np.bool,
             }
