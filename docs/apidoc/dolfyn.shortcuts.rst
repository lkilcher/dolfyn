Data Shortcuts (Properties)
===========================

|dlfn| datasets also contain shortcuts to other variables that can be obtained
from simple operations of its data items. Certain shortcuts require variables
calculated using the :ref:`DOLfYN API <package>`.

.. csv-table:: Notes on common properties found in |dlfn| data objects.
               :header-rows: 1
               :widths: 15, 20, 85
               :file: ../shortcuts.csv

**Important Note:** The items listed in Table 4 are not stored in the dataset
but are provided as attributes (shortcuts) to the dataset itself.
They are accessed through the `xarray accessor 
<http://xarray.pydata.org/en/stable/internals/extending-xarray.html>`_ `velds`.

For example, to return the magnitude of the horizontal velocity::

	>> import dolfyn
	>> dat = dolfyn.read_example('AWAC_test01.wpr')
	
	>> dat.velds.U_mag

	<xarray.DataArray 'vel' (range: 20, time: 9997)>
	array([[1.12594587, 0.82454599, 0.96503734, ..., 3.40359042, 3.34527587,
			3.44412805],
		   [0.86688534, 1.05108722, 1.12899632, ..., 0.72053462, 6.47548786,
			0.49120468],
		   [0.88066635, 0.97954744, 0.63123135, ..., 4.37153751, 2.77540426,
			1.81550287],
		   ...,
		   [1.00013206, 1.21381814, 1.14834231, ..., 5.89236205, 1.44082763,
			2.7157082 ],
		   [0.7759962 , 0.89600228, 1.02900833, ..., 2.39949021, 2.18758737,
			4.41797285],
		   [0.95729835, 1.15594339, 1.15038508, ..., 3.11517746, 3.79158362,
			2.66788512]])
	Coordinates:
	  * range    (range) float32 1.41 2.41 3.4 4.4 5.4 ... 17.36 18.36 19.35 20.35
	  * time     (time) float64 1.34e+09 1.34e+09 1.34e+09 ... 1.34e+09 1.34e+09
	Attributes:
		units:        m/s
		description:  horizontal velocity magnitude