# Building Package

Upgrade packaging tools:

    python -m pip install --upgrade build pip twine

Build:

    python -m build

## Upload to Test-PyPi

Upload to Test-PyPi:

    python3 -m twine upload --repository testpypi dist/dolfyn-*

### Testing

Before uploading to the distribution version of PyPi, it is a best practice to:

1. Build a test virtual environment
2. Install dependencies

        python3 -m pip install numpy>=1.20 scipy>=1.7.0 six>=1.16.0 xarray>=0.18.2 netcdf4>=1.5.7

3. Install from testpypi:

        python3 -m pip install --index-url https://test.pypi.org/simple/ dolfyn

4. Confirm that you can import the package and do a version check(?)
    
## Upload to PyPi

    python3 -m twine upload dist/dolfyn-*


# Building docs

@jmcvey3 can you add some info here?
