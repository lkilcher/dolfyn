add_vectrino branch
=======

Make changes to documentation
======
- Include vectrino as a supported Nortek Instrument in about.rst
- Build the documentation


Change code to allow reading of Vectrino ADV
=======
- Modify io.nortek
- Include vno_data dicts in io.nortek_defs 
- Modify rotate.base


Testing
=======
- Ensure that changes don't break previous tests
- Add vectrino_data01.vno as example_data
- Modify test_read_adv to include that vectrino test
- Make vectrino_data01.nc for testing data
- Ensure that new tests don't break
