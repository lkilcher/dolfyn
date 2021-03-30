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
			- take into consideration instrument type for rotation/reference frames
			- need function that can change dataarray coordinates for "rotatable" variables
			- need ability to save as 'netcdf' - doesn't like curly braces {}
	