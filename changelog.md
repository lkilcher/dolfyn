# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## Unversioned
    - Bugfixes
	    - Correct CF convention "standard_names"
		- Rename debugger log files from ".log" to ".dolfyn.log"
		- Fix recording for instruments in "average" mode (vs "burst" mode)
		- Fix for instruments that did not record water velocity
		- Fix netCDF4 compression encoding
		- Retain prior netCDF4 variable encoding
		- Fix bug in reading raw Nortek Signature altimeter data
		- Fix bug where noise input wasn't being subtracted from auto-spectra

	- API/Useability
	    - Updates to support python 3.10 and 3.11
		- Added ability to read Nortek AWAC waves data
		- Added ability to subtract Doppler noise in TKE dissipation rate functions
		- Added function to calculate turbulence intensity and remove noise 

## Version 1.3.0
    - Bugfixes
		- Added check to ensure `n_bin` is shorter than the total data length when calling
		  `dolfyn.TimeBinner.reshape`
	    - Added checks to ensure `n_fft` and `n_fft_coh` can't be greater than `n_bin`
		- Fixed bug where `dolfyn.adp.nan_beyond_surface` overtrimmed TRDI instrument data
		- Fixed bug where `dolfyn.ADVBinner.calc_csd` would fail if `n_fft` != `n_fft_coh`
		- `VelBinner.std` and `VelBinner.var` can now handle nan values

    - API/Useability
	    - Calculation of depth from pressure sensor updated to use linear approximation of the
		  equation of state, rather than EOS-80
		- Added warnings for ADV motion-correction function
		- Updated `dataset.velds.U_dir` shortcut to automatically convert "degrees CCW from
		  X/East/streamwise" to "degrees CW from X/North/streamwise"
		- `dolfyn.ADVBinner.calc_csd` now returns frequency coordinate `coh_freq` instead of `freq`
		- Added "beam_angle" attribute to Nortek Signature datasets
		- Saved full Nortek Signature "config" dictionary as json string in attributes
		- Added warning if "rotate_vars" attribute not found
		- Added VMDAS variables containing GPS heading/pitch/roll (GPS must be AHRS-equipped for 
		  these to return non-zero)
		
		- Added ADCP turbulence functions
		- Added function to calculate Doppler noise to ADV turbulence functions
		- Added funtion to check slope of spectra's isotropic turbulence cascade

## Version 1.2.1
    - Bugfixes
	    - Fixed errors in docs and docstrings
		- Skipped unknown TRDI Ocean Surveyor ID codes

    - API/Useability
	    - Added CF convention metadata to variables

## Version 1.2.0
    - Bugfixes
	    - Fixed errors in TRDI reader that caused ensembles to be skipped
		- Variables found from NMEA data now all contain _gps tag
		- Calculate VMDAS and WinRiver sampling frequency from diff of time coordinate
	    - Fixed bug that dropped shared but differing "lag" coordinate between auto-covariance
		  and cross-covariance functions
	    - Fix duty cycle attributes for some Nortek instruments
		- Fix bug where 'accel' variable was rotated incorrectly in `correct_motion`
		- Fix bug where ADV IMU variables could not be rotated to beam coordinates

	- API/Useability
		- Added the ability for the TRDI reader to search for the VMDAS navigation header 
		  manually and determine which slot (nb vs bb) that VMDAS is saved in - Thank you jklymak!
		- Clarified VMDAS navigation block variable names
		- Added ability to read WinRiver2 NMEA data (GGA, VTG, HDT, DBT)
		- Added ability to read TRDI 5th beam altimeter data
		- Added ability to read RiverPro/StreamPro surface layer profile
		- Updated TRDI attribute names
		- Debugging readers now uses logging module
		- Add 'fill_nan_ensemble_mean' function to ADV cleaning methods
		- Spectra frequency coordinate name is set to 'freq', whether using radial (rad/s) or
		  classical (Hz) frequency units instead of 'omega' and 'f', respectively
	    - `correct_motion` is now capable of processing data from duty-cycled ADVs
	    - `CalcMotion` class is changed from private to public

