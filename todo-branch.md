# NOTE

The idea here is that API functions (such as `rotate2`) can handle (take as input and return the matching dtype) either `xarray.Dataset` or `velocity.Velocity` objects. i.e.:

    dsi = dolfyn.read('some raw file in inst coords')
    vdsi = dsi.velds
    vdse = dolfyn.rotate2(vdsi, 'earth', inplace=False) # an velocity.Velocity is returned (matches input vdsi)
    dse = dolfyn.rotate2(dsi, 'earth', inplace=False) # an xarray.Dataset is returned (matches input dsi)

This seems like a really nice feature, however it is problematic when doing something like this:

    _dse = dsi.velds.rotate2('earth', inplace=False)
    
In this case it is unclear whether `_dse` should be a `Velocity` object or a `Dataset` (currently it's a `Dataset`). The obvious solution to this would be to remove the option for `inplace=False` from the `velocity.Velocity` methods and always do `inplace=True`. However, I think `inplace=False` is sometimes nice. On the other hand, this can easily be accomplished with the *function*.

# TODO

If this goes forward, we still need to:
- document the behavior in the api-docs
- add some tests.
