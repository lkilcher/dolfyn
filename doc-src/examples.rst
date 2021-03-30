Example Scripts
...............

ADCP Data
"""""""""

The following example 1) reads in ADCP data, 2) cleans it for
erroneous and missing data, 3) rotate to true North Earth frame,
4) bin data into ensembles.

.. literalinclude:: examples/adcp_example01.py


ADV Data
""""""""

The following shows an example of how to 1) read in ADV data,
2) clean or "despike" the data, 3) rotate the data to the
principal flow axes frame, 4) calculate fundamental turbulence 
statistics.

.. literalinclude:: examples/adv_example01.py
