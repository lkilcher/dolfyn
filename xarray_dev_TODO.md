Xarray DOLfYN to MHKit
----------------------
1. Update documentation to cover DOLfYN’s full capabilities
		- Format similarly to MHKiT documentation
		- Update old and fill in missing documentation
		- Note which objects/functions are still in developmental state
		- Review entire code and note where objects/functions and their dependencies are located
		
2. Switch base datatype from h5py “Dolfyn dataobject” to Xarray “Dataset”
		- start with xarray_testing2.py (code to convert h5py data object to xarray format)
		- string that code to "dlfn.read()" (loads into h5 data object then converts over to a DataSet)
		- build xarray into IO code if time permits

3. Refactor code to call/pull from xarray “Dataset”
		- Rotation code - update so that all instrument rotations still return the same
		- Create xarray classes equivalent to 'Velocity', 'TKEdata' and 'Velbinner', 'TurbBinner'
		- Update 'clean' and 'motion correction' functions to run off xarray
		- Update this list as necessary
		
		- Testing - compare h5py DOLfYN to xarray DOLfYN output
		- Update documentation from step 2 with xarray referencing – API object/function arguments and keywords shouldn’t change
		
4. Port DOLfYN into MHKit
		- import relevant functions
