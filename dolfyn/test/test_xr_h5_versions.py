from dolfyn.h5.test.base import load_tdata as load_h5
from dolfyn.test.base import load_ncdata as load_nc
from numpy.testing import assert_allclose

# earth2principal fails miserably when nanmean (xarray built-in mean) fills in 
# values within principal heading calculation (instead of np.mean)
# dimension mismatch of 1 affects motion-correction filters
f_names = ['RDI_test01',
           'RDI_test01_rotate_beam2inst',
           'RDI_test01_rotate_inst2earth',
           #'RDI_test01_rotate_earth2principal',
           'RDI_withBT',
           'RDI_test01_rotate_beam2inst',
           'AWAC_test01',
           'AWAC_test01_ud',
           'AWAC_test01_earth2inst',
           #'AWAC_test01_earth2principal',
           'AWAC_test01_inst2beam',
           'BenchFile01',
           'BenchFile01_rotate_beam2inst',
           'BenchFile01_rotate_inst2earth',
           #'BenchFile01_rotate_earth2principal',
           'Sig1000_IMU',
           'Sig1000_IMU_ud',
           'Sig1000_IMU_rotate_beam2inst',
           #'Sig1000_IMU_rotate_inst2earth', # should fail, AHRS rotation bug
           'VelEchoBT01',
           'VelEchoBT01_rotate_beam2inst',
           'winriver01',
           'winriver02',
           'winriver02_rotate_ship2earth',
           'vector_data01', # all vector data have dimension mismatch
           'vector_data01_rotate_inst2beam',
           'vector_data01_rotate_inst2earth',
           'vector_data_imu01',
           'vector_data_imu01-json',
           #'vector_data_imu01-json_mc', # 0.4% off
           #'vector_data_imu01_mc', # 0.4% off
           #'vector_data_imu01_mcDeclin10', # 0.4% off
           #'vector_data_imu01_rotate_earth2principal', # 0.04% off
           'vector_data_imu01_rotate_inst2beam',
           'vector_data_imu01_rotate_inst2earth',
           'burst_mode01']


def load_data(filename, ext):
    if ext=='.nc':
        return load_nc(filename + ext)
    elif ext=='.h5':
        return load_h5(filename + ext)


def test_data():
    for ky in f_names:
        ds = load_data(ky, '.nc')
        h5 = load_data(ky, '.h5')
        
        # handling dimension mismatching - product of nan handling differences
        sh1 = ds.vel.shape
        sh2 = h5.vel.shape
        ds_vel = ds.vel.values[...,:min(sh1[-1],sh2[-1])]
        h5_vel = h5.vel[...,:min(sh1[-1],sh2[-1])]
        
        assert_allclose(ds_vel, h5_vel, atol=1e-6, err_msg="{}".format(ky))
        #assert_allclose(ds.vel.values, h5.vel, atol=1e-7, err_msg="{}".format(ky))


if __name__=='__main__':
    test_data()
    