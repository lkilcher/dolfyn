import dolfyn.adv.base as avm
import dolfyn.io.nortek as nrtk
import dolfyn.adv.motion as avmot
import numpy as np
reload(nrtk)
reload(avm)
reload(avmot)

dat = avm.load('test/data/vector_data_imu01_mc.h5', 'ALL')

tdm = nrtk.read_nortek('example_data/vector_data_imu01.VEC')
tdm.props['body2head_rotmat'] = np.eye(3)
tdm.props['body2head_vec'] = np.array([-1.0, 0.5, 0.2])
avmot.correct_motion(tdm)

# dat_imu = avm.load('test/data/vector_data_imu01.h5', 'ALL')

# def read_test(make_data=False):

#     tdm = avm.read_nortek('example_data/vector_data_imu01.VEC')
#     # These values are not correct for this data but I'm adding them for
#     # test purposes only.
#     tdm.props['body2head_rotmat'] = np.eye(3)
#     tdm.props['body2head_vec'] = np.array([-1.0, 0.5, 0.2])

#     if make_data:
#         td.save(test_root + 'data/vector_data01.h5')
#         tdm.save(test_root + 'data/vector_data_imu01.h5')
#         return

#     err_str = ("The output of read_nortek('vector_data01.VEC') "
#                "does not match 'vector_data01.h5'.")
#     assert td == dat, err_str
#     err_str = ("The output of read_nortek('vector_data_imu01.VEC') "
#                "does not match 'vector_data_imu01.h5'.")
#     assert tdm == dat_imu, err_str

