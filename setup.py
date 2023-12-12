from setuptools import setup, find_packages
import os
import shutil

# Change this to True if you want to include the tests and test data
# in the distribution.
include_tests = False

try:
    # This deals with a bug where the tests aren't excluded due to not
    # rebuilding the files in this folder.
    shutil.rmtree('dolfyn.egg-info')
except OSError:
    pass

# Get the version info We do this to avoid importing __init__, which
# depends on other packages that may not yet be installed.
base_dir = os.path.abspath(os.path.dirname(__file__))
version = {}
with open(base_dir + "/dolfyn/_version.py") as fp:
    exec(fp.read(), version)


config = dict(
    name='dolfyn',
    version=version['__version__'],
    description='Doppler Ocean Library for pYthoN.',
    author='DOLfYN Developers',
    author_email='james.mcvey@pnnl.gov',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Topic :: Scientific/Engineering',
    ],
    url='http://github.com/lkilcher/dolfyn',
    packages=find_packages(exclude=['dolfyn.tests']),
    package_data={},
    install_requires=['numpy>=1.21',
                      'scipy>=1.7.0',
                      'xarray>=0.19.0',
                      'netCDF4',
                      'bottleneck'],
    provides=['dolfyn'],
    scripts=['scripts/motcorrect_vector.py', 'scripts/binary2mat.py'],
)


if include_tests:
    config['packages'].append('dolfyn.tests')
    config['package_data'].update({'dolfyn.tests': ['data/*']},)

setup(**config)
