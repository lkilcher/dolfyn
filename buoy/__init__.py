import data_base as db
import numpy as np

class buoy_raw(db.velocity):
    
    @property
    def U(self,):
        if not hasattr(self,'_Ucpmlx'):
            self._Ucmplx=-self.wspd.astype(np.float64)*np.exp(1j*np.pi/180*db.tbx.degN2cartDeg(self.wdir.astype(np.float64)))
        # The minus sign is to change wind direction to the direction the wind is blowing in.
        return self._Ucmplx

    @property
    def u(self,):
        return self.U.real

    @property
    def v(self,):
        return self.U.imag


type_map=db.get_typemap(__name__)
def load(fname,data_groups=None):
    with db.loader(fname,type_map) as ldr:
        return ldr.load(data_groups)

def mmload(fname,data_groups=None):
    with db.loader(fname,type_map) as ldr:
        return ldr.mmload(data_groups)
