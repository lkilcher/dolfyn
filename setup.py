# The setup script for installing DOLfYN.
from numpy.distutils.core import setup,Extension,Command
from numpy.distutils.command.install_data import install_data
from distutils.command.install import install
from distutils import log
import dolfyn._version as ver
import os

class chmod_install_data(install_data):
    """
    This class ensures that data files get installed with
    read permissions.
    """
    def run(self):
        install_data.run(self)
        if os.name in ['posix']:
            for fn in self.get_outputs():
                if not (fn.endswith('.py') or fn.endswith('.pyc')):
                    mode = (( (os.stat(fn).st_mode) | 0o554 ) & 0o7777 )
                    log.info(('changing mode of %s to %o' % (fn, mode)))
                    os.chmod(fn,mode)

class chmod_install(install):
    """
    This class ensures that scripts and extensions get installed with
    read and execute permissions.
    """
    def run(self):
        install.run(self)
        if os.name in ['posix']:
            for fn in self.get_outputs():
                mode = (( (os.stat(fn).st_mode) | 0o555 ) & 0o7777 )
                log.info(('changing mode of %s to %o' % (fn, mode)))
                os.chmod(fn,mode)

setup(name='dolfyn',
      version=ver.__version__,
      description='Doppler Ocean Library for pYthoN.',
      author='Levi Kilcher',
      author_email='levi.kilcher@nrel.gov',
      url='http://github.com/lkilcher/dolfyn',
      download_url = 'https://github.com/lkilcher/dolfyn/tarball/0.2',
      packages=['dolfyn','dolfyn.adv','dolfyn.io','dolfyn.data','dolfyn.meta','dolfyn.tools','dolfyn.adcp',],
      install_requires=['numpy','h5py','scipy','matplotlib'],
      provides=['dolfyn',],
      scripts=['scripts/motcorrect_vector.py','scripts/vec2mat.py'],
      #cmdclass={'install_data':chmod_install_data,'install':chmod_install,},
      )
