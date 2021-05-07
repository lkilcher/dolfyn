Xarray DOLfYN to MHKiT Changelog
------------------------------------------
- Step 'initialization'
	- Create xarray branch on dolfyn - done
	- Fix Nortek Signature binary file to load burst data - rough hack completed
	- Fix loading of VMDAS reprocessed .enx files - done
	- Comment out the code that forbids access to data object cause it's aggravating- done
	- Update documentation to build off 'make html' - done
	- Set up Travis CI - done
	- Fix 'latlon' vs 'lonlat' error in read adp tests - done
	- Set Travis CI to run doctests - done
	- Fix calc_turbulence '__call__' error - done
	- Organize most relevent aspects of code to run straight from 'import dolfyn as dlfn' and correct import inconsistencies - done
	- Fixed mathmatical error in 'range' calculation (bin 1 dist = blank dist + cell size)
	- Fixed Nortek echosounder 'dB' scaling


- Update documentation
	- Create sphinx API doctree - done
	- Fill in and update API documentation - done
	- Create and update ADCP and ADV examples - done
	- Update documentation that's already there - done
	- Format docs similarly to MHKiT's - done
	- Add 'About' section - done
	- Fix doctest errors - once xarray update completed
	
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
			- removed 'alt' variables for now ...
			- adjusted scaling on ambig_vel vars
			- changed dataset 'keys' so that they're more consistent (including adding underscores)
			- simplified 'config' dictionary in DOLfYN object so that it's easier to read
	
- Refactor DOLfYN
	- started renaming files to x_*.py
		- Rotation code - done, checked
			- 'set_inst2head_rotmat' is located in the Velocity class, everything else is functional
			- Orientation wasn't taken into account for Nortek Signatures
				- Solved Nortek Signature rotation issues for fixed up vs down 
				- Doesn't handle AHRS-equipped instrument rotations well
			- Verified TRDI, AWAC, and Vector match h5py dolfyn output
				
		- Motion correction code - done, checked
			- motion correction object has been removed
			
		- TimeData, Velocity, TKEdata class refactoring - done
			- TimeData is now void
			- Added TKEdata as an xarray accessors named 'Veldata'
			- 'Velocity' remains as is
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
				- Added comments
			- Updated turbulence dissipation functions return correctly for xarray
				- LT83 or TE01 methods can take either the 3D velocity or a single velocity array
				- SF method only can handle single beam at a time
					- sanity note: dissipation rates within isotropic cascade for each velocity direction should theoretically be equal (def of isotropic)
					- leaving to user to average 'LT83' returns together if they'd like
					- 'TE01' natively returns the averaged dissipation rate
				- Added 'np.nan-' so the 'epsilon' functions can handle nans

		- Cleaning code - done
			- Need to update with xarray's nan interpolation - done
			- ADCPs - individual cleaning functions
			- ADVs - has masking methods that feed into a fill-in method
			
- Refactor DOLfYN's binary readers - done
		1. Binary files read into a dictionary of dictionaries using netcdf naming conventions
			- Should be easier to debug
		2. Need to write (adjust the file I previously created) an xarray dataset constructor that'll build off that dictionary
		3. Should be able to use the '_set_coords' subroutine located in `rotate.base` to set orientation coordinates
		- is there a point to keeping a dedicated h5py DOLfYN to xarray DOLfYN conversion file?
	- Step 1 completed
		- No pressure data from vectors or awacs?? Registering as 0 in binary?
		- AWAC temp scaling is way off (?) - Added 0.01 factor
		- Added 0.1 scale factor for Signature magnetometer to return in units of uT
	- Step 2 & 3 - done
		- Moved Vector rotation matrices from attributes to variables
		- Removed user-nonsensical configuration data
		- Added 'save_mat' function
		- Fixed - Broke rotation code - bad determinant warning in 'orientmat' at indices {} error - added rough code to search for nan's

- Update testing - in progress
	- Added check signature velocity rotations against nortek matfiles - done
	- Logical values are auto-dropped when saving netCDF - changed true/false attributes to 1/0
	- Dropped testing for python 2.x because xarray doesn't support it
	- Tests against h5:
		- ADV motion correction is 17.1% off?
		- earth2principal rotations fail because np.nanmean is built into xarray's 'mean' attribute(!) when calculating principal heading vs ndarray.mean(), so that's cool to know.


- TODO:
	- Change mpl time to epoch time
	- Something really funky with Nortek AHRS orientation matrix where 1-5% of rotated values are beyond 1e-3 tolerance (and appear randomly distributed)
	- Fix Nortek Signature burst read hack
	- Error reading Sig VM .ad2cp file echosounder data, only loads first column? - related to burst read hack

	- Add motion-correction for ADCPs
	- depth of adcp for range for nortek instruments? - not taken into account natively by Nortek
	- Function to calculate 'S(k)'? Already wrote one for the wavenumber
	- pseudo-TI function for ADCPs?

- Notes:
	- deep copy absolutely everything. <-period <-endstop (Is there a way to disable global variables?)
	- DOLfYN loads data as returned by the instrument or software (generally if velocity in beam no correction has been done, if in earth it has)
	- Subsequently-read TRDI datafiles will contain variables from previous instrument even if the instrument didn't record them - remnant/memory of global variables in the IO code?
	- Occasional TRDI sampling frequency calculation error - calculation depends on a variable that appears haphazardly written by TRDI software (VMDAS)
	- Bad AWAC IMU data reads as 6551.x?
	
	