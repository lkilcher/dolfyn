# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## Unversioned

## Version 0.12.3
	- Update dependencies so that `pip install dolfyn==0.12` works.
	- Fix read for sig files to read to end of file
	- Add savemat function

## Version 0.12.2
	- Switch from `'lonlat'` to `'latlon'` as the designated entry-name in `dat.props`
	- Bugfix for reading timestamps
	- Bugfix for earth-2-principal rotations

## Version 0.12.1
    - Handle `inst2head_rotmat`, this includes an API change:
      - `body2head_vec` and `body2head_rotmat` have been replaced by
        `inst2head_vec` and `inst2head_rotmat`, respectively.
      - Also you must use `dat.set_inst2head_rotmat` now (don't set it directly as `dat.props['inst2head_rotmat'] = ...`)
      - Stricter handling of `dat.props` (e.g., don't allow `dat.props['coord_sys'] = 'inst'`)

## Version 0.12
	- Handle echo (0x1c) and bottom-track (0x17) Nortek Signature pings
	- Handle corrupted timestamps in Nortek Signature pings (assign NaN)
	- Bugfix for files that have missing pings at the start of the file
	- Handle rotations of angrt and accel for `_bt` and `_b5` pings
	- Add quaternion data from Nortek Signatures with AHRS
	- AD2CP index files include burst version and hw_ensemble counter, include versioning

## Version 0.11.1
	- Remove the keep_orient_raw option, and just put instrument h,p,r into `dat['orient']['raw']`

## Version 0.11.0
	- Use dat.set_declination() to set the declination
	- new defs for heading, pitch, roll (+docs)
		- new order of euler2orient inputs (h,p,r)
		- dropped heading, pitch, roll from data; unless user specifies
		keep_orient_raw=True in `dolfyn.read`, in which case the data is
		stored in orient.raw
	- New definitions/tools for 'principal coordinate system'
		- switched from using principal_angle to principal_heading
		- removed `calc_principal_angle` method
		- added `calc_principal_heading` function
		- principal rotations only from earth
	- ad2cp earth2principal rotations now supported
	- Major improvements to documentation of rotations (Thanks Michelle Fogarty!)

## Version 0.10.1
	- Add the `.shortcuts` property
	- Read userdata.json files for ADPs
	- Account for declination in ADP data processing
	- Add function for calculating orientation matrix of RDI ADPs
	- Support motion-correction of ADV data in non-inst frames

## Version 0.10.0
	- Major reorg
	- Switch to Apache 2.0 License
	- Major documentation overhaul
	- Add more tests

## Version 0.9.0

- Changed the io layer to use pyDictH5 for hdf5 files. This is another
  project of mine. The two data formats are not the same, but -- for
  the time being -- DOLfYN will read the old file formats as well.
- The package is now py3 compatible
- Add continuous integration on Appveyor, Travis-ci, codecov
- Added a universal 'read' function.
- Add capability to read AD2CP files.
- Changed back to a Apache license (CC4.0 isn't quite right for software)

## Version 0.8.2 (January 1, 2018)

- Test reorg. (#17)

    - Move test and data into pkg.
    - Update manifest and todo
    - Switch to pkg_resources
    - Now make this an option in the setup.py file.
    - Move binary-files to example_data folder
    - Fixes for test-reorg rebase

- Fixes to Nortek Signature I/O.


## Version 0.8.1 (June 8, 2017)

- Improve winriver I/O.

## Version 0.8.0 (May 30, 2017)

- Fix declination handling in rotations.
- Read WinRiver files, and add a test.
- Add a test for AWAC file I/O.
- More py3 fixes.
- Add support for Nortek Signature (.ad2cp) files.

## Version 0.7.0 (April 13, 2017)

- Fix 7f79 bug (issue #7)
- Add `<source_name>.userdata.json` files
- Changed to a Creative Commons 4.0 license.

## Version 0.6.0 (January 10, 2017)

- Rename `_u` to `vel`.
- Fix windows read-bug (issue #6)
- More Python 3 fixes.
- Add tests for ADP files.
- Fix inst2earth rotations, and add reverse (earth2inst).

## Version 0.5.0

- Added a test for reading an RDI ADCP file.
- The ADV module is now Python 3 compatible.
- Add motion correction flags to ADV output files.
- Add the changelog!

