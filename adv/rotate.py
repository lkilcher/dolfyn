import numpy as np
import warnings
import scipy.signal as sig
from scipy.integrate import cumtrapz

sin=np.sin
cos=np.cos

def calcAccelVel(accel,samp_freq,filt_freq):
    """
    First filter the acceleration data.
    *samp_freq* is the sampling frequency.
    *filt_freq* is the frequency to filter at.
    """
    # 8th order butterworth filter.
    print float(filt_freq)/(samp_freq/2)
    filt=sig.butter(2,float(filt_freq)/(samp_freq/2))
    #hp=np.empty_like(accel)
    #for idx in range(accel.shape[0]):
    #    hp[idx]=accel[idx]-sig.filtfilt(filt[0],filt[1],accel[idx])
    hp=accel
    shp=list(accel.shape[:-1])
    shp+=[1]
    dat=np.concatenate((np.zeros(shp),cumtrapz(hp,dx=1./samp_freq)),axis=-1)
    for idx in range(accel.shape[0]):
        dat[idx]=dat[idx]-sig.filtfilt(filt[0],filt[1],dat[idx])
    # NOTE: The minus sign is because the measured induced velocities are in the opposite direction of the head motion.
    #       i.e. when the head moves one way in stationary flow, it measures a velocity in the other direction.
    return -dat


def calcRotationVel(AngRt,vec_imu2sample):
    """
    Calculate the induced velocity due to rotations of the ADV.

    This is based on the Angular Rate *AngRt* data and the vector, *vec_imu2sample*.

    Returns:
      A tuple of u,v,w velocities induced by the rotations.
    """
    # This motion of the head due to rotations should be the cross-product of omega (rotation vector) and the vector from the IMU to the ADV sample volume.
    #           u=dz*omegaY-dy*omegaZ,v=dx*omegaZ-dz*omegaX,w=dy*omegaX-dx*omegaY
    # where vec_imu2sample=[dx,dy,dz], and AngRt=[omegaX,omegaY,omegaZ]
    # NOTE: The minus sign is because the measured-induced velocities are in the opposite direction of the head motion.
    #       i.e. when the head moves one way in stationary flow, it measures a velocity in the opposite direction.
    return -np.array([vec_imu2sample[2]*AngRt[1]-vec_imu2sample[1]*AngRt[2],vec_imu2sample[0]*AngRt[2]-vec_imu2sample[2]*AngRt[0],vec_imu2sample[1]*AngRt[0]-vec_imu2sample[0]*AngRt[1]])

def orient2euler(obj):
    """
    Returns the euler angle orientation of the ADV, calculated from the orientation matrix.
      Cite: Microstrain2012a

    Returns:
    *pitch*,*roll*,*heading* (deg,deg,deg true)
    """
    if hasattr(obj,'orientmat'):
        omat=obj.orientmat
    elif np.ndarray in obj.__class__.__mro__ and obj.shape[:2]==(3,3):
        omat=obj
    # I'm pretty sure the 'yaw' is the angle from the east axis, so we correct this for 'deg_true':
    return 180/np.pi*np.arcsin(-omat[0,2]),180/np.pi*np.arctan2(omat[1,2],omat[2,2]),(np.pi/2-np.arctan2(omat[0,1],omat[0,0]))*180/np.pi

def cat4rot(tpl):
    tmp=[]
    for vl in tpl:
        tmp.append(vl[None,:])
    return np.concatenate(tuple(tmp),axis=0)

