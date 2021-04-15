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
	- Bug (unimportant) - when reading TRDI data with bottom-track, every subsequently read datafile will contain the 'bt' variables even if the instrument didn't record them

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
	- *Need to incorporate 'alt' and 'ast' variable keys into readers (they're keys for the AD2CP's second profiling configuration)
	
- Refactor DOLfYN
	- started renaming files to x_*.py
		- Rotation code - done, checked
			- 'set_inst2head_rotmat' is located in the Velocity class, everything else is functional
			- Orientation up/down not taken into account for Nortek Signatures? - fixed
			- Fixed two Nortek Signature rotation errors - one for upside down instruments (sign change) and one for upside up instruments (if-statement mistake)
				- Still a (truncation?) 1% ish error for upside up signatures
			- Verified with Nortek Signature data (facing up and down)
			- Verified with TRDI Sentinel Workhorse (facing down - VMDAS)
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
			- _xarray accessor warning due to inheritance?_
			
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
				- can't handle nan's without `np.nanmean`, etc

				
		- Cleaning code - in progress
			- need to update with xarray's nan interpolation
			- ADCPs - done, needs checking
			- ADVs - not started, just GN2002
			
- Refactor DOLfYN's binary readers - starting soon
	
	
	