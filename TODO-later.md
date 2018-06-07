Testing
======

Coverage
- Look at coverage report.

Add tests to confirm that matlab file I/O works.

Default to not including test folder (or just data?) in a release.

Data Processing
=============

Support for 3-beam solutions in rotations for adp's (i.e. in adp.rotate.beam2inst)

What if I want 30-minute turbulence averages spaced 15-minutes apart?
  - add `n_pad` option to `TurbBinner.__init__`, or
  - Add capability for `n_fft` > `n_bin`?

What about dropping data from averaging? Is this something we should support? Via negative `n_pad`?

``adp.base.binner``: support for calculating stresses using Stacey++1999 method.

Support for motion-correcting ADP data.


File I/O
======

Add support for csv files? What do these look like?

File format:
- Or, switch to default to matlab files?
- Best option: write matlab-compatible hdf5 files?!
- Create a `load_dolfyn.m` script, that can be used to load the .hdf5 or .mat files?
  - Including time conversion to datenum
  - This could potentially be a slippery slope toward building a Matlab package.

'meta arrays'
- Add array-dim labels.
- Handle units (use Pint?).

Average multiple GPGGA strings in a single ensemble (`io.rdi.read_rdi`)

