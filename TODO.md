General
=======

Talk w/ @jmcvey3
======
- How to document the dolfyn-view data-objects (`<obj>.velds`)? Is building this even a good idea? ... I started this. I need help from @jmcvey3. Espcially I think we need a page that documents the `velocity.Velocity` class. Maybe this gets added to the 'shortcuts' page?
- Add simplify/standardize functions


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

Update conda-forge install


File I/O
========

Support for AWAC waves data (AST)

Support for files containing data from 2 water-track profiling configurations


Data Processing
===============

Coordinate systems:
- Support for rotating directly from 'inst' to 'principal'

Implement Reynolds stress rotations (e.g. rotating u'w'_ from 'inst' to 'principal' coordinates) for ADVs
      This is in the `reorg-add_omat` branch. The big issue is: `orientmat` is bad (`det != 1`) after averaging data from a moving instrument.
    - Do quaternions average better?
    - Obviously there are some issues with doing rotations of some data based on the average orientation, but it still seems like we ought to be able to do it if it's moving slowly, right?
    - Should we enforce no reverse rotations on averaged objects (unless they are fixed, e.g. principal->earth?, or other check for no motion?)?

What if I want 30-minute turbulence averages spaced 15-minutes apart?
  - add `n_pad` option to `ADVBinner.__init__`, or
  - Add capability for `n_fft` > `n_bin`?

What about dropping data from averaging? Is this something we should support? Via negative `n_pad`?

ADCPs:
  - Support for motion-correcting ADCP data
