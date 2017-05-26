# The setup script for installing DOLfYN.
# from distutils.core import setup
from setuptools import setup, find_packages
import dolfyn._version as ver
import shutil

# Change this to True if you want to include the tests and test data
# in the distribution.
include_tests = False

try:
    # This deals with a bug where the tests aren't excluded due to not
    # rebuilding the files in this folder.
    shutil.rmtree('dolfyn.egg-info')
except:
    pass


config = dict(
    name='dolfyn',
    version=ver.__version__,
    description='Doppler Ocean Library for pYthoN.',
    author='Levi Kilcher',
    author_email='levi.kilcher@nrel.gov',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        #'Topic :: Scientific/Engineering :: Earth Science',
    ],
    url='http://github.com/lkilcher/dolfyn',
    packages=find_packages(exclude=['*.test']),
    # ['dolfyn', 'dolfyn.adv', 'dolfyn.io', 'dolfyn.data',
    #           'dolfyn.meta', 'dolfyn.tools', 'dolfyn.adp', ],
    package_data={},
    install_requires=['numpy', 'scipy', 'h5py', ],
    provides=['dolfyn', ],
    scripts=['scripts/motcorrect_vector.py', 'scripts/vec2mat.py'],
    # entry_points = {
    #    'console_scripts':
    #    ['motcorrect_vector = dolfyn.adv.scripts:motcorrect_vector',
    #     ],
    #    },
    dependency_links=['https://pypi.python.org/pypi/'],
    # cmdclass =
    # {'install_data':chmod_install_data,'install':chmod_install,},
)


if include_tests:
    config['packages'].append('dolfyn.test')
    config['package_data'].update({'dolfyn.test': ['data/*']},)

setup(**config)
