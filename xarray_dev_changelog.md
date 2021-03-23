Xarray DOLfYN to MHKiT Changelog
-----------------------------
- Fix Nortek Signature binary file to load burst data - rough hack completed
- Fix loading of VMDAS reprocessed .enx files - done
- Comment out the code that forbids access to data object cause it's aggravating- done
- Update documentation to build off '>>make html' - done
- Set up Travis CI - done
- Fix 'latlon' vs 'lonlat' error in read adp tests - done
- Set Travis CI to run doctests - done
= Fix calc_turbulence __call__ error - done
- Push changes in my fork to an xarray branch on dolfyn
- Start updating documentation
	- Create sphinx API doctree - done
	- change that formatting theme in conf.py file to reflect MHKiT's
	- Fill in and update API documentation - done
	- Create and update ADCP and ADV examples - in progress
	- Update documentation that's already there - in progress
	- Fix doctest errors