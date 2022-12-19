# Update Package Version

1. Update version number and release date in dolfyn/_version.py
2. Update version number in changelog.md
3. Commit version number changes
4. Create a new version tag and push to repository:

        git tag v#.#.#
        git push origin --tags

# Building Package

Upgrade packaging tools:

    python3 -m pip install --upgrade build pip twine

Remove legacy files from dist/ directory.

    rm dist/dolfyn-*

Build:

    python3 -m build

## Upload to Test-PyPi

Upload to Test-PyPi:

    python3 -m twine upload --repository testpypi dist/dolfyn-*

### Testing

Before uploading to the distribution version of PyPi, it is a best practice to:

1. Build a test virtual environment
2. Install dependencies

        python3 -m pip install -r requirements.txt

3. Install from testpypi:

        python3 -m pip install --index-url https://test.pypi.org/simple/ dolfyn

4. Confirm that you can import the package and do a version check

        pip freeze | findstr dolfyn  # version check
    
## Upload to PyPi

    python3 -m twine upload dist/dolfyn-*


## Upload to Conda

1. Update package version and requirements in meta.yaml
2. Update source url and sha256 from pypi page (https://pypi.org/project/dolfyn/#files)
3. Updated conda, conda-build, and conda-verify

        conda update conda conda-build conda-verify anaconda-client

3. Build conda package:

        conda-build .

4. Note where package is saved locally (~/miniconda3/conda-bld/linux-64/dolfyn-v1.2.0-py39_0.tar.bz2)

4. Test package:

        conda install --use-local dolfyn

5. Upload to anaconda:

        anaconda login
        anaconda upload <package_local_filepath>

# Building docs

Change directories in a command window:

    cd dolfyn/docs
    
To build documentation in html:

    make html
    
To remove all built documentation:

    make clean
