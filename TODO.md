General
=======

Talk w/ @jmcvey3
======
- Move docs? ... and links to docs in `README.md`
- Add notes for building docs to `distribution_notes.md`
- coveralls links?
- +Maintainer on PyPi
- +Maintainer of docs?


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

Support for TRDI Sentinel V instruments

Find faster solution to Nortek burst read hack

Occasional TRDI sampling frequency calculation error - calculation depends on a variable that can be haphazardly written by TRDI software (VMDAS)


Data Processing
===============

Coordinate systems:
- Support for rotating directly from 'inst' to 'principal'

ADV burst mode: need to add checks that turbulence averaging doesn't "cross bursts".

Implement Reynolds stress rotations (e.g. rotating u'w'_ from 'inst' to 'principal' coordinates)
      This is in the `reorg-add_omat` branch. The big issue is: `orientmat` is bad (`det != 1`) after averaging data from a moving instrument.
    - Do quaternions average better?
    - Obviously there are some issues with doing rotations of some data based on the average orientation, but it still seems like we ought to be able to do it if it's moving slowly, right?
    - Should we enforce no reverse rotations on averaged objects (unless they are fixed, e.g. principal->earth?, or other check for no motion?)?

What if I want 30-minute turbulence averages spaced 15-minutes apart?
  - add `n_pad` option to `ADVBinner.__init__`, or
  - Add capability for `n_fft` > `n_bin`?

What about dropping data from averaging? Is this something we should support? Via negative `n_pad`?

ADCPs:
  - Support for calculating principal heading by ensemble?
  - Support for motion-correcting ADCP data
  - turbulence analysis - requires Reynolds stress rotations
