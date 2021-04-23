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
	- Create function out of conversion file and incorporate into 'read' function - in progress as bugs show up
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
	- Attempt to read binary files straight into a dataset - done
	
- Refactor DOLfYN
	- started renaming files to x_*.py
		- Rotation code - done, checked
			- 'set_inst2head_rotmat' is located in the Velocity class, everything else is functional
			- Orientation up/down wasn't taken into account for Nortek Signatures?
				- Fixed two Nortek Signature rotation errors - one for upside-down instruments (a simple sign change according to Nortek docs) and one for upside-up instruments (if statement error)
				- Still a (truncation?) 1% error for upside-up Signature velocity data?
			- Verified Nortek Signature data (facing up and down)
			- Verified TRDI Sentinel Workhorse (facing down - VMDAS)
				- should work with those facing up, not verified
				
		- Motion correction code - done, checked
			- motion correction object has been removed
			
		- TimeData, Velocity, TKEdata class refactoring - done
			- TimeData is now void
			- Added Velocity and TKEdata as xarray accessors
				- These will have to feed into the ADV and ADP objects, so they might lose their accessor status and simply inherit into ADPdata and ADVdata
			- Renamed TKEdata class to 'TKE'
			- Dubbed the Velocity class xarray accessor 'Veldata'
			- Dubbed the TKE class xarray accessor 'TKEdata'
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
				- Changed U_mag (horizontal vel) to vel_avg (3D) in all three methods so that they use 'x' to calculate 'Sxx', where x=[1,2,3]
				- Changed 'calc_L_int' to use the 3D velocity as well because 'calc_acov' returns the 3D autocovariance for each velocity term
				- methods can take either the 3D velocity or a single velocity array
					- sanity note: dissipation rates within isotropic cascade for each velocity direction should theoretically be equal (def of isotropic)
					- leaving to user to average 'LT83' returns together if they'd like
					- 'TE01' natively returns the averaged dissipation rate
				- Added 'np.nan-' so the 'epsilon' functions can handle nans

		- Cleaning code - done
			- Need to update with xarray's nan interpolation - done
			- ADCPs - individual cleaning functions
			- ADVs - has masking methods that feed into a fill-in method
			
- Refactor DOLfYN's binary readers - in progress
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
		- Need to move Vector rotation matrices from attributes to variables, and remove a lot of config junk - done
		- Need a bit of code to chop off nan's - done
		
- Debugging:
	- When reading TRDI data with bottom-track, every subsequently-read datafile will contain the 'bt' variables even if the instrument didn't record them - remnant/memory of global variables in the IO code?
	- Occasional TRDI sampling frequency calculation error - calculation depends on a variable that appears haphazardly written by TRDI software (VMDAS)
	- Bad AWAC IMU data reads as 6551.x?
	- *xarray accessor warning due to 'Velocity' and 'TKE' inheritance?
	- !!!*Broke rotation code - bad determinant warning in 'orientmat' at indices {} error- how did Levi chop this data off originally?

- To do:
	- Change mpltime to epoch time or something
	- Optimize I/O code
	- depth of adcp for range for nortek instruments? - not taken into account natively by Nortek
	- Function to calculate 'S(k)'? Already wrote one for the wavenumber
	- Save as mat function - done, working on loading a mat file
	- Add functionality for dual profiling configurations - *Need to incorporate 'alt' and 'ast' variable keys into readers (they're keys for the AD2CP's second profiling configuration)
	- Add functionality for Nortek SigVM .ad2cp files
	
	