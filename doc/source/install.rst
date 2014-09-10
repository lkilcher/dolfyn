.. _install:

Download and Install
====================

|dlfn| can be installed in several different ways depending on your system.  At the most general level, assuming you have Python and NumPy installed, you should be able to simply download |dlfn| from the repository (http://github.com/lkilcher/dolfyn\ ). For example, if git is installed, you can::

   $ git clone http://github.com/lkilcher/dolfyn <download_location>

If `<download_location>` is not specified, the repository will be created in the current directory in a new `dolfyn` folder. Once you have downloaded |dlfn|, you may either:

a) install it into your Python packages repository by executing the setup.py script::

     $ cd <download_location>
     $ python setup.py install

b) use it out of `<download_location>`.

For information on how to use |dlfn| consult the :doc:`usage` page.

Dependencies
------------

- |dlfn| is known to work with Python 2.7 and numpy 1.6.
- |dlfn| requires `h5py <www.h5py.org>`_, and `SciPy <http://www.scipy.org>`_.

