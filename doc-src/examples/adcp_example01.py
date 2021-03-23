# Start by importing DOLfYN:
import dolfyn as dlfn

# Then read a file containing adv data:
dat = dlfn.read('../../dolfyn/example_data/Sig1000_IMU.ad2cp')

# Filter velocities greater than 3 (m/s for this data)
dlfn.adcp.clean.vel_exceeds_thresh(dat, thresh=3, source='inst')

# Clean NaN's in data by depth bin first
dlfn.adcp.clean.fillgaps_time(dat)
# Data can also be filled in by profile
dlfn.adcp.clean.fillgaps_depth(dat)

# Rotate data from the instrument to true ENU (vs magnetic) frame:
# First set the magnetic declination
dat.set_declination(10) # 10 degrees East
dat = dat.rotate2('earth')

# Define an averaging object, and create an 'ensembled' data set:
binner = dlfn.VelBinner(n_bin=300, fs=dat.props['fs'])
dat_bin = binner.do_avg(dat)

# At any point you can save the data:
dat_bin.to_hdf5('adcp_data.h5')

# And reload the data:
dat_bin_copy = dlfn.load('adcp_data.h5')
