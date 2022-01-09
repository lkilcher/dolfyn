<img src="img/logo.png" width="70"> DOLfYN
=======================
![Build](https://github.com/jmcvey3/dolfyn/actions/workflows/build.yml/badge.svg)
[![Coverage Status](https://coveralls.io/repos/github/jmcvey3/dolfyn/badge.svg?branch=master)](https://coveralls.io/github/jmcvey3/dolfyn?branch=master)
[![Documentation Status](https://readthedocs.org/projects/dolfyn-xarray/badge/?version=latest)](https://dolfyn-xarray.readthedocs.io/en/latest/?badge=latest)

BIG NEWS!!!
------

Hello everyone! Just so that you know, dolfyn 0.13.0 has just been
released (available on PyPi), and it is a MAJOR REFACTOR of the code
so that DOLfYN is now built on xarray, rather than the hokey
`pyDictH5` package that I'd built.

DOLfYN 0.13.0 is _not_ backwards compatible with earlier version. This
means two things:

1. The data files (`.h5` files) you created with earlier versions
of DOLfYN will no longer load with DOLfYN 0.13.0.
2. The syntax of DOLfYN 0.13.0 is completely different from earlier version.

Because of this, it's probably easiest to continue using earlier
versions of DOLfYN for your old data. If you want to bring some data
into DOLfYN 0.13, you will need to
`dolfyn.read(binary_source_file.VEC)`, and then refactor your code to
work properly with DOLfYN's new syntax. I may be providing some
updates to dolfyn 0.12 via the v0.12-backports branch (and associated
releases), but I doubt that will last long.

Very sorry that we didn't communicate the plan for this change, but
the truth is that we simply don't know who our users are. The good
news is that I think in the long run this will make DOLfYN a much more
robust, powerful, and compatible tool -- especially because we now
write/load xarray-formatted netcdf4 files, which is becoming a
standard.

A **HUGE THANK YOU** to @jmcvey3 who did the vast majority of the work
to make this happen.


Summary
------

DOLfYN is the Doppler Oceanography Library for pYthoN.

It is designed to read and work with Acoustic Doppler Velocimeter
(ADV) and Acoustic Doppler Profiler (ADP/ADCP) data. DOLfYN includes
libraries for reading binary Nortek(tm) and Teledyne RDI(tm) data
files.
* Read in binary data files from acoustic Doppler instruments
* Clean data
* Rotate vector data through coordinate systems (i.e. beam - instrument - Earth frames of reference)
* Motion correction for buoy-mounted ADV velocity measurements (via onboard IMU data)
* Bin/ensemble averaging
* Calculate turbulence statistics

Documentation
-------------

For details visit the 
[DOLfYN homepage](https://dolfyn-xarray.readthedocs.io/en/latest/).  

Installation
------------

DOLfYN requires Python 3.6 or later and a number of dependencies. See the 
[install page](https://dolfyn-xarray.readthedocs.io/en/latest/install.html)
for greater details.

License
-------

DOLfYN is copyright through the National Renewable Energy Laboratory, 
Pacific Northwest National Laboratory, and Sandia National Laboratories. 
The software is distributed under the Revised BSD License.
See the [license](LICENSE.txt) for more information.

