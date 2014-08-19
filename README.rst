DOLfYN is the Doppler Oceanography Library for pYthoN.

DOLfYN includes libraries for reading binary Nortek(tm) '.vec' and Teledyne-RDI(tm) '.###' data files.  At this point it is designed to read and work with Acoustic Doppler Velocimeter (ADV) and Acoustic Doppler Profiler (ADP/ADCP) data.  If you have a data file of one of these formats that is not read by DOLfYN, contact the DOLfYN development team.  If you have suggestions of other data-file formats that should be added to DOLfYN, contact the development team.

DOLfYN includes a data abstraction layer that enables saving and loading of data after it has been read from the binary files and processed.

Currently DOLfYN documentation is vary sparse. I will work on updating the documentation to make it more useful to folks. Send me a note if you would find this helpful, it might help me move it up on my list.

Installation
============

To install DOLfYN, simply download the repository from http://github.com/lkilcher/dolfyn . If you have git installed, you may simply do::

  $ git clone http://github.com/lkilcher/dolfyn <your-preferred-download-location>

Then run the setup script. On a POSIX system this might look like::

  $ cd <your-preferred-download-location>
  $ sudo python setup.py install

Dependencies
============

DOLfYN depends on `Python <http://www.python.org>`_ 2.7 (Python 3 is not yet supported), `NumPy <http://www.numpy.org>`_, `h5py <www.h5py.org>`_, and `SciPy <http://www.scipy.org>`_.

License
=======

DOLfYN is distributed under the Apache 2.0 license.  See the LICENSE.txt file for further details.
