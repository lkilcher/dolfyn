.. _units:

Terminology
===========

|dlfn| generally uses the `*MKS* system
<https://en.wikipedia.org/wiki/MKS_system_of_units>`_, with most
angles in degrees.

.. csv-table:: Table 1: The units of common variables found in |dlfn| data objects.
               :header-rows: 1
               :widths: 15, 20, 15, 50
               :file: ./units.csv

Data Shortcuts (Properties)
---------------------------

In addition to the data items listed above, |dlfn| data objects also
contain shortcuts to tools and other variables that can be obtained
from simple operations of its data items. These attributes aren't
listed in the view of the data shown above. Instead, to see the
variables that are available as shortcuts for a particular data
object, take a look at the ``dat.shortcuts`` property (new in |dlfn|
0.10.1).

.. csv-table:: Table 2: Notes on common properties found in |dlfn| data objects.
               :header-rows: 1
               :widths: 15, 20, 85
               :file: ./shortcuts.csv

**Important Note:** The items listed in Table 3 are not stored in the data
object but are provided as attributes (shortcuts) to |dlfn| data objects.

.. _data-props

User Meta-Data (``dat.props``)
------------------------------

The ``props`` data-group of |dlfn| data objects is a place for
user-specified meta-data and |dlfn|-specific implementation data. The
most common variables found here are described in Table 2.

.. |dagger| unicode:: 0x02020 .. the dagger-symbol

.. csv-table:: Table 3: The entries in ``dat.props`` that are used in |dlfn|.
               :header-rows: 1
               :widths: 15, 105
               :file: ./props_info.csv

\*: These entries are set and controlled by |dlfn|, and are not meant
to be modified directly by the user. Attempts to set or change them
directly (e.g., ``dat.props['fs'] = 10``) will raise an error.

\*\*: These entries are set and controlled via
``dat.set_<property name>`` methods. Attempts to set or change
them directly (e.g., ``dat.props['declination'] = 20``) will be
deprecated in future versions of |dlfn|.

|dagger|: These entries are not used or set by |dlfn|, but they are
useful measurement meta-data and are listed here to assist in
standardizing the location and format of this information.

.. _json-userdata

Specify meta-data in a JSON file
--------------------------------

The values in ``dat.props`` can also be set in a json file,
``<data_filename>.userdata.json``, containing a single `json-object
<https://json.org/>`_. For example, the contents of these files should
look something like::

    {"inst2head_rotmat": "identity",
     "inst2head_vec": [-1.0, 0.5, 0.2],
     "motion accel_filtfreq Hz": 0.03,
     "declination": 8.28,
     "latlon": [39.9402, -105.2283]
    }

Prior to reading a binary data file ``my_data.VEC``, you can
create a ``my_data.userdata.json`` file. Then when you do
``dolfyn.read('my_data.VEC')``, |dlfn| will read the contents of
``my_data.userdata.json`` and include that information in the
``dat.props`` attribute of the returned data object. This
feature is provided so that meta-data can live alongside your
binary data files.
