General
=======


Testing
=======

Coverage
- Look at coverage report.

Add tests to confirm that all *scripts* work.


Documentation
=============

Create a 'contributing to DOLfYN' page.
- Email me!
- Create tasks on github 'projects'? or something like [MPL enhacement proposals (MEPs)](https://matplotlib.org/devel/MEP/index.html)?


Packaging
=========

Version++ (1.0?!)

New PyPi entry

Build a conda install


File I/O
========

Support for AWAC waves data (AST)

Support for TRDI Sentinel V ADCP

Fix Nortek burst read hack


Data Processing
===============

- Bad AWAC IMU data reads as 6551.x?
- No pressure data from Vectors or AWACs? Registering as 0 in binary?

Coordinate systems:
- Support for rotating directly from 'inst' to 'principal'

ADV burst mode: need to add checks that turbulence averaging doesn't "cross bursts".

Add check for correct sample-rate in binned (e.g., binned.TimeBinner.check_indata)? Does this check need to be in all methods of TimeBinner that do binning (averaging)? Is there a way to use decorators to do this?
- Occasional TRDI sampling frequency calculation error - calculation depends on a variable that appears haphazardly written by TRDI software (VMDAS)

I've done a first attempt at implementing stress-rotations, but isn't as straightforward as originally anticipated.  This is in the `reorg-add_omat` branch. The big issue is: `orientmat` is bad (`det != 1`) after averaging data from a moving instrument.
    - Do quaternions average better?
    - Obviously there are some issues with doing rotations of some data based on the average orientation, but it still seems like we ought to be able to do it if it's moving slowly, right?
    - Should we enforce no reverse rotations on averaged objects (unless they are fixed, e.g. principal->earth?, or other check for no motion?)?

What if I want 30-minute turbulence averages spaced 15-minutes apart?
  - add `n_pad` option to `TurbBinner.__init__`, or
  - Add capability for `n_fft` > `n_bin`?

What about dropping data from averaging? Is this something we should support? Via negative `n_pad`?

ADCP's:
  - Support for calculating principal heading by ensemble?
  - Support for motion-correcting ADCP data
  - turbulence analysis

