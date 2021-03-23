import numpy as np
from matplotlib import pyplot as plt
plt.rcParams.update({'font.size': 22})
import matplotlib.dates as mpldt

import dolfyn as dlfn


## User-input data
fname = '../dolfyn/example_data/vector_data_imu01.VEC'
accel_filter = .03 # motion correction filter [Hz]
ensemble_size = 32*300 # sampling frequency * 300 seconds

# Read the data in, use the '.userdata.json' file
data_raw = dlfn.read(fname, userdata=True)

# Crop the data for t_range using DOLfYN's 'subset' method (creates a copy)
# The time range of interest:
t_range = [mpldt.date2num(mpldt.datetime.datetime(2012, 6, 12, 12, 8, 30)), np.inf]

t_range_inds = (t_range[0] < data_raw.mpltime) & (data_raw.mpltime < t_range[1])
data = data_raw.subset[t_range_inds]

# Clean the file using the Goring+Nikora method:
dlfn.adv.clean.GN2002(data)

# plotting raw vs qc'd data
ax = plt.figure(figsize=(20,10)).add_axes([.14, .14, .8, .74])
ax.plot(data_raw.mpltime, data_raw.u, label='raw data')
ax.plot(data.mpltime, data.u, label='despiked')
ax.set_xlabel('Time (HH:MM)')
ax.xaxis.set_major_formatter(mpldt.DateFormatter('%H:%M'))
ax.set_ylabel('u-dir velocity, (m/s)')
ax.set_title('Raw vs Despiked Data')
plt.legend(loc='upper right')
plt.show()


## Perform motion correction
data_cleaned = data.copy()

dlfn.adv.motion.correct_motion(data, accel_filter, to_earth=False)
# For reference, dolfyn defines ‘inst’ as the IMU frame of reference, not 
# the ADV sensor head
# After motion correction, the pre- and post-correction datasets coordinates
# may not align. Since here the ADV sensor head and battery body axes are
# aligned, data.u is the same axis as data_cleaned.u

# Plotting corrected vs uncorrect velocity in instrument coordinates
ax = plt.figure(figsize=(20,10)).add_axes([.14, .14, .8, .74])
ax.plot(data.mpltime, data_cleaned.u, 'g-', label='uncorrected')
ax.plot(data.mpltime, data.u, 'b-', label='motion-corrected')
ax.set_xlabel('Time (HH:MM)')
ax.xaxis.set_major_formatter(mpldt.DateFormatter('%H:%M'))
ax.set_ylabel('u velocity, (m/s)')
ax.set_title('Pre- and Post- Motion Corrected Data in XYZ coordinates')
plt.legend(loc='upper right')
plt.show()


## Rotate the uncorrected data into the earth frame for comparison to motion correction:
data = data.rotate2('earth')
data_uncorrected = data_cleaned.rotate2('earth')


## Calc principal heading (from earth coordinates) and rotate into 'principal axes frame'
# This function assumes n_fft = bin size when creating spectra
def princ_head(data, n_bin):
    # Calculates principal heading for each bin/ensemble.
    # Useful for tidal channels whose principal flow direction changes with
    # velocity.
    # Splits data apart into the ensembles used to create spectral FFT
    # windows and calculates the principal heading for each, then concatenates
    # the data back together.
    windows = dict()
    for i in range(int(np.floor(len(data.u)/n_bin))):
        # split data into ensembles of size n_bin
        ensemble = np.arange(n_bin*i, n_bin + n_bin*i)
        windows[i] = data.subset[ensemble]
        
        # calculate principal heading for each ensemble
        windows[i].props['principal_heading'] = dlfn.calc_principal_heading(windows[i].vel)
        #print(windows[i].props['principal_heading'])
        windows[i] = windows[i].rotate2('principal')

        if i!=0: 
            # cannot reconcatenate if the prop dictionary is different
            windows[i].props = windows[0].props
            # append data back together
            windows[0].append(windows[i])

    return windows[0]

data = princ_head(data, ensemble_size)
data_uncorrected = princ_head(data_uncorrected, ensemble_size)

# Plotting corrected vs uncorrected velocity in principal coordinates
ax = plt.figure(figsize=(20,10)).add_axes([.14, .14, .8, .74])
ax.plot(data_uncorrected.mpltime, data_uncorrected.u, 'g-', label='uncorrected')
ax.plot(data.mpltime, data.u, 'b-', label='motion-corrected')
ax.set_xlabel('Time (HH:MM)')
ax.xaxis.set_major_formatter(mpldt.DateFormatter('%H:%M'))
ax.set_ylabel('streamwise velocity, (m/s)')
ax.set_title('Corrected and Uncorrected Data in Principal Coordinates')
plt.legend(loc='upper right')
plt.show()


## Create velocity spectra
# Initiate tool to bin data based on the ensemble length. If n_fft is none,
# n_fft is equal to n_bin
ensemble_tool = dlfn.VelBinner(n_bin=ensemble_size, fs=data.props['fs'], n_fft=None)

# motion corrected data
data.spectra = ensemble_tool.do_spec(data)
# not-motion corrected data
unm_spectra = ensemble_tool.calc_vel_psd(data_uncorrected.vel)
# Find motion spectra from IMU velocity
uh_spectra = ensemble_tool.calc_vel_psd(data.orient['velacc'] + 
                                        data.orient['velrot'])

# Calc PSD frequency in Hz
freq = data.spectra['omega']/(2*np.pi)

# Plot U, V, W spectra
U = ['u','v','w'] # u:0, v:1, w:2
for i in range(len(U)):
    plt.figure(figsize=(15,13))
    plt.loglog(freq, np.mean(uh_spectra[i],0), 'c', 
               label=('motion spectra ' + str(accel_filter) + 'Hz filter'))
    plt.loglog(freq, np.mean(unm_spectra[i],0), 'r', label='uncorrected')
    plt.loglog(freq, np.mean(data.spectra['vel'][i],0), 'b', label='motion corrected')

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

