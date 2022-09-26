# Start by importing DOLfYN:
import dolfyn
import dolfyn.adp.api as api

# Then read a file containing adv data:
ds = dolfyn.read_example('BenchFile01.ad2cp')

# This ADCP was sitting 0.5 m up from the seabed
# in a tripod
api.clean.set_range_offset(ds, h_deploy=0.5)

# Filter the data by low correlation values (< 50% here)
ds = api.clean.correlation_filter(ds, thresh=50)

# Rotate data from the instrument to true ENU (vs magnetic) frame:
# First set the magnetic declination
dolfyn.set_declination(ds, 10)  # 10 degrees East
dolfyn.rotate2(ds, 'earth')

# At any point you can save the data:
#dolfyn.save(dat_cln, 'adcp_data.nc')

# And reload the data:
#dat_copy = dolfyn.load('adcp_data.nc')
