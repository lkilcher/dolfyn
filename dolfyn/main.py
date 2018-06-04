import pkg_resources
from .io.api import read
from .io.hdf5 import load


def read_example(name, **kwargs):
    """Read an example data file.

    Parameters
    ==========
    name : string
        Available files:

            AWAC_test01.wpr
            BenchFile01.ad2cp
            RDI_test01.000
            burst_mode01.VEC
            vector_data01.VEC
            vector_data_imu01.VEC
            winriver01.PD0
            winriver02.PD0

    Returns
    =======
    dat : ADV or ADP data object.

    """
    filename = pkg_resources.resource_filename(
        'dolfyn',
        'example_data/' + name)
    return read(filename, **kwargs)
