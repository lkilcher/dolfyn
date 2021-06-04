Xarray DOLfYN to MHKiT Changelog
--------------------------------
- Step 'initialization'
	- Create xarray branch on dolfyn - done
	- Fix Nortek Signature binary file to load burst data - rough hack completed
	- Fix loading of VMDAS reprocessed .enx files - done
	- Update documentation to build off 'make html' - done
	- Set up Travis CI - done
	- Fix 'latlon' vs 'lonlat' error in read adp tests - done
	- Fix calc_turbulence '__call__' error - done
	- Organize most relevent aspects of code to run straight from 'import dolfyn as dlfn' and correct import inconsistencies - done
	- Fixed mathmatical error in 'range' calculation (bin 1 dist = blank dist + cell size)
	- Fixed Nortek echosounder 'dB' scaling
	
- Convert DOLfYN object to xarray DataSet
	- Basic conversion file - done
	- Create function out of conversion file and incorporate into 'read' function - done and replaced by refactored I/O
			- Need function that can change dataarray coordinates for "rotatable" variables - done
				- take into consideration instrument type for rotation/reference frames
				- going to feed this into the rotations code
			- Need ability to save as 'netcdf' - done
				- noted that it's impossible to save multivariable attributes in xarray
				- transformation matrices are thus saved in the dataset variables list
			- removed 'sys' variables from xarray dataset because it was near impossible to save them
			- adjusted scaling on ambig_vel vars
			- changed dataset 'keys' so that they're more consistent (including adding underscores)
			- simplified 'config' dictionary in DOLfYN object so that it's easier to read
	
- Refactor DOLfYN
	- started renaming files to x_*.py
		- Rotation code - done
			- `rotate2`, `set_inst2head_rotmat`, `calc_principal_heading`, and `set_declination` now located in 'rotate.base'
			- Orientation wasn't taken into account for Nortek Signatures
				- Solved Nortek Signature rotation issues for fixed up vs down 
				- AHRS orientmat is the transpose of dolfyn's HPR-calculated
			- Verified TRDI, AWAC, and Vector match h5py dolfyn output
				
		- Motion correction code - done, checked
			- motion correction object has been removed
			
		- TimeData, Velocity, TKEdata class refactoring - done
			- TimeData is now void
			- Combined Velocity and TKEdata in Velocity
			- Velocity has xarray accessor 'Veldata'
			- Moved methods (`set_declination`, `set_inst2head_rotmat`) into the 'rotate' module
			- All properties now return xr.DataArrays
			
		- TimeBinner, VelBinner, TurbBinner class refactoring - done
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
				- Changed '.mean()' to 'np.nanmean' so the 'epsilon' functions can handle nans

		- Cleaning code - done
			- Updated with xarray's nativenan interpolation
			- ADCPs - individual cleaning functions
			- ADVs - has masking methods that feed into a fill-in method
			
		- Time - done
			- Changed mpl time to epoch time
			- Added conversion functions
			
		- Refactor binary readers - done
				1. Binary files read into a dictionary of dictionaries using netcdf naming conventions
					- Should be easier to debug
				2. Wrote an xarray dataset constructor that'll build off that dictionary
				3. Using the `_set_coords` subroutine located in `rotate.base` to set orientation coordinates
			- Step 1 completed
				- No pressure data from vectors or awacs?? Registering as 0 in binary?
				- Fixed AWAC temp scaling - Added 0.01 factor
				- Added 0.1 scale factor for Signature magnetometer to return in units of uT
				- Fixed GPS timestamps for TRDI WinRiver and VMDAS data
			- Step 2 & 3 - done
				- Moved Vector rotation matrices from attributes to variables
				- Removed user-nonsensical configuration data
				- Added matlab I/O capabilities
				- Added code to search for nan's in Nortek classic instrument's orientation data - bad determinant warning in 'orientmat' at indices {} error
				- Added code to trim GPS data to its native length - TRDI doesn't save lat/lon interpolated to velocity data timestamps

- Update testing - done
	- Added check signature velocity rotations against nortek matfiles - done
	- Changed true/false attributes to 1/0 - Logical values are auto-dropped when saving netCDF
	- Dropped testing for python 2.x because xarray doesn't support it
	- Updated test data to handle `np.nanmean` changes in source code
	- Verified xarray output against h5py and dropped h5py-based source code from package
	- Testing and h5 folders not included in setup.py


- Notes:
	- Deep copy absolutely everything. <-period <-endstop (Is there a way to disable global variables?)
	- DOLfYN loads data as returned by the instrument or software (generally if velocity in beam no correction has been done, if in earth it has)
	- Occasional TRDI sampling frequency calculation error - calculation depends on a variable that appears haphazardly written by TRDI software (VMDAS)
	- Bad AWAC IMU data reads as 6551.x?
	