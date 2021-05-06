import pkg_resources
import dolfyn.main as dlfn
import dolfyn.adp.api as apm
import dolfyn.adv.api as avm
import dolfyn.adv.base as adv_base
import dolfyn.test.compare_legacy as cmp

fnm = (
#    'winriver02.PD0'
#    'winriver01.PD0'
#    'RDI_test01.000'
#    'AWAC_test01.wpr'
#    'burst_mode01.VEC'
#    'vector_data01.VEC'
    #'vector_data_imu01.VEC'
    'BenchFile01.ad2cp'
)



fname_old = pkg_resources.resource_filename(
    'dolfyn.test',
    'data/' + fnm.rsplit('.')[0] + '.h5'
)

fname_new = pkg_resources.resource_filename(
    'dolfyn',
    'example_data/' + fnm
)

if fnm in ['vector_data01.VEC',
           'vector_data_imu01.VEC']:
    nens = 100
else:
    nens = None

datn = dlfn.read(fname_new, nens=nens)
if isinstance(datn, adv_base.ADVraw):
    dato = avm.load_legacy(fname_old, 'ALL')
else:
    dato = apm.load_legacy(fname_old, 'ALL')

if datn.props['inst_make'] in 'RDI':
    dato.groups['sys'] = dato.groups.pop('index')
    dato.add_data('range', dato.pop_data('ranges'), 'main')
    for ky in ['inst_make', 'inst_model',
               'inst_type', 'rotate_vars']:
        datn.props.pop(ky)
if datn.props['inst_model'] in 'Signature':
    for ky in ['inst_make', 'inst_model',
               'inst_type']:
        datn.props.pop(ky)
    dato.groups.add(['heading', 'pitch', 'roll'], 'orient')

try:
    datn['config']['_type'] = datn.config.config_type
except AttributeError:
    pass

fail = False
if not cmp.compare_new2old(datn, dato):
    fail = True
    print("Comparing new->old failed.")
if not cmp.compare_old2new(dato, datn):
    fail = True
    print("Comparing old->new failed.")
if not fail:
    print('Yay, everything passed!')
