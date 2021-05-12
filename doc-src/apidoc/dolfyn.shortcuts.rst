Data Shortcuts (Properties)
===========================

In addition to the data items listed above, |dlfn| data objects also
contain shortcuts to tools and other variables that can be obtained
from simple operations of its data items.

**Important Note:** The items listed in Table 3 are not stored in the data
object but are provided as attributes (shortcuts) to |dlfn| data objects.
They are accessed through the xarray accessor `Veldata`, e.g., to
return the horizontal velocity::

	 >> `ds`.Veldata.U_mag

.. csv-table:: Table 2: Notes on common properties found in |dlfn| data objects.
               :header-rows: 1
               :widths: 15, 20, 85
               :file: ../shortcuts.csv