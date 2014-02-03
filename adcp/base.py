from ..data import base as db
from ..data import velocity as dbvel
from pylab import date2num,num2date
import numpy as np
from scipy.stats.stats import nanmean,nanstd
import pylab as plb
#from pylab import plot,show
import rotate
from scipy.signal import detrend

deg2rad=np.pi/180

def nanvar(dat,**kwargs):
    if kwargs.has_key('axis') and kwargs['axis']<0:
        kwargs['axis']=dat.ndim+kwargs['axis']
    return nanstd(dat,**kwargs)**2

# These may need to be a data_base object, and it would be good to give it a __save__ method, which can be incorporated into my data_base methods.
class adcp_header(object):
    header_id=0
    dat_offsets=0

class adcp_config(db.config):
    config_type='ADCP'
    
    def __init__(self,):
        #self._data_groups={}
        #self.setattr('_data_groups',{'main':data_base.oset([])}) # Legacy setattr
        #super(adcp_config,self).__init__() # I Don't think this is necessary.
        self.name='wh-adcp'
        self.sourceprog='instrument'
        self.prog_ver=0


def diffz_first(dat,z,axis=0):
    return np.diff(dat,axis=0)/(np.diff(z)[:,None])

## Need to add this at some point...
## Get it from my ddz.m file
#def diffz_centered(dat,z,axis=0):
#    return np.diff(dat,axis=0)/(np.diff(z)[:,None])

## class adcp_raw_meta(db.velocity_meta):
##     def __init__(self,*args,**kwargs):
##         #self.update()
##         super(adcp_raw_meta,self).__init__(*args,**kwargs)


class adcp_raw(dbvel.velocity):
    #meta=adcp_raw_meta()
    inds=slice(1000)
    diff_style='first'
    
    def iter_n(self,names,nbin):
        """
        Iterate over the list of variables *names*, yielding chunks of *nbin* profiles.
        """
        i=0
        if names.__class__ is not list:
            names=[names]
        outs=[]
        while i+nbin<self.shape[1]:
            for nm in names:
                outs.append(getattr(self,nm)[:,i:(i+nbin)])
            yield tuple(outs)
            i+=nbin
    
    def _diff_func(self,nm):
        if self.diff_style=='first':
            return diffz_first(getattr(self,nm),self.z)
        else:
            return diffz_centered(getattr(self,nm),self.z)

    @property
    def zd(self,):
        if self.diff_style=='first':
            return self.z[0:-1]+np.diff(self.z)/2
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
        return self.dudz**2+self.dvdz**2

    @property
    def time(self,):
        return self.mpltime[:]-self.toff
    @time.setter
    def time(self,val):
        self.add_data('mpltime',val)
    def __getitem__(self,indx):
        dat=getattr(self,indx)
        if hasattr(self,'mask'):
            return np.ma.masked_array(dat,mask=self.mask)
        else:
            return np.ma.masked_array(dat,mask=np.isnan(dat))
    
    def __repr__(self,):
        mmstr=''
        if self.mpltime.__class__ is db.h5._hl.dataset.Dataset:
            mmstr='mm'
        if (not hasattr(self,'mpltime')) or self.mpltime[0]<1:
            print 'Warning: no time information!'
            dt=num2date(693596)
            tm=np.array([0,0])
        else:
            tm=[self.mpltime[0],self.mpltime[-1]]
            dt=num2date(tm[0])
        return "%0.2f hour %sADCP record (%s bins, %s pings), started: %s" % ((tm[-1]-tm[0])*24,mmstr,self.shape[0],self.shape[1],dt.strftime('%b %d, %Y %H:%M'))


## class adcp_binned_meta(db.velocity_meta):
##    def __init__(self,*args,**kwargs):
##        self.update({'Etke':db.varMeta('Etke',{2:'m',-2:'s'}),
##            })
##        super(adcp_binned_meta,self).__init__(*args,**kwargs)

