# Start by importing DOLfYN:
import dolfyn as dlfn

# Then read a file containing adv data:
dat = dlfn.read('../../../data/vector_data01.VEC')

dlfn.adcp.clean.vel_exceeds_thresh(dat, thresh=3, source='inst')

# Clean NaN's in data by depth bin first
dlfn.adcp.clean.fillgaps_time(dat)
# Data can also be filled in by profile
dlfn.adcp.clean.fillgaps_depth(dat)

# Rotate that data from the instrument to true ENU (vs magnetic) frame:
# First set the magnetic declination
dat.set_declination(10) # 10 degrees East
dat = dlfn.rotate2(dat, 'earth')

# Define an averaging object, and create an 'ensembled' data set:
binner = dlfn.VelBinner(n_bin=300, fs=dat.props['fs'], n_fft=300)
dat_bin = binner(dat)

# At any point you can save the data:
dat_bin.to_hdf5('adcp_data.h5')

# And reload the data:
dat_bin_copy = dlfn.load('adcp_data.h5')
