Documentation
====

Add some examples to the plotting tools page

Add a units section.

Add usage examples for the adp package.

Document the .userdata.json files
    - declination handling

Document rotations (note: beam coordinate system is only variables
that start with 'vel')

Document variables in data objects

Document load vs. mmload (remove mmload!?)

Document generic read function (io.api.read)
    - What types of data files does this function read?

Document changed location of tests.

General Test Updates
-------

Add check for `coord_sys_principal_ref` in `earth2principal` fn's.

Add tests for ADP:

- averaging!

Data Processing
========

Support for 3-beam solutions in rotations for adp's (i.e. in adp.rotate.beam2inst)

ADV burst mode: need to add checks that turbulence averaging doesn't "cross bursts".

What if I want 30-minute turbulence averages spaced 15-minutes apart?
  - add `n_pad` option to `TurbBinner.__init__`, or
  - Add capability for `n_fft` > `n_bin`?

What about dropping data from averaging? Is this something we should support? Via negative `n_pad`?

``adp.base.binner``: support for calculating stresses using Stacey++1999 method.

- Add tools for loading test data?

Binary Reading
---------------

- Average multiple GPGGA strings in a single ensemble (`io.rdi.read_rdi`)

- Fix Signature rotations.

Default to not including test folder (or just data?) in a release.

Testing
======

Add tests to confirm that all scripts work.

Add tests to confirm that matlab file I/O works.

Low Priority
======
Add support for csv files? What do these look like?

File format:
- Or, switch to default to matlab files?
- Best option: write matlab-compatible hdf5 files?!

Build a conda install

Handle units (use Pint?).

Add array-dim labels.

Testing Framework
--------

- More tests for correct sample-rate in data.binned (e.g., data.binned.TimeBinner.check_indata)? Does this check need to be in all methods of TimeBinner that do binning (averaging)? Is there a way to use decorators to do this?
