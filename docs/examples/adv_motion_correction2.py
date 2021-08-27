import numpy as np
from datetime import datetime
import dolfyn as dlfn
import dolfyn.adv.api as api

from matplotlib import pyplot as plt
from matplotlib import dates as mpldt


## User-input data
fname = '../dolfyn/example_data/vector_data_imu01.VEC'
accel_filter = .03 # motion correction filter [Hz]
ensemble_size = 32*300 # sampling frequency * 300 seconds

# Read the data in, use the '.userdata.json' file
data_raw = dlfn.read(fname, userdata=True)

# Crop the data for the time range of interest:
t_range = [dlfn.time.date2epoch(datetime(2012, 6, 12, 12, 8, 30)), np.inf]
t_range_inds = (t_range[0] < data_raw.time) & (data_raw.time < t_range[1])

data = data_raw.isel(time=t_range_inds)
# For plotting time on x-axis
dt = dlfn.time.epoch2date(data.time)

# Clean the file using the Goring+Nikora method:
bad = api.clean.GN2002(data.vel)
data['vel'] = api.clean.clean_fill(data.vel, bad, method='cubic')
# data.coords['mask'] = (('dir','time'), ~bad)
# data.vel.values = data.vel.where(data.mask)

# plotting raw vs qc'd data
ax = plt.figure(figsize=(20,10)).add_axes([.14, .14, .8, .74])
ax.plot(dlfn.time.epoch2date(data_raw.time), data_raw.Veldata.u, label='raw data')
ax.plot(dt, data.Veldata.u, label='despiked')
ax.set_xlabel('Time')
ax.xaxis.set_major_formatter(mpldt.DateFormatter('%D %H:%M'))
ax.set_ylabel('u-dir velocity, (m/s)')
ax.set_title('Raw vs Despiked Data')
plt.legend(loc='upper right')
plt.show()

data_cleaned = data.copy(deep=True)

## Perform motion correction
data = api.correct_motion(data, accel_filter, to_earth=False)
# For reference, dolfyn defines ‘inst’ as the IMU frame of reference, not 
# the ADV sensor head
# After motion correction, the pre- and post-correction datasets coordinates
# may not align. Since here the ADV sensor head and battery body axes are
# aligned, data.u is the same axis as data_cleaned.u

# Plotting corrected vs uncorrect velocity in instrument coordinates
ax = plt.figure(figsize=(20,10)).add_axes([.14, .14, .8, .74])
ax.plot(dt, data_cleaned.Veldata.u, 'g-', label='uncorrected')
ax.plot(dt, data.Veldata.u, 'b-', label='motion-corrected')
ax.set_xlabel('Time')
ax.xaxis.set_major_formatter(mpldt.DateFormatter('%D %H:%M'))
ax.set_ylabel('u velocity, (m/s)')
ax.set_title('Pre- and Post- Motion Corrected Data in XYZ coordinates')
plt.legend(loc='upper right')
plt.show()


## Rotate the uncorrected data into the earth frame for comparison to motion correction:
data = dlfn.rotate2(data, 'earth')
data_uncorrected = dlfn.rotate2(data_cleaned, 'earth')

# Calc principal heading (from earth coordinates) and rotate into 'principal axes frame'
data.attrs['principal_heading'] = dlfn.calc_principal_heading(data.vel)
data_uncorrected.attrs['principal_heading'] = dlfn.calc_principal_heading(
    data_uncorrected.vel)

# Plotting corrected vs uncorrected velocity in principal coordinates
ax = plt.figure(figsize=(20,10)).add_axes([.14, .14, .8, .74])
ax.plot(dt, data_uncorrected.Veldata.u, 'g-', label='uncorrected')
ax.plot(dt, data.Veldata.u, 'b-', label='motion-corrected')
ax.set_xlabel('Time')
ax.xaxis.set_major_formatter(mpldt.DateFormatter('%D %H:%M'))
ax.set_ylabel('streamwise velocity, (m/s)')
ax.set_title('Corrected and Uncorrected Data in Principal Coordinates')
plt.legend(loc='upper right')
plt.show()


## Create velocity spectra
# Initiate tool to bin data based on the ensemble length. If n_fft is none,
# n_fft is equal to n_bin
ensemble_tool = api.ADVBinner(n_bin=ensemble_size, fs=data.fs, n_fft=None)

# motion corrected data
mc_spec = ensemble_tool.calc_vel_psd(data.vel, freq_units='Hz')
# not-motion corrected data
unm_spec = ensemble_tool.calc_vel_psd(data_uncorrected.vel, freq_units='Hz')
# Find motion spectra from IMU velocity
uh_spec = ensemble_tool.calc_vel_psd(data['velacc'] + data['velrot'], 
                                     freq_units='Hz')

# Plot U, V, W spectra
U = ['u','v','w'] # u:0, v:1, w:2
for i in range(len(U)):
    plt.figure(figsize=(15,13))
    plt.loglog(uh_spec.f, uh_spec[i].mean(axis=0), 'c', 
               label=('motion spectra ' + str(accel_filter) + 'Hz filter'))
    plt.loglog(unm_spec.f, unm_spec[i].mean(axis=0), 'r', label='uncorrected')
    plt.loglog(mc_spec.f, mc_spec[i].mean(axis=0), 'b', label='motion corrected')

    # plot -5/3 line
    f_tmp = np.logspace(-2, 1)
    plt.plot(f_tmp, 4e-5*f_tmp**(-5/3), 'k--', label='f^-5/3 slope')

    if U[i]=='u':
        plt.title('Spectra in streamwise dir')
    elif U[i]=='v':
        plt.title('Spectra in cross-stream dir')
    else:
        plt.title('Spectra in up dir')
    plt.xlabel('Freq [Hz]')
    plt.ylabel('$\mathrm{[m^2s^{-2}/Hz]}$', size='large')
    plt.legend()
plt.show()
