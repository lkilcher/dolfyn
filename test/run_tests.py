import dolfyn.adv.api as avm
import numpy as np


def read_test(make_data=False):

    td = avm.read_nortek('../example_data/vector_data01.VEC')
    tdm = avm.read_nortek('../example_data/vector_data_imu01.VEC')
    # These values are not correct for this data
    tdm.props['body2head_rotmat'] = np.eye(3)
    tdm.props['body2head_vec'] = np.array([-1.0, 0.5, 0.2])  

    if make_data:
        td.save('data/vector_data01.h5')
        tdm.save('data/vector_data_imu01.h5')
        return

    cd = avm.load('data/vector_data01.h5', 'ALL')
    cdm = avm.load('data/vector_data_imu01.h5', 'ALL')

    assert td == cd, "The output of read_nortek('vector_data01.VEC') does not match 'vector_data01.h5'."
    assert tdm == cdm, "The output of read_nortek('vector_data_imu01.VEC') does not match 'vector_data_imu01.h5'."


def motion_test(make_data=False):
    mc = avm.motion.CorrectMotion()
    tdm = avm.load('data/vector_data_imu01.h5')
    mc(tdm)

    if make_data:
        tdm.save('data/vector_data_imu01_mc.h5')
        return

    cdm = avm.load('data/vector_data_imu01_mc.h5')

    assert tdm == cdm

if __name__ == '__main__':
    read_test()
    motion_test()

    print('All tests passed!')
