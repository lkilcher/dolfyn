import pkg_resources
import dolfyn.main as dlfn
import dolfyn.adp.api as apm
import dolfyn.adv.api as avm
import dolfyn.test.compare_legacy as cmp

fname_old = pkg_resources.resource_filename(
    'dolfyn.test',
    'data/winriver01.h5',
    #'data/RDI_test01.h5',
    #'data/AWAC_test01.h5',
    #'data/burst_mode01.h5'
)

fname_new = pkg_resources.resource_filename(
    'dolfyn',
    'example_data/winriver01.PD0'
    #'example_data/RDI_test01.000'
    #'example_data/AWAC_test01.wpr'
    #'example_data/burst_mode01.VEC'
)


dato = apm.load_legacy(fname_old, 'ALL')
datn = dlfn.read(fname_new)

if datn.props['inst_make'] == 'RDI':
    dato.groups['sys'] = dato.groups.pop('index')
    dato.add_data('range', dato.pop_data('ranges'), 'main')
    for ky in ['inst_make', 'inst_model',
               'inst_type', 'rotate_vars']:
        datn.props.pop(ky)
try:
    datn['config']['_type'] = datn.config.config_type
except AttributeError:
    pass

assert cmp.compare_new2old(datn, dato), 'FAIL'
assert cmp.compare_old2new(dato, datn), 'FAIL2'
print('Yay!')
