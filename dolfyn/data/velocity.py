from base import np,Dprops,time_based,ma
from ..io.main import saveable
import h5py as h5
from binned import time_bindat,time_binner,rad_hz
from base import DataError
from matplotlib.dates import date2num,num2date

class velocity(time_based,saveable):

    def __repr__(self,):
        mmstr=''
        if self.mpltime.__class__ is h5._hl.dataset.Dataset:
            mmstr=' - (!memory mapped!)'
        if (not hasattr(self,'mpltime')) or self.mpltime[0]<1:
            print 'Warning: no time information!'
            dt=num2date(693596)
            tm=np.array([0,0])
        else:
            tm=[self.mpltime[0],self.mpltime[-1]]
            dt=num2date(tm[0])
        return "%0.2fh %s %s (%s) record, started: %s%s" % ((tm[-1]-tm[0])*24,self.props.get('inst_make','*unknown*'),self.props.get('inst_model','*unknown*'),self.props.get('inst_type','*unknown*'),dt.strftime('%b %d, %Y %H:%M'),mmstr,)

    def _pre_mat_save(self,outdict):
        outdict['u']=self._u
        outdict.pop('_u')
        if not outdict.has_key('datenum') and outdict.has_key('mpltime'):
            outdict['datenum']=self.mpltime.reshape((1,-1))+366
            outdict.pop('mpltime')
        if hasattr(self,'ranges'):
            outdict['ranges']=self.ranges.reshape([-1,1])

    @property
    def shape(self,):
        return self.u.shape

    @property
    def noise(self,):
        return self.props.get('doppler_noise',[0.,0.,0.])

    @property
    def U_mag(self,):
        """
        Velocity magnitude
        """
        return np.abs(self.U)

    @property
    def U_angle(self,):
        """
        Angle of velocity vector.
        """
        return np.angle(self.U)

    def calc_principal_angle(self,bin=None):
        """
        Compute the principal angle of the horizontal velocity.
        """
        if not self.props['coord_sys'] in ['earth','inst']:
            raise DataError("The principal angle should only be estimated if the coordinate system is either 'earth' or 'inst'.")
        self.props['coord_sys_principal_ref']=self.props['coord_sys']
        dt=self.U
        if bin is None:
            if dt.ndim>1:
                dt=dt.mean(0)
        else:
            dt=dt[bin]
        dt[dt.imag<=0]*=np.exp(1j*np.pi)
        # Now double the angle, so that angles near pi and 0 get averaged together correctly:
        dt*=np.exp(1j*np.angle(dt))
        dt=np.ma.masked_invalid(dt)
        # Divide the angle by 2 to remove the doubling done on the previous line.
        self.props['principal_angle']=np.angle(np.mean(dt,0,dtype=np.complex128))/2
        # Angle returns values between -pi and pi.  I want the principal angle always to be between 0 and pi.
        #  Therefore, add pi to the negative ones.
        if self.props['principal_angle']<0:
            self.props['principal_angle']+=np.pi

    def earth2principal(self,var='_u'):
        """
        Rotate the data into its principal axes.
        """
        dat=getattr(self,var)
        if ma.valid and dat.__class__ is ma.marray:
            if hasattr(dat.meta,'coordsys') and dat.meta.coordsys=='principal':
                return # Do nothing.
            else:
                dat.meta.coordsys='principal' # Set the coordsys.
        sang=np.sin(-self.principal_angle)
        cang=np.cos(-self.principal_angle)
        dat[:2]=np.tensordot(np.array([[cang,-sang],[sang,cang]],dtype='float32'),np.array(dat[:2]),([1],[0])) # Rotate the data using a rotation matrix.
        self.props['coord_sys']='principal'

    def _init(self,nm,shape,dtype='float32',meta=None,clear_fromGrp=None,group='main'):
        """
        This is a backwards-compatability hack to make it possible to load older-version data files.
        """
        if not hasattr(self,nm):
            self.add_data(nm,np.empty(shape,dtype=dtype),group,meta=meta)
        if clear_fromGrp:
            self.groups.remove(clear_fromGrp)

    @property
    def u(self,):
        return self._u[0]
    @u.setter
    def u(self,val):
        self._init('_u',[3]+list(val.shape),val.dtype,clear_fromGrp='u')
        self._u[0]=val
    @property
    def v(self,):
        return self._u[1]
    @v.setter
    def v(self,val):
        self._init('_u',[3]+list(val.shape),val.dtype,clear_fromGrp='v')
        self._u[1]=val
    @property
    def w(self,):
        return self._u[2]
    @w.setter
    def w(self,val):
        self._init('_u',[3]+list(val.shape),val.dtype,clear_fromGrp='w')
        self._u[2]=val

    @property
    def principal_angle(self,):
        """
        Return the principal angle of the data.
        """
        if not self.props.has_key('principal_angle'):
            self.calc_principal_angle()
        return self.props['principal_angle']

    def U_rot(self,angle):
        return self.U*np.exp(1j*angle)

    def rotate_var(self,angle,vrs=('u','v')):
        return (getattr(self,vrs[0])+1j*getattr(self,vrs[1]))*np.exp(1j*angle)
    
    @property
    def U_earth(self,):
        if self.props['coord_sys']=='earth':
            return self.U
        return self.U_rot(self.principal_angle)

    @property
    def u_earth(self,):
        return self.U_earth.real

    @property
    def v_earth(self,):
        return self.U_earth.imag

    @property
    def U_pax(self,):
        """
        The complex velocity in principal axes.
        """
        if self.props['coord_sys']=='principal':
            return self.U
        return self.U_rot(-self.principal_angle)

    @property
    def u_pax(self,):
        """
        The main component of the principal axes velocity.
        """
        return self.U_pax.real

    @property
    def v_pax(self,):
        """
        The off-axis component of the prinicipal axes velocity.
        """
        return self.U_pax.imag

    @property
    def U(self,):
        return self.u[:]+self.v[:]*1j
    