def inst2earth(advo,use_mean_rotation=False):
    """
    Rotate the data from the instrument frame to the earth frame.

    The rotation matrix is computed from heading, pitch, and roll
    .
    Taken from a "Coordinate transformation" script on the nortek site.
    
    --References--
    http://www.nortek-as.com/en/knowledge-center/forum/software/644656788
    http://www.nortek-as.com/en/knowledge-center/forum/software/644656788/resolveuid/af5dec86a5df8e7fd82a2f2aed1bc537
    """
    rr=advo.roll*np.pi/180
    pp=advo.pitch*np.pi/180
    hh=(advo.heading-90)*np.pi/180
    if use_mean_rotation==True:
        rr=np.angle(np.exp(1j*rr).mean())
        pp=np.angle(np.exp(1j*pp).mean())
        hh=np.angle(np.exp(1j*hh).mean())
    if advo.props.has_key('declination'):
        hh+=(advo.props['declination']*np.pi/180) # Declination is in degrees East, so we add this to True heading.
    else:
        warnings.warn('No declination in adv object.  Assuming a declination of 0.')
    if advo.props.has_key('heading_offset'):
        hh+=advo.props['heading_offset']*np.pi/180  # Offset is in CCW degrees that the case was offset relative to the head.
    if advo.config.orientation=='down':
        # NOTE: For ADVs: 'down' configuration means the head was pointing UP!
        #       check the Nortek coordinate transform matlab script for more info.
        #       The 'up' orientation corresponds to the communication cable begin up.
        #       This is ridiculous, but apparently a reality.
        rr+=np.pi
        # I did some of the math, and this is the same as multiplying rows 2 and 3 of the
        # T matrix by -1 (in the ADV coordinate transform script), and also the same as
        # multiplying columns 2 and 3 of the heading matrix by -1.  Anyway, I did it
        # this way to be consistent with the ADCP rotation script, which looks similar.
        #
        # The way it is written in the adv CT script is annoying:
        #    T and T_org, and minusing rows 2+3 of T, which only goes into R, but using T_org
        #    elsewhere.
    if advo.config.coordinate_system=='XYZ' and not hasattr(advo,'u_inst'):
        advo.add_data('u_inst',advo.u,'inst')
        advo.add_data('v_inst',advo.v,'inst')
        advo.add_data('w_inst',advo.w,'inst')
    #### This is directly from the matlab script:
    ## H=np.zeros(shp)
    ## H[0,0]=cos(hh);  H[0,1]=sin(hh);
    ## H[1,0]=-sin(hh); H[1,1]=cos(hh);
    ## H[2,2]=1
    ## P=np.zeros(shp)
    ## P[0,0]=cos(pp);  P[0,1]=-sin(pp)*sin(rr); P[0,2]=-cos(rr)*sin(pp)
    ## P[1,0]=0;        P[1,1]=cos(rr);          P[1,2]=-sin(rr)
    ## P[2,0]=sin(pp);  P[2,1]=sin(rr)*cos(pp);  P[2,2]=cos(pp)*cos(rr)
    ##
    #### This is me redoing the math:
    ch=cos(hh);sh=sin(hh)
    cp=cos(pp);sp=sin(pp)
    cr=cos(rr);sr=sin(rr)
    ## rotmat=ch*cp,-ch*sp*sr+sh*cr,-ch*cr*sp-sh*sr;
    ##        -sh*cp,sh*sp*sr+ch*cr,sh*cr*sp-ch*sr;
    ##         sp,sr*cp,cp*cr
    #umat=np.empty((3,len(advo.u_inst)),dtype='single')
    #umat=np.tensordot(rotmat,cat4rot((advo.u_inst,advo.v_inst,advo.w_inst)),axes=(1,0)).astype('single')
    #### This is me actually doing the rotation:
    #R=np.dot(H,P)
    #u=
    u=((ch*cp)*advo.u_inst+(-ch*sp*sr+sh*cr)*advo.v_inst+(-ch*cr*sp-sh*sr)*advo.w_inst).astype('single')
    v=((-sh*cp)*advo.u_inst+(sh*sp*sr+ch*cr)*advo.v_inst+(sh*cr*sp-ch*sr)*advo.w_inst).astype('single')
    w=((sp)*advo.u_inst+(sr*cp)*advo.v_inst+cp*cr*advo.w_inst).astype('single')
    advo.add_data('u',u,'main')
    advo.add_data('v',v,'main')
    advo.add_data('w',w,'main')
    advo.props['coord_sys']='earth'
    
def earth2principal(advo,vrs=('u','v')):
    """
    Rotate the horizontal velocity into its principal axes.
    """
    #if advo.props['coord_sys']=='inst' and not hasattr(advo,'u_inst'):
    #    advo.add_data('u_inst',advo.u,group='inst')
    #    advo.add_data('v_inst',advo.v,group='inst')
    #    advo.add_data('w_inst',advo.w,group='inst')
    if advo.props['coord_sys']=='principal':
        return
    tmp=advo.U_rot(-advo.principal_angle)
    advo.u=tmp.real.astype('single')
    advo.v=tmp.imag.astype('single')
    advo.props['coord_sys']='principal'

def principal2earth(advo):
    """
    Rotate the horizontal velocity into earth coordinates.
    """
    tmp=advo.U_rot(advo.principal_angle)
    advo.u=tmp.real.astype('single')
    advo.v=tmp.imag.astype('single')
    advo.props['coord_sys']='earth'
    