class adcp_binned(dbvel.vel_bindat_tke,adcp_raw):
    #meta=adcp_binned_meta()
    inds=slice(None)

    @property
    def Etke(self,):
        return self.upup_[:]+self.vpvp_[:]+self.wpwp_[:]
    
    def calc_avar(self,advr):
        """
        Calculate the variance of 'u','v' and 'w'.
        """
        flds=['u','v','w']
        for fld in flds:
            self.add_data(fld+'p'+fld+'p_',nanmean(self.demean(advr,fld)**2,axis=-1))
        # These are the beam rotation constants, multiplied by sqrt(num_beams_in_component),
        # to give the error (we are adding/subtracting 2,2 and 4 beams in u,v, and w.
        if self.props.has_key('doppler_noise'):
            if dict not in self.props['doppler_noise'].__class__.__mro__:
                erruv=self.props['doppler_noise']/2/np.sin(self.config.beam_angle*np.pi/180)*2**0.5
                errw=self.props['doppler_noise']/4/np.cos(self.config.beam_angle*np.pi/180)*2
                self.upup_-=erruv**2
                self.vpvp_-=erruv**2
                self.wpwp_-=errw**2
            else:
                self.upup_-=self.props['doppler_noise']['u']**2
                self.vpvp_-=self.props['doppler_noise']['v']**2
                self.wpwp_-=self.props['doppler_noise']['w']**2
        #self.meta['upup_']=db.varMeta("u'u'",{2:'m',-2:'s'})
        #self.meta['vpvp_']=db.varMeta("v'v'",{2:'m',-2:'s'})
        #self.meta['wpwp_']=db.varMeta("w'w'",{2:'m',-2:'s'})
        
    def calc_eps_sfz(self,adpr):
        """
        I'm not really sure this works.
        It seems that it might work over a couple bins at most, but in general I think the structure functions
        must be done in time (just as in advs), rather than depth.

        *** Currently, this function is in a debugging state, and is non-functional. ***
        """
        self.epsilon_sfz=np.empty(self.shape,dtype='float32')
        D=np.empty((self.shape[0],self.shape[0]))
        inds=range(adpr.shape[0])
        for idx,(bm1,) in enumerate(adpr.iter_n(['beam1vel'],self.props['n_bin'])):
            bm1-=self.beam1vel[:,idx][:,None]
            for ind in inds:
                D[ind,:]=nanmean((bm1[ind,:]-bm1)**2,axis=1)
                r=np.abs(adpr.ranges[ind]-adpr.ranges)
                pti=inds.copyind
                plb.plot(D[pti,:],r**(2./3.))
                if ind==10:
                    error

    def calc_ustar_fitstress(self,dinds=slice(None),H=None):
        if H is None:
            H=self.depth_m[:][None,:]
        sgn=np.sign(self.upwp_[dinds].mean(0))
        self.ustar=(sgn*self.upwp_[dinds]/(1-self.z[dinds][:,None]/H)).mean(0)**0.5
        #p=polyfit(self.hab[dinds],sgn*self.upwp_[dinds],1)
        #self.ustar=p[1]**(0.5)
        #self.hbl_fit=p[0]/p[1]

    def calc_tke(self,apdr,aniso_ratios=[.5,.3],dnoise=None):
        """
        Compute the tke.  An assumption about the fraction of energy in the <w'w'> component must be made.

        aniso_ratios specifies the anisotropy ratios, v'v'/u'u' and w'w'/u'u', to use, respectively.
        """
        #*wpwp_frac* specifies the fraction of tke assumed to be in the <w'w'> component.
        #*wpwp_frac* was defaulted to 0.12 when implemented.
        # Because of the need to make an assumption, I wonder if this is not a
        # better way to estimate tke than simply from transformed velocities?
        bmang=apdr.config.beam_angle*deg2rad
        fac=(1+np.sum(aniso_ratios))
        if dnoise is None:
            if not apdr.props.has_key('doppler_noise'):
                raise db.DataError('An estimate of doppler noise is required to estimate TKE.')
            dnoise=apdr.props['doppler_noise']
        # This involves some funny ellipse trig...
        # define the "unit" ellipse as having a
        theta=self.props['principal_angle']+self.heading_deg[:]*deg2rad
        rx=aniso_ratios[0]/np.sqrt(aniso_ratios[0]*np.cos(theta)**2+np.sin(theta)**2)
        ry=aniso_ratios[0]/np.sqrt(aniso_ratios[0]*np.cos(theta+np.pi/2)**2+np.sin(theta+np.pi/2)**2)
        dx2=(nanvar(self.reshape(apdr.beam1vel),axis=-1)+nanvar(self.reshape(apdr.beam2vel),axis=-1))/2-dnoise**2
        dy2=(nanvar(self.reshape(apdr.beam3vel),axis=-1)+nanvar(self.reshape(apdr.beam4vel),axis=-1))/2-dnoise**2
        dx2*=1./rx # Scale by the 'unit' ellipse radius that the instrument was at, to get the magnitude of the x-direction u'u'.
        dy2*=1./ry # Do the same for the direction the instruments y-axis was at.
        dx2*=1/(np.sin(bmang)**2+aniso_ratios[1]*np.cos(bmang)**2)*fac
        dy2*=1/(np.sin(bmang)**2+aniso_ratios[1]*np.cos(bmang)**2)*fac
        dx2[dx2<0]=0
        dy2[dy2<0]=0
        self.add_data('q2u',dx2,'stress')
        self.add_data('q2v',dy2,'stress')
        return self.Etke_indir
        
    @property
    def Etke_indir(self,):
        return (self.q2u[:]+self.q2v[:])/2.

    def calc_stresses(self,apdr):
        """
        Calculate the stresses from, the difference in the beam variances.
        Reference: Stacey, Monosmith and Burau; (1999) JGR [104] "Measurements of Reynolds stress profiles in unstratified tidal flow"
        """
        fac=4*np.sin(self.config.beam_angle*deg2rad)*np.cos(self.config.beam_angle*deg2rad)
        # Note: Stacey defines the beams incorrectly for Workhorse ADCPs.
        #       According to the workhorse coordinate transformation documentation, the instrument's:
        #                        x-axis points from beam 1 to 2, and
        #                        y-axis points from beam 4 to 3.
        #       Therefore:
        stress=((nanvar(self.reshape(apdr.beam1vel),axis=-1)-nanvar(self.reshape(apdr.beam2vel),axis=-1))+1j*(nanvar(self.reshape(apdr.beam4vel),axis=-1)-nanvar(self.reshape(apdr.beam3vel),axis=-1)))/fac
        if self.config.orientation=='up':
            # This comes about because, when the ADCP is 'up', the u and w velocities need to be multiplied by -1
            # (equivalent to adding pi to the roll).  See the coordinate transformation documentation for more info.
            # The uw (real) component has two minus signs, but the vw (imag) component only has one, therefore:
            stress.imag*=-1
        stress*=rotate.inst2earth_heading(self)
        if self.props['coord_sys']=='principal':
            stress*=np.exp(-1j*self.props['principal_angle'])
        self.add_data('upwp_',stress.real,'stress')
        self.add_data('vpwp_',stress.imag,'stress')
        #self.meta['upwp_']=db.varMeta("u'w'",{2:'m',-2:'s'})
        #self.meta['vpwp_']=db.varMeta("v'w'",{2:'m',-2:'s'})



def bin_adcp(apdo,n_bin):
    out=adcp_binned()
    apdo._copy_props(out)
    out.props['n_bin']=n_bin
    l=len(apdo.time)
    out.props['n']=np.floor(l/n_bin)
    
    for nm,dat,grpnm in apdo.iter_wg():
        print nm
        if hasattr(dat,'shape') and dat.shape[-1]==l:
            out.add_data(nm,
                         nanmean(out.reshape(apdo.get_data(nm)),axis=-1).astype(dat.dtype),
                         group=grpnm)
        else:
            out.add_data(nm,apdo.get_data(nm),group=grpnm)
    if hasattr(apdo.config,'beam_angle') and hasattr(apdo,'beam1vel'): # This means it is a workhorse, created with adcp.readbin.  Need to generalize this...
        out.calc_stresses(apdo)
        out.calc_tke(apdo)
    out.calc_avar(apdo)
    return out

type_map=db.get_typemap(__name__)
def load(fname,data_groups=None):
    with db.loader(fname,type_map) as ldr:
        return ldr.load(data_groups)

def mmload(fname,data_groups=None):
    with db.loader(fname,type_map) as ldr:
        return ldr.mmload(data_groups)