## Version 1.1.0
    - Bugfixes
	    - "calc_tke" function now errors if given multi-beam ADCP velocity vector
	    - Clean thresh function failed to remove spikes
		- ADV despiking max gap input
		- Fix input error to calc_L_int
		- `dist_bt` and `prcnt_gd` variables should be in beam coordinates

	- API/Useability
		- Moved "calc_stress" and "calc_csd" functions to ADVBinner class
		- Removed "do_tke" function
		- Frequency units for calculating power spectral densities are consistently set to rad/s
		- Made base PSD and CPSD functions public
		- Renamed variable "stress" to "stress_vec" to stay consistent

## Version 1.0.2
    - Bugfixes
	    - Detect missing timestamps in ADV binary files

	- API/Useability
	    - Added classic Nortek instrument configuration details into dataset attributes

## Version 1.0.1
	- Bugfixes:
		- ADV and TRDI correlation and amplitude 'dir' dimension values
		  now remain in "beam" coordinates (#96)
		- Removed deployment height from surface interference cleaning 
		  (`find_surface_from_P`) calculation
		- Remove extra entry added to ADV time dimension when `read` is 
		  given "nens" argument
		- Auto-convert "maxgap" argument in ADCP "fillgaps_time" to numpy.timedelta64

	- API/Useability
		- Change functions in `TimeBinner` that use reshape (detrend, 
		  demean, mean, var, std) from private to public

## Version 1.0.0
	- Change the xarray dataset-accessor from `Veldata` to `velds`.
	- Begin reimplementing DOLfYN API in the velocity.Velocity class (accessed via velds above)
	- Switch from epoch time to datetime64 in datasets
	    - This also includes a bugfix where the epoch time was machine specific.
	- No longer Python 2 compatible.
	- Re-implement the 'inplace' argument for several API functions.

	- Nortek Signature (.ad2cp):
		- Fix some read issues
		- Decoded binary 'status' variables
		- Dropped 'temp_mag' (magnetometer temperature) - this thermistor isn't calibrated
		- Added 'xmit_energy' (beam transmit energy in dB) into data variables

## Version 0.13.0
	- Refactored source code to use xarray instead of h5py-derived data objects

	- Input/Output:
		- I/O now returns xarray Datasets
		- Variables names are now consistent across all instruments
		- Rotation and orientation matrices are all saved as xarray variables

		- Created functions to handle saving/loading dolfyn datasets to/from netCDF and MATLAB file formats
			- It is possible to open dolfyn datasets using `xarray.open_dataset()`, 
			  but not possible to save through` xarray.to_netcdf()`

		- Scaling bugs:
			- Fixed AWAC temperature scaling
			- Fixed scaling on all `ambig_vel` variables
			- Fixed Signature magnetometer to return in units of microTeslas
			- Fixed Nortek echosounder 'dB' scaling

		- Fixed error in Nortek 'range' calculation (bin 1 dist = blank dist + cell size)
		- Added function in the ADCP API to add the deployment depth to this range (`clean.set_deploy_altitude()`)

		- Rounded Nortek AWAC blanking distance and range to 2 decimal places
		- Read support for 2-4 beam

		- Fix error reading VMDAS-processed files
		- Switch from `'lonlat` to `latlon` as the designated entry-name in `dat.attrs`

		- Created function to handle nans in ADV orientation matrix data so that rotation code won't fail

		- Removed user-nonsensical configuration data
		- Changed true/false attributes to 1/0 - Logical values are auto-dropped when saving netCDF

	- Rotations:
		- `rotate2()`, `set_inst2head_rotmat()`, `calc_principal_heading()`, and `set_declination()` now 
		  located in `rotate.api` and can be accessed using `dolfyn.<function>`

		- Solved errors where orientation wasn't taken into account for Nortek Signatures
			- Fixed Nortek Signature rotation issues for fixed up vs down
			- Fixed AHRS-equipped Nortek Signature rotation issues
			- AHRS orientmat is the transpose of dolfyn's HPR-calculated orientation matrix

	- Motion correction code:
		- `CorrectMotion` object has been removed
		- replaced '.mean()' with `np.nanmean()` in `motion_correction()` and `calc_principal_heading()`

	- `TimeData`, `Velocity`, `TKEdata`:
		- `TimeData` class has been removed
		- Combined `Velocity` and `TKEdata` classes into `Velocity`, which now contains all dolfyn shortcuts
		- `Velocity` class is set up with xarray accessor `Veldata`
		- All properties return `xarray.DataArrays`
		- Added a property to calculate wavenumber `k` from the spectral frequency vector

	- TimeBinner, VelBinner, TurbBinner class refactoring:
		- Changed `.mean()` to `np.nanmean()` so functions can handle nans

		- `TurbBinner` renamed to `ADVBinner` and set in the ADV API

		- Renamed `calc_vel_psd()` and `calc_vel_csd()` to `calc_psd()` and `calc_csd()`
		- Fixed bug where `calc_vel_csd()` wasn't using "n_fft_coh" input
		- Added "freq_units" option to `calc_psd()` and `calc_csd()` using either frequency in Hz (f) or 
		  rad/s (omega) ("freq_units" input)
				- Renamed `calc_omega()` to `calc_freq()` and added "freq_units" as input
				- Calling `TurbBinner`/`calc_turbulence()` still automatically use 'rad/s'
		- FFT frequency "omega"|"f" is now a xarray coordinate rather than its own variable

		- "do" functions take Datasets as input, "calc" funtions take DataArrays as input

		- Updated `U_dir` description to be CCW from East (consistent with imag vs real axes)
		- Added `convert_degrees()` function in tools.misc to convert CCW from East to CW from North, and 
		  vice versa

		- Renamed `sigma_Uh` variable to `U_std` and moved it from adv.turbulence to velocity.VelBinner as 
		  a function in `do_avg()`
		- Renamed properties `Ecoh` to `E_coh` and `Itke` to `I_tke`
		- Removed `Itke_thresh` from `TurbBinner` and added to `Velocity` class as it is only used with the 
		  `I_tke` property

		- Coherence, phase_angle, and auto-/cross-covariance now work as described in their docstrings
			- Will take 1D or 3D velocity arrays as input
			- Renamed `cohere()` and `phase_angle()` to `calc_coh()` and `calc_phase_angle()`
			- Fixed bug where `tools.psd.coherence` wasn't correctly calling `tools.psd.cpsd` or 
			  `tools.psd.cpsd_quasisync`

		- Updated turbulence dissipation functions return correctly for xarray
			- Fixed `calc_turbulence()` '__call__' error
			- Removed inputs not used by `calc_turbulence()` and `ADVBinner` function call ('omega_range' 
			  and 'out_type')
			- These are stored in `turbulence.py` in the ADV API
			- LT83 or TE01 methods can take either the 1D or 3D velocity arrays as input
				- if 3D velocity given as input
					- 'LT83' returns 3D dissipation rate
					- 'TE01' natively returns the averaged dissipation rate
			- SF method only can handle single array at a time

	- Cleaning code:
		- ADV cleaning functions now return a logical mask to mark bad data
			- `clean_fill()` function takes this mask as input, removes bad data, and interpolates it
		- Added `surface_from_P()` and `correlation_filter()` functions to ADP cleaning functions
		- ADP `fillgaps_time()` and `fillgaps_depth()` and ADV `clean_fill()` use xarray's `na_interpolate()` 
		  to fill in bad data.

	- Time:
		- Removed mpltime support and changed to epoch time (seconds since 1970/1/1 00:00:00)
		- Solved bug where unaware timestamp would convert to different times depending on working computer timezone
			- Instrument time remains in the timezone in which it was logged by the instrument, no matter the timezone 
			  of the user analyzing the data
		- Added code to convert between epoch time <-> datetime <-> datestring, MATLAB datenum conversion functions

	- Testing updates:
		- Added check signature velocity rotations against nortek matfiles
		- Dropped testing for python 2.x because xarray doesn't support it
		- Verified xarray output against h5py-based source code
		- Updated test data to handle changes in source code
		- Testing folders not included in setup.py
		- Increased testing coverage to 90%

	- Updated documentation to build off 'make html' in command prompt


## Version 0.12.1
    - Handle `inst2head_rotmat`, this includes an API change:
      - `body2head_vec` and `body2head_rotmat` have been replaced by
        `inst2head_vec` and `inst2head_rotmat`, respectively.
      - Also you must use `dat.set_inst2head_rotmat` now (don't set it directly as `dat.props['inst2head_rotmat'] = ...`)
      - Stricter handling of `dat.props` (e.g., don't allow `dat.props['coord_sys'] = 'inst'`)

## Version 0.12
	- Handle echo (0x1c) and bottom-track (0x17) Nortek Signature pings
	- Handle corrupted timestamps in Nortek Signature pings (assign NaN)
	- Bugfix for files that have missing pings at the start of the file
	- Handle rotations of angrt and accel for `_bt` and `_b5` pings
	- Add quaternion data from Nortek Signatures with AHRS
	- AD2CP index files include burst version and hw_ensemble counter, include versioning

## Version 0.11.1
	- Remove the keep_orient_raw option, and just put instrument h,p,r into `dat['orient']['raw']`

## Version 0.11.0
	- Use dat.set_declination() to set the declination
	- new defs for heading, pitch, roll (+docs)
		- new order of euler2orient inputs (h,p,r)
		- dropped heading, pitch, roll from data; unless user specifies
		keep_orient_raw=True in `dolfyn.read`, in which case the data is
		stored in orient.raw
	- New definitions/tools for 'principal coordinate system'
		- switched from using principal_angle to principal_heading
		- removed `calc_principal_angle` method
		- added `calc_principal_heading` function
		- principal rotations only from earth
	- ad2cp earth2principal rotations now supported
	- Major improvements to documentation of rotations (Thanks Michelle Fogarty!)

## Version 0.10.1
	- Add the `.shortcuts` property
	- Read userdata.json files for ADPs
	- Account for declination in ADP data processing
	- Add function for calculating orientation matrix of RDI ADPs
	- Support motion-correction of ADV data in non-inst frames

## Version 0.10.0
	- Major reorg
	- Switch to Apache 2.0 License
	- Major documentation overhaul
	- Add more tests

## Version 0.9.0

- Changed the io layer to use pyDictH5 for hdf5 files. This is another
  project of mine. The two data formats are not the same, but -- for
  the time being -- DOLfYN will read the old file formats as well.
- The package is now py3 compatible
- Add continuous integration on Appveyor, Travis-ci, codecov
- Added a universal 'read' function.
- Add capability to read AD2CP files.
- Changed back to a Apache license (CC4.0 isn't quite right for software)

## Version 0.8.2 (January 1, 2018)

- Test reorg. (#17)

    - Move test and data into pkg.
    - Update manifest and todo
    - Switch to pkg_resources
    - Now make this an option in the setup.py file.
    - Move binary-files to example_data folder
    - Fixes for test-reorg rebase

- Fixes to Nortek Signature I/O.


## Version 0.8.1 (June 8, 2017)

- Improve winriver I/O.

## Version 0.8.0 (May 30, 2017)

- Fix declination handling in rotations.
- Read WinRiver files, and add a test.
- Add a test for AWAC file I/O.
- More py3 fixes.
- Add support for Nortek Signature (.ad2cp) files.

## Version 0.7.0 (April 13, 2017)

- Fix 7f79 bug (issue #7)
- Add `<source_name>.userdata.json` files
- Changed to a Creative Commons 4.0 license.

## Version 0.6.0 (January 10, 2017)

- Rename `_u` to `vel`.
- Fix windows read-bug (issue #6)
- More Python 3 fixes.
- Add tests for ADP files.
- Fix inst2earth rotations, and add reverse (earth2inst).

## Version 0.5.0

- Added a test for reading an RDI ADCP file.
- The ADV module is now Python 3 compatible.
- Add motion correction flags to ADV output files.
- Add the changelog!

