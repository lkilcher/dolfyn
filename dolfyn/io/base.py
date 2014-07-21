from os.path import expanduser

class data_factory(object):
    """
    A base class for data factory objects.  data_factory objects save or load data from files.
    """
    closefile=True
    def __enter__(self,):
        """
        Allow data_factory objects to use python's 'with' statement.
        """
        return self

    def __exit__(self,type,value,trace):
        """
        Close the file at the end of the with statement.
        """
        if self.closefile:
            self.close()
            if hasattr(self,'_extrafiles'):
                for fl in self._extrafiles:
                    fl.close()
    @property
    def filename(self,):
        return self._filename

    @filename.setter
    def filename(self,filename):
        self._filename=expanduser(filename)

if __name__=='__main__':
    #filename='/home/lkilcher/data/eastriver/advb_10m_6_09.h5'
    filename='/home/lkilcher/data/ttm_dem_june2012/TTM_Vectors/TTM_NRELvector_Jun2012_b5m.h5'
    import adv
    ldr=loader(filename,adv.type_map)
    dat=ldr.load()
    
