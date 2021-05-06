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

3. Refactor code to call/pull from xarray “Dataset”
		- Starting with keeping originals and using copies to edit (named 'x_*.py')
		- Rotation code - update so that all instrument rotations still return the same
		- Update 'motion correction' functions to run off xarray
		- Update '*data' classes - add 'Velocity' and 'TKEdata' as xarray accessors
		- Update 'binner' classes
		- Update 'clean' functions
		- Rewrite I/O code to read binary data into xarray datasets
		- Testing 
			- compare h5py DOLfYN to xarray DOLfYN output
			- compare xarray dolfyn to matlab output
		- Change 'time' basetype
		- Update documentation from step 2 with xarray referencing – API object/function arguments and keywords shouldn’t change
		
4. Port DOLfYN into MHKit
		- import relevant functions
