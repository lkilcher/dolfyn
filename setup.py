# The setup script for installing DOLfYN.
from distutils.core import setup
import dolfyn._version as ver

setup(name='dolfyn',
      version=ver.__version__,
      description='Doppler Ocean Library for pYthoN.',
      author='Levi Kilcher',
      author_email='levi.kilcher@nrel.gov',
      classifiers = ['Development Status :: 3 - Alpha',
                     'Intended Audience :: Science/Research',
                     'License :: OSI Approved :: Apache Software License',
                     'Natural Language :: English',
                     'Topic :: Scientific/Engineering :: Earth Science',
                     ],
      url='http://github.com/lkilcher/dolfyn',
      #download_url = 'https://github.com/lkilcher/dolfyn/tarball/0.2.beta.2',
      packages=['dolfyn','dolfyn.adv','dolfyn.io','dolfyn.data','dolfyn.meta','dolfyn.tools','dolfyn.adcp',],
      install_requires = ['numpy', 'h5py', 'scipy', 'matplotlib'],
      provides=['dolfyn',],
      scripts=['scripts/motcorrect_vector.py','scripts/vec2mat.py'],
      #cmdclass={'install_data':chmod_install_data,'install':chmod_install,},
      )
