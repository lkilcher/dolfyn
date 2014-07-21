from scipy import io as spio
from base import data_factory
import copy

class saver(data_factory):
    ver=1.1

    def close(self):
        pass

    def __init__(self,filename,mode='w',format='5',do_compression=True,oned_as='row',):
        self.file_mode=mode
        self.filename=filename
        self.format=format
        self.do_compression=do_compression
        self.oned_as=oned_as


    def obj2todict(self,obj,groups=None):
        out={}
        for nm,dat in obj.iter(groups):
            out[nm]=dat
        out['props']=dict(copy.deepcopy(obj.props))
        out['props'].pop('doppler_noise',None)
        for nm in out['props'].keys(): # unicodes key-names are not supported
            if nm.__class__ is unicode:
                out['props'][str(nm)]=out['props'].pop(nm)
        return out

    def write(self,obj,groups=None):
        out=self.obj2todict(obj,groups=groups)
        if hasattr(obj,'_pre_mat_save'):
            obj._pre_mat_save(out)
        spio.savemat(self.filename,out,format=self.format,do_compression=self.do_compression,oned_as=self.oned_as)
