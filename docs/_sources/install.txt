.. _install:

Download and Install
====================

|dlfn| can be installed in several different ways depending on your
system.  On Windows I recommend getting PythonXY, because it comes
with a functioning pip installation.

If you are on a system with a working version of Python that includes
pip, you can simply do::

    $ pip install dolfyn

For systems that do not include pip you will need to install the :ref:`dependencies` manually. From that point onward you can download |dlfn| from the repository (:repo:`/`). For example, if git is installed, you can::

   $ git clone https://github.com/lkilcher/dolfyn.git <download_location>

If `<download_location>` is not specified, the repository will be created in the current directory in a new `dolfyn` folder. Once you have downloaded |dlfn|, you may either:

a) install it into your Python packages repository by executing the setup.py script::

     $ cd <download_location>
     $ python setup.py install

b) use it out of `<download_location>`.

For information on how to use |dlfn| consult the :doc:`usage` page.


Dependencies
------------

.. _dependencies

- |dlfn| is known to work with Python 2.7 and `Numpy <http://www.numpy.org>`_ >=1.6.
- |dlfn| requires `h5py <www.h5py.org>`_, and `SciPy <http://www.scipy.org>`_.

