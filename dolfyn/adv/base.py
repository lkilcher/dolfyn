"""
The base module for the adv package.
"""
#from ..data import base as db
from ..io import main as dio
from pycoda.base import data
from pycoda.io import load_hdf5
from ..data import velocity as dbvel
import numpy as np
from ..data.base import config, SpecData
from ..data import base_old
from matplotlib import dates as dt

# import turbulence as turb

# This is the body->imu vector (in body frame)
# In inches it is: (0.25, 0.25, 5.9)
body2imu = {'Nortek VECTOR': np.array([0.00635, 0.00635, 0.14986])}


class ADVconfig(data):

    """
    A base class for ADV config objects.
    """
    # Is this needed?
    pass


class ADVraw(dbvel.Velocity):

    """
    The base class for ADV data objects.
    """

    # def subset(self, inds=None, time_range=None):
    #     if inds is None and time_range is None:
    #         raise Exception("Either inds or time_range must be specified.")
    #     elif inds is not None:
    #     if time_range is not None:
    #         if time_range[0] is None:
    #             i0 = 0
    #         else:
    #             inds =

    @property
    def fs(self, ):
        return self.props['fs']

    @property
    def make_model(self,):
        return self.props['inst_make'] + ' ' + self.props['inst_model']

    @property
    def body2imu_vec(self,):
        # Currently only the Nortek VECTOR has an IMU.
        return body2imu[self.make_model]

    def has_imu(self,):
        """
        Test whether this data object contains Inertial Motion Unit
        (IMU) data.
        """
        return 'Accel' in self.orient


class ADVbinned(dbvel.VelBindatSpec, ADVraw):

    """
    A base class for binned ADV objects.
    """
    # Is this needed?
    pass


# # Get the data classes in the current namespace:
type_map = dio.get_typemap(__name__)
# # This is for backward compatability (I changed the names of these
# # classes to conform with PEP8 standards):
type_map.update(
    {'adv_raw': ADVraw,
     'adv_config': ADVconfig,
     'adv_binned': ADVbinned,
     'ADVraw': ADVraw,
     'ADVconfig': ADVconfig,
     'ADVbinned': ADVbinned,
     })


def remap_config(old_cfg, new_cfg=None):
    if new_cfg is None:
        new_cfg = config()
    for nm in old_cfg:
        if isinstance(old_cfg[nm], base_old.config):
            new_cfg[nm] = config(_type=old_cfg[nm].config_type)
            remap_config(old_cfg[nm].main, new_cfg[nm])
        else:
            new_cfg[nm] = old_cfg[nm]
    return new_cfg


def load(fname, ):
    try:
        return load_hdf5(fname, )
    except KeyError:
        out = load_old(fname, data_groups='ALL', type_map=type_map)
        main = out.pop('main')
        for nm in main:
            out[nm] = main[nm]
        out['vel'] = out.pop('_u')
        out['env']['pressure'] = out.pop('pressure')
        ess = out.pop('_essential')
        for val in ess:
            out[val] = ess[val]
        out['orient']['orientation_down'] = out.pop('orientation_down')
        out['sys'] = out.pop('#sys', data())
        out['sys']['_sysi'] = out.pop('_sysi')
        out['props']['rotate_vars'].remove('_u')
        out['props']['rotate_vars'].add('vel')
        for val in out['props']['rotate_vars']:
            if val in ['Accel', 'AngRt', 'Mag', 'AccelStable',
                       'uacc', 'urot', 'uraw']:
                out.props['rotate_vars'].remove(val)
                if val.startswith('u'):
                    val = 'vel_' + val[1:]
                if val not in ['vel_raw']:
                    val = 'orient.' + val
                out.props['rotate_vars'].add(val)
        out['_extra'] = out.pop('#extra', data())
        out['_extra']['AnaIn2MSB'] = out.env.pop('AnaIn2MSB')
        sig = out.pop('signal')
        out['sys']['corr'] = sig['_corr']
        out['sys']['amp'] = sig['_amp']
        if 'spec' in out:
            out['Spec'] = SpecData()
            tmp_specdata = out.pop('spec')
            out.Spec['vel'] = tmp_specdata['Spec']
            out.Spec['omega'] = out.pop('omega')
            out['orient']['Spec'] = SpecData()
            if 'Spec_uacc' in tmp_specdata:
                out['orient']['Spec']['vel_acc'] = tmp_specdata['Spec_uacc']
            if 'Spec_urot' in tmp_specdata:
                out['orient']['Spec']['vel_rot'] = tmp_specdata['Spec_urot']
            if 'Spec_umot' in tmp_specdata:
                out['orient']['Spec']['vel_mot'] = tmp_specdata['Spec_umot']
            if len(out['orient']['Spec']) == 0:
                out['orient'].pop('Spec')
            else:
                out['orient']['Spec']['omega'] = out['Spec']['omega'].copy()
            if 'Spec_uraw' in tmp_specdata:
                out['Spec']['vel_raw'] = tmp_specdata['Spec_uraw']
        if '_tke' in out:
            out['vel2'] = out.pop('_tke')
        #out['env']['pressure'] = out.pop('pressure')
        if 'config' in out:
            cfg = out.config.config
            try:
                out['config'] = remap_config(out.pop('config'), config()).config
            except:
                out['config'] = data()
                pass
            out['config']['inst_type'] = cfg.config_type
            out['config']['_type'] = 'NORTEK'
        if 'orientmat' in out['orient']:
            out['orient']['mat'] = out['orient'].pop('orientmat')
        try:
            out['orient']['vel_rot'] = out.orient.pop('urot')
            out['orient']['vel_acc'] = out.orient.pop('uacc')
            out['vel_raw'] = out.pop('uraw')
        except:
            pass
        return out


def mmload():
    pass


def load_old(fname, data_groups=None, type_map=type_map):
    """
    Load ADV objects from hdf5 format.

    Parameters
    ----------
    fname : string
      The file to load.
    data_groups : {list(strings), None, 'ALL'}
      Specifies which groups to load.  It can be:

      - :class:`None`: Load default groups (those not starting with a '#')
      - :class:`list`: A list of groups to load (plus 'essential' groups, ie
        those starting with '_')
      - 'ALL': Load all groups.

    type_map : dict, type
      A dictionary that maps `class-strings` (stored in the data file)
      to available classes.
    """
    with dio.loader(fname, type_map) as ldr:
        return ldr.load(data_groups)


# def mmload(fname, type_map=type_map):
#     """
#     Memory-map load ADV objects from hdf5 format.

#     Parameters
#     ----------
#     fname : string
#       The file to load.
#     type_map : dict, type
#       A dictionary that maps `class-strings` (stored in the data file)
#       to available classes.
#     """
#     with dio.loader(fname, type_map) as ldr:
#         return ldr.mmload('ALL')
