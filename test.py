import dolfyn.adv.base as avm
import dolfyn.io.nortek as nrtk
reload(nrtk)
reload(avm)

# # d=np.zeros(100)
# rdr = nrtk.NortekReader(datfile, debug=False, do_checksum=True)
# rdr.readfile()
# rdr.dat2sci()
# dat = rdr.data


dat = avm.load('test/data/vector_data01.h5', 'ALL')
# dat_imu = avm.load('test/data/vector_data_imu01.h5', 'ALL')

# def read_test(make_data=False):

#     td = avm.read_nortek('example_data/vector_data01.VEC')
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

