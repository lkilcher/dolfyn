# Start by importing DOLfYN:
import dolfyn as dlfn
import dolfyn.adp.api as apm
import matplotlib.pyplot as plt

# Then read a file containing adv data:
dat = dlfn.read_example('BenchFile01.ad2cp')

# Filter beam data with correlation < 70%
dat_cln = apm.clean.correlation_filter(dat, thresh=70)

# Fill in NaN's in data by depth bin first
dat_cln = apm.clean.fillgaps_time(dat_cln)
# Data can also be filled in by profile
dat_cln = apm.clean.fillgaps_depth(dat_cln)

# Rotate data from the instrument to true ENU (vs magnetic) frame:
# First set the magnetic declination
dat_cln = dat_cln.Veldata.set_declination(10) # 10 degrees East
dat_earth = dlfn.rotate2(dat_cln, 'earth')

# Define an averaging object, and create an 'ensembled' data set:
binner = dlfn.VelBinner(n_bin=300, fs=dat.fs)
dat_bin = binner.do_avg(dat_earth)

# At any point you can save the data:
dlfn.save(dat_bin, 'adcp_data.nc')

# And reload the data:
dat_bin_copy = dlfn.load('adcp_data.nc')

plt.figure()
plt.pcolormesh(dat_bin.time, dat_bin.range, dat_bin.Veldata.U_mag)
plt.ylabel('Range [m]')
plt.xlabel('Time')