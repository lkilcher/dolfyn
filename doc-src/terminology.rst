.. _units:

Metadata
========

Units
-----

|dlfn| generally uses the `*MKS* system
<https://en.wikipedia.org/wiki/MKS_system_of_units>`_. Common variables and units are listed in Table 1:

.. csv-table:: : The units of common variables found in |dlfn| data objects.
               :header-rows: 1
               :widths: 15, 20, 15, 50
               :file: ./units.csv

|dlfn| Attributes
-----------------

The ``attrs`` data-group of xarray Datasets is a place for
user-specified meta-data and |dlfn|-specific implementation data. The
most common variables found here are described in Table 2.

.. |dagger| unicode:: 0x02020 .. the dagger-symbol

.. csv-table:: The entries in ``dat.props`` that are used in |dlfn|.
               :header-rows: 1
               :widths: 15, 105
               :file: ./props_info.csv

\*: These entries are set and controlled by |dlfn|, and are not meant
to be modified directly by the user.

\*\*: These entries are set and controlled via
``dat.set_<property name>`` methods.

|dagger|: These entries are not used or set by |dlfn|, but they are
useful measurement meta-data and are listed here to assist in
standardizing the location and format of this information.

Specify metadata in a JSON file
--------------------------------

The values in ``dat.attrs`` can also be set in a json file,
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
``dat.attrs`` attribute of the returned data object. This
feature is provided so that meta-data can live alongside your
binary data files.
