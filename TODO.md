General
=======

Support for 3-beam solutions in rotations for adp's (i.e. in adp.rotate.beam2inst)

ADV burst mode: need to add checks that turbulence averaging doesn't "cross bursts"".

What if I want 30-minute turbulence averages spaced 15-minutes apart?
  - add `n_pad` option to `TurbBinner.__init__`, or
  - Add capability for `n_fft` > `n_bin`?

What about dropping data from averaging? Is this something we should support? Via negative `n_pad`?!?

Testing
======

Add test to confirm that the adv_example01.py script works.

Add tests to confirm that all scripts work.

Add tests to confirm that matlab file I/O works.

Documentation
====

Move from gh-pages to doc/ folder for documentation.

Document need for git-lfs for testfiles!

Document need for command line tools (xcode) on OSX.

Document need for Python 2?

