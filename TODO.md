General
=======

File format:
- Switch to pycoda formatted hdf5 files? --Use git's submodule functionality?
- Or, switch to default to matlab files?
- Best option: write matlab-compatible hdf5 files?!

Add support for csv files? What do these look like?

Support for 3-beam solutions in rotations for adp's (i.e. in adp.rotate.beam2inst)

ADV burst mode: need to add checks that turbulence averaging doesn't "cross bursts".

What if I want 30-minute turbulence averages spaced 15-minutes apart?
  - add `n_pad` option to `TurbBinner.__init__`, or
  - Add capability for `n_fft` > `n_bin`?

What about dropping data from averaging? Is this something we should support? Via negative `n_pad`?!?

Add updated Nortek ``.dep`` files, and document the Vector SW version somewhere.

``adp.base.binner``: support for calculating stresses using Stacey++1999 method.

Move example ``data/RDI_test01.000`` to LFS

- ``*.[0-9][0-9][0-9] filter=lfs diff=lfs merge=lfs -text`` should be added to ``example_data/.gitattributes``

- Move example_data to test folder?

- Move tests to pkg folder?

- Use pkg_resources for data files?

- Add tools for loading test data?

- Add a generalized 'read' function.

- More tests for correct sample-rate in data.binned (e.g., data.binned.TimeBinner.check_indata)? Does this check need to be in all methods of TimeBinner that do binning (averaging)? Is there a way to use decorators to do this?

- Average multiple GPGGA strings in a single ensemble

Testing
======

Add tests for ADP:

- winriver01.PD0
- averaging!
- earth2principal rotation
- AWAC rotations

Add tests to confirm that all scripts work.

Add tests to confirm that matlab file I/O works.

Documentation
====

Add some examples to the plotting tools page

Add usage examples for the adp package.

Document the .userdata.json files
    - declination handling

Document variables in data objects

Document load vs. mmload
