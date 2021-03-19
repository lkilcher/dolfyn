Xarray DOLfYN to MHKit
---------------------------
1. Update documentation to cover DOLfYN’s full capabilities shown in the previous slide
		- Format similarly to MHKiT documentation
		- Add notes which objects/functions are still in developmental state
		- Review entire code and note where objects/functions and their dependencies are located
		
2. Switch base datatype from h5py “Dolfyn dataobject” to Xarray “Dataset”
		- start with xarray_testing2.py (code to convert h5py data object to xarray format)
		- string that code to "dlfn.read()" for now (loads into h5 data object then converts over)
		- build into IO code if time permits

3. Refactor code to call/pull from xarray “Dataset”
		- Start with ADCP code because it's simpler than ADV code
		- Update this list as things become clearer
		
		- Testing - compare h5py DOLfYN to xarray DOLfYN output
		- Update documentation from step 2 with xarray referencing – API object/function arguments and keywords shouldn’t change
		
4. Port DOLfYN into MHKit
		- import relevant functions
