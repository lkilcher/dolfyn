import numpy as np
from ..data import base as db
from ..io import main as dio
from ..data import velocity as dbvel
from ..tools.psd import psd_freq
from scipy.special import cbrt
import copy
from ..OrderedSet import OrderedSet as oset
#import turbulence as turb
ma=db.ma

class adv_config(db.config):
    pass

class adv_raw(dbvel.velocity):

    def has_imu(self,):
        return hasattr(self,'Accel') | hasattr(self,'Veloc')

    pass
    ## @property
    ## def rotmat_beam(self,):
    ##     """
    ##     Returns the beam rotation matrix.
    ##     (Stored in the adv config.)
    ##     """
    ##     return self.config.transformation_matrix

class msadv_raw(adv_raw):
    """
    IMU-ADV class (i.e. Nortek ADV with a Microstrain inertial chip).
    """
    pass #For now this is a place holder.
    

class adv_binned(dbvel.vel_bindat_spec,adv_raw):
    pass
    ## @property
    ## def ustar_eps(self,):
    ##     return (self.epsilon/turb.kappa/self.props['hab'])**(1./3.)

    ## @property
    ## def phi_epsilon(self,):
    ##     return turb.kappa*self.epsilon*10./(self.ustar**3.)

    ## @property
    ## def Suu_f(self,):
    ##     return self.Suu*f_fac
    ## @property
    ## def Svv_f(self,):
    ##     return self.Svv*f_fac
    ## @property
    ## def Sww_f(self,):
    ##     return self.Sww*f_fac


type_map=dio.get_typemap(__name__) # Get the data classes in the current namespace.

def load(fname,data_groups=None,type_map=type_map):
    """
    A function for loading ADV objects.

    'data_groups' specifies which groups to load.  It can be:
        None  - Load default groups (those not starting with a '#')
        [...] - A list of groups to load (plus 'essential' groups, ie those starting with '_')
        'ALL' - Load all groups.
    """
    with dio.loader(fname,type_map) as ldr:
        return ldr.load(data_groups)

def mmload(fname,data_groups=None,type_map=type_map):
    with dio.loader(fname,type_map) as ldr:
        return ldr.mmload(data_groups)