class vel_bindat_tke(velocity,time_bindat):

    @property
    def Ecoh(self,):
        """
        Niel Kelley's "coherent energy", i.e. the rms of the stresses.
        Why did he do it this way, instead of the sum of the magnitude of the stresses?
        """
        return (self.upwp_**2+self.upvp_**2+self.vpwp_**2)**(0.5)

    def Itke(self,):
        """
        Turbulence intensity.
        Ratio of standard deviation of velocity magnitude to velocity magnitude.
        """
        return np.ma.masked_where(self.U_mag<self.props['Itke_thresh'],self.sigma_Uh/self.U_mag)

    @property
    def Etke(self,):
        return self.tke.sum(0)

    @property
    def upvp_(self,):
        return self.stress[0]
    @upvp_.setter
    def upvp_(self,val):
        self._init('stress',[3]+list(val.shape),val.dtype,clear_fromGrp='upvp_')
        self.stress[0]=val
    @property
    def upwp_(self,):
        return self.stress[1]
    @upwp_.setter
    def upwp_(self,val):
        self._init('stress',[3]+list(val.shape),val.dtype,clear_fromGrp='upwp_')
        self.stress[1]=val
    @property
    def vpwp_(self,):
        return self.stress[2]
    @vpwp_.setter
    def vpwp_(self,val):
        self._init('stress',[3]+list(val.shape),val.dtype,clear_fromGrp='vpwp_')
        self.stress[2]=val

    @property
    def upup_(self,):
        return self.tke[0]
    @property
    def vpvp_(self,):
        return self.tke[1]
    @property
    def wpwp_(self,):
        return self.tke[2]

    @upup_.setter
    def upup_(self,val):
        self._init('tke',[3]+list(val.shape),val.dtype,clear_fromGrp='upup_')
        self.tke[0]=val
    @vpvp_.setter
    def vpvp_(self,val):
        self._init('tke',[3]+list(val.shape),val.dtype,clear_fromGrp='vpvp_')
        self.tke[1]=val
    @wpwp_.setter
    def wpwp_(self,val):
        self._init('tke',[3]+list(val.shape),val.dtype,clear_fromGrp='wpwp_')
        self.tke[2]=val

