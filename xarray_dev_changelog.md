Xarray DOLfYN to MHKiT Changelog
------------------------------------------
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
- when loading TRDI data with bottom-track, every subsequent datafile will contain the 'bt' variables even if the instrument didn't record them

- Update documentation
	- Create sphinx API doctree - done
	- Fill in and update API documentation - done
	- Create and update ADCP and ADV examples - done
	- Update documentation that's already there - done
	- Format docs similarly to MHKiT's - done
	- Add 'About' section - done
	- Fix doctest errors - once xarray update completed
	
- Convert DOLfYN object to xarray DataSet
	- basic conversion file - done
	- create function out of conversion file and incorporate into 'read' function - in progress
			- need function that can change dataarray coordinates for "rotatable" variables - done
				- take into consideration instrument type for rotation/reference frames
				- going to feed this into the rotations code
			- removed 'sys' variables from xarray dataset because it was near impossible to save them
			- removed 'alt' variables because I'm not sure what they are <?>
			- adjusted scaling on ambig_vel vars
			- changed dataset 'keys' so that they're more consistent (including adding underscores)
			- simplified 'config' dictionary in DOLfYN object so that it's easier to read
				- really should just read straight into xarray if I had time
			- need ability to save as 'netcdf' - done
				- noted that it's impossible to save multivariable attributes in xarray
				- transformation matrices are thus saved in the dataset variables list
			
	