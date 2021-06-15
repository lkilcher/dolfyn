# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## Unversioned
	- Xarray refactoring:
	- Rotation code:
		- `rotate2`, `set_inst2head_rotmat`, `calc_principal_heading`, and `set_declination` now located in 'rotate.api'
		- Orientation wasn't taken into account for Nortek Signatures
			- Solved Nortek Signature rotation issues for fixed up vs down 
			- AHRS orientmat is the transpose of dolfyn's HPR-calculated
		- Verified TRDI, AWAC, and Vector match h5py dolfyn output
			
	- Motion correction code:
		- motion correction object has been removed
		
	- TimeData, Velocity, TKEdata class refactoring:
		- TimeData is now void
		- Combined Velocity and TKEdata in Velocity
		- Velocity has xarray accessor 'Veldata'
		- Moved methods (`set_declination`, `set_inst2head_rotmat`) into the 'rotate' module
		- All properties now return xr.DataArrays
		
	- TimeBinner, VelBinner, TurbBinner class refactoring:
		- Ensured calc_vel_csd ran off the standard coherence length n_fft (bin size / 6)
		- fft frequency is now a xarray coordinate rather than its own variable
		- Added "freq_units" option to 'calc_vel_psd' and 'calc_vel_csd' using either frequency in Hz (f) or rad/s (omega)
				- Renamed 'calc_omega' to 'calc_freq' and added the Hz or rad/s option
				- Calling TurbBinner/'calc_turbulence' will automatically still use 'rad/s'
		- Set all non-user functions to internal functions
		- "do" functions take dataset as input, "calc" funtions take velocity dataarray input
		- Added a property to calculate wavenumber k from the psd frequency vector
		- Renamed the "sigma_Uh" variable to "U_std" and added it as a function in 'do_avg'
		- Renamed properties "Ecoh" to 'E_coh' and "Itke" to 'I_tke'
		- Removed 'Itke_thresh' from TurbBinner as it is only used with the I_tke property
		- Coherence and covariance functions
			- Renamed 'cohere' and 'phase_angle' to 'calc_coh' and 'calc_phase_angle'
			- Updated so that one can calculate coherence, auto-/cross-covariance with 1D or 3D velocity arrays
		- Updated turbulence dissipation functions return correctly for xarray
			- LT83 or TE01 methods can take either the 3D velocity or a single velocity array
			- SF method only can handle single beam at a time
				- sanity note: dissipation rates within isotropic cascade for each velocity direction should theoretically be equal (def of isotropic)
				- leaving to user to average 'LT83' returns together if they'd like
				- 'TE01' natively returns the averaged dissipation rate
			- Changed '.mean()' to 'np.nanmean' so functions can handle nans

	- Cleaning code:
		- Updated with xarray's native nan interpolation
		- ADV functions now return a logical mask to mark bad data
		- ADCP function automatically apply the mask
		
	- Time:
		- Removed mpltime support
		- Added epoch - datetime - datestring conversion functions		
		- Changed mpl time to epoch time

	- Refactor binary readers
			1. Binary files read into a dictionary of dictionaries using netcdf naming conventions
			2. Wrote an xarray dataset constructor that'll build off that dictionary
			3. Created the `_set_coords` subroutine located in `rotate.base` to set orientation coordinates
		- Step 1 completed
			- Fixed AWAC temp scaling - Added 0.01 factor
			- adjusted scaling on ambig_vel vars
			- Added 0.1 scale factor for Signature magnetometer to return in units of uT
			- changed dataset 'keys' so that they're more consistent (including adding underscores)
			- Fixed GPS timestamps for TRDI WinRiver and VMDAS data
		- Step 2 & 3 - done
			- Moved Vector rotation matrices from attributes to variables
			- Removed user-nonsensical configuration data
			- Added matlab I/O capabilities
			- Added code to search for nan's in Nortek classic instrument's orientation data - bad determinant warning in 'orientmat' at indices {} error
			- Added code to trim GPS data to its native length - TRDI doesn't save lat/lon interpolated to velocity data timestamps

	- Update testing:
		- Added check signature velocity rotations against nortek matfiles - done
		- Changed true/false attributes to 1/0 - Logical values are auto-dropped when saving netCDF
		- Dropped testing for python 2.x because xarray doesn't support it
		- Updated test data to handle `np.nanmean` changes in source code
		- Verified xarray output against h5py-based source code
		- Testing and h5 folders not included in setup.py

	- Fix Nortek Signature binary file to load burst data - rough hack completed
	- Fix loading of VMDAS reprocessed .enx files
	- Update documentation to build off 'make html'
	- Set up Travis CI
	- Fix calc_turbulence '__call__' error
	- Fixed mathmatical error in 'range' calculation (bin 1 dist = blank dist + cell size)
	- Fixed Nortek echosounder 'dB' scaling
    - Switch from `'lonlat'` to `'latlon'` as the designated entry-name in `dat.props`

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