class vel_binner_tke(time_binner):
    def calc_tke(self,veldat,noise=[0,0,0]):
        """
        Calculate the tke (variances of u,v,w) for the data object
        *veldat* and place them in *outdat.
        """
        out=np.mean(self.detrend(veldat)**2,-1,dtype=np.float64).astype('float32')
        out[0]-=noise[0]**2
        out[1]-=noise[1]**2
        out[2]-=noise[2]**2
        return out
        
    
    def calc_stress(self,veldat):
        """
        Calculate the stresses (cross-covariances of u,v,w) for the data object
        *veldat* and place them in *outdat.
        """
        out=np.empty(self._outshape(veldat.shape)[:-1],dtype=np.float32)
        out[0]=np.mean(self.detrend(veldat[0])*self.detrend(veldat[1]),-1,dtype=np.float64).astype(np.float32)
        out[1]=np.mean(self.detrend(veldat[0])*self.detrend(veldat[2]),-1,dtype=np.float64).astype(np.float32)
        out[2]=np.mean(self.detrend(veldat[1])*self.detrend(veldat[2]),-1,dtype=np.float64).astype(np.float32)
        return out

class vel_bindat_spec(vel_bindat_tke):

    @property
    def k(self,):
        """
        Wavenumber.
        """
        return self.omega[:,None]/self.U_mag

    @property
    def Suu(self,):
        return self.Spec[0]
    @Suu.setter
    def Suu(self,val):
        self._init('Spec',[3]+list(val.shape),val.dtype,clear_fromGrp='Suu')
        self.Spec[0]=val
    @property
    def Svv(self,):
        return self.Spec[1]
    @Svv.setter
    def Svv(self,val):
        self._init('Spec',[3]+list(val.shape),val.dtype,clear_fromGrp='Svv')
        self.Spec[1]=val
    @property
    def Sww(self,):
        return self.Spec[2]
    @Sww.setter
    def Sww(self,val):
        self._init('Spec',[3]+list(val.shape),val.dtype,clear_fromGrp='Sww')
        self.Spec[2]=val

    @property
    def Suu_hz(self,):
        return self.Spec[0]*rad_hz
    @property
    def Svv_hz(self,):
        return self.Spec[1]*rad_hz
    @property
    def Sww_hz(self,):
        return self.Spec[2]*rad_hz
    
class vel_binner_spec(vel_binner_tke):

    def calc_vel_psd(self,veldat,fs=None,rotate_u=False,noise=[0,0,0],n_pad=None):
        """
        Calculate the psd of *veldat*'s velocity and place it in *outdat*.

        Parameters
        ----------
        *veldat*   : The raw data object that contains velocity data.
        *outdat*   : The bin'd data object where data will be stored.
        *rotate_u* : (optional) If True, each 'bin' of horizontal velocity is
                     rotated into its principal axis prior to calculating the psd.
                     (default: False).
        *noise*    : Noise level of each component's velocity measurement (default to 0).
        """
        fs=self._parse_fs(fs)
        if rotate_u:
            tmpdat=self.reshape(veldat[0]+1j*veldat[1])
            tmpdat*=np.exp(-1j*np.angle(tmpdat.mean(-1)))
            if noise[0]!=noise[1]:
                print 'Warning: noise levels different for u,v. This means noise-correction cannot be done here when rotating velocity.'
                noise[0]=noise[1]=0
            datu=self.psd(tmpdat.real,fs,noise=noise[0],n_pad=n_pad)
            datv=self.psd(tmpdat.imag,fs,noise=noise[1],n_pad=n_pad)
        else:
            datu=self.psd(veldat[0],fs,noise=noise[0],n_pad=n_pad)
            datv=self.psd(veldat[1],fs,noise=noise[1],n_pad=n_pad)
        datw=self.psd(veldat[2],fs,noise=noise[2],n_pad=n_pad)
        out=np.empty([3]+list(datw.shape),dtype=np.float32)
        if ma.valid:
            if self.hz:
                units=ma.unitsDict({'s':-2,'m':-2,'hz':-1})
            else:
                units=ma.unitsDict({'s':-1,'m':-2})
            out=ma.marray(out,ma.varMeta('S_{%s%s}',units,veldat.meta.dim_names+['freq']))
        out[:]=datu,datv,datw
        return out
    
