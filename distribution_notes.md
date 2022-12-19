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


# Building docs

Change directories in a command window:

    cd dolfyn/docs
    
To build documentation in html:

    make html
    
To remove all built documentation:

    make clean
