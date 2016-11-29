from scipy import io as spio
from .base import DataFactory
import copy
try:
    # Python 2
    ucode_type = unicode
except NameError:
    # No unicode builtin in Python 3
    ucode_type = None


class Saver(DataFactory):

    """
    The 'matlab' saver data factory writes :class:`main.Saveable`
    objects to disk. In general, this should not be used in user
    space. Instead, use a data object's
    :meth:`main.Saveable.save_mat` method.

    This utilizes scipy's save_mat routine; see it for options.

    """

    ver = 1.1

    def close(self):
        pass

    def __init__(self, filename, mode='w', format='5',
                 do_compression=True, oned_as='row',):
        self.file_mode = mode
        self.filename = filename
        self.format = format
        self.do_compression = do_compression
        self.oned_as = oned_as

    def _obj2todict(self, obj, groups=None):
        """
        Convert the data in obj to a dictionary suitable for scipy's
        save_mat.
        """
        out = {}
        for nm, dat in obj.iter(groups):
            out[nm] = dat
        out['props'] = dict(copy.deepcopy(obj.props))
        out['props'].pop('doppler_noise', None)
        for nm in list(out['props'].keys()):
            # unicodes key-names are not supported
            if nm.__class__ is ucode_type:
                out['props'][str(nm)] = out['props'].pop(nm)
                nm = str(nm)
            # sets are not supported
            if out['props'][nm].__class__ is set:
                out['props'][nm] = list(out['props'][nm])
        return out

    def write(self, obj, groups=None):
        """
        Write data in `obj` to disk.

        Parameters
        ----------

        obj : :class:`main.Saveable`
          The data object to save

        groups : {string, list, None,}
          A group or list of groups to write to the file. By default
          (None), it writes all groups.

        """
        out = self._obj2todict(obj, groups=groups)
        if hasattr(obj, '_pre_mat_save'):
            obj._pre_mat_save(out)
        spio.savemat(self.filename,
                     out,
                     format=self.format,
                     do_compression=self.do_compression,
                     oned_as=self.oned_as)
