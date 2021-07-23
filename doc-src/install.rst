.. _install:

Installation
============

|dlfn| can be installed using pip::

    $ pip install dolfyn

Or, if you would like download the source code locally so that you can modify
it, you can clone the repository::
    
   $ git clone https://github.com/jmcvey3/dolfyn/

And then use pip to install it as an 'editable' package::

	 $ cd dolfyn
     $ pip install -e .
	 
Once installed, to create documentation (you may have to pip install sphinx_rtd_theme)::

	 $ cd dolfyn\doc-src
	 $ make html

If you would like to contribute, please follow the guidelines in the `contributing.md` file.

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
`install pytest
<https://docs.pytest.org/en/6.2.x/getting-started.html>`_,
then open a command prompt and run::

  $ python -m pytest

If any of the tests do not pass, first confirm that you have installed
all of the dependencies correctly, including :ref:`git-lfs
<datafiles>`, then check to see if others are having a similar issue
before creating a :repo:`new one <issues/>`.

.. _dependencies:

Dependencies
------------

|dlfn| was originally built upon the h5py package and has since been refactored
to build off xarray to make use of the netCDF data format. Support is upheld for 
python 3.6 onward.

 - `NumPy <http://www.numpy.org>`_ >=1.17.0
 - `SciPy <http://www.scipy.org>`_. >=1.5.0
 - `xarray <http://xarray.pydata.org/en/stable/>`_ >= 1.17
 - `h5netcdf <https://github.com/h5netcdf/h5netcdf>`_ >= 0.11
