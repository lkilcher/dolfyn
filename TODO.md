Finalize the API
===================

    import dolfyn as dlfn
    dlfn.adv  # for adv-specific funcs
    dlfn.adv.correct_motion  # only in dolfyn.adv for now?
    dlfn.adv.TurbBinner
    dlfn.adp  # for adp-specific funcs
    dlfn.plot  # need to figure out what's in this module
    dlfn.rotate2
    dlfn.VelBinner  # class for doing averaging + turbulence analysis
    dlfn.clean

Otherwise, data objects have the following methods:

    rotate2, save/to_hdf5, __repr__, subset, copy, __iter__, walk
    __getitem__  # dat[<group>.<name>] indexing, etc.
    show  # need to add this!
    
What else is there?! I think I need to forego 'autodoc', and select specific funcs/objects for the API page.


Documentation
====

Create a file I/O page
- Document read function (io.api.read)
  - What types of data files does this function read?
    - add 'timezone' handling to `dat.props`?

Add some examples to the plotting tools page
- add a ``show`` method and document it.

Add usage examples for the adp package.

Create a 'contributing to DOLfYN' page.
- Email me!
- Create tasks on github 'projects'? or something like [MPL enhacement proposals (MEPs)](https://matplotlib.org/devel/MEP/index.html)?
  - I could create a few starter entries from `TODO-later`
- Document need for git-lfs. (Are there other options? Maybe a `get_test_data.py`?)
- Document how to run tests. (switch to `py.test`?)

FIXTHIS
=======

Find all instances of !FIXTHIS! and fix them!

Testing
======

Add tests to confirm that all *scripts* work.

Tests should use API-level functions.
- This means I need to better define the API.

Coverage
- Add `earth2principal` rotation tests for ADPs?
- Add averaging tests for ADP.

Data Processing
========

Coordinate systems:
- Support for rotating directly from 'inst' to 'principal'

ADV burst mode: need to add checks that turbulence averaging doesn't "cross bursts".

Add check for correct sample-rate in data.binned (e.g., data.binned.TimeBinner.check_indata)? Does this check need to be in all methods of TimeBinner that do binning (averaging)? Is there a way to use decorators to do this?

Packaging
===========

Version++ (1.0?!)

New PyPi entry

Build a conda install
