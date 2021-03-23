.. _install:

Download and Install
====================

|dlfn| can be installed using pip::

    $ pip install dolfyn

If you want to download the source code locally so that you can modify
it, you can clone the repository::
    
   $ git clone https://github.com/lkilcher/dolfyn/

And then use pip to install it as an 'editable' package::

     $ cd dolfyn
     $ pip install -e ./
	 
Or install as a standard package::

	 $ cd dolfyn
	 $ python setup.py install

To create documentation::

	 $ cd dolfyn\doc-src
	 $ make html

.. _datafiles:

Data Files and Test Files
-------------------------

|dlfn| has several moderately large (a few MB each) binary data files
included with the repo. These are example data files, and test-data
files used to confirm that the repository is functioning correctly. In
order to keep the size of the source repository minimal, these data
files are actually stored using GitHub's `git-lfs
<git-lfs.github.com>`_ tools.

This means that if you want to be able to load these example data
files, or run the tests, you will need to `install git-lfs
<https://help.github.com/articles/installing-git-large-file-storage/>`_. If
you cloned the repository prior to installing git-lfs, run the command
``git lfs fetch`` after installing git-lfs to pull the files.

.. _testing:

Testing
-------

The |dlfn| developers are slowly building a collection of unit-tests
using the `Nose <http://nose.readthedocs.io/>`_ testing
framework. Currently the unit-tests are all housed in the ``test/``
folder (including the data files). To run the tests, you'll need to
`install Nose
<http://nose.readthedocs.io/en/latest/#installation-and-quick-start>`_,
then open a command prompt and run::

  $ nosetests

If any of the tests do not pass, first confirm that you have installed
all of the dependencies correctly, including :ref:`git-lfs
<datafiles>`, then check to see if others are having a similar issue
before creating a :repo:`new one <issues/>`.


.. _dependencies:

Dependencies
------------

- |dlfn| was developed in `Python 2.7 <https://docs.python.org/2/>`_.
  All of the existing unit tests work in `Python 3.8 <https://docs.python.org/3/>`_,
  but this testing is limited to a subset of the code
  and so there may still be lingering `2 to 3
  <https://docs.python.org/2/howto/pyporting.html>`_ conversion issues.
  If you encounter problems with Python 3 have a look at the
  :repo:`issues <issues/>` page and potentially submit a new one (be
  sure to indicate that you are using Python 3).
- `Numpy <http://www.numpy.org>`_ >=1.6.0
- `h5py <http://www.h5py.org>`_ >=2.10.0
- `SciPy <http://www.scipy.org>`_. >=1.5.0
