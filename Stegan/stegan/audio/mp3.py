class MP3File(object):
    LAME_PATH = ""
    
    def __init__(self):
        self.headers = {}
        self.data = bytearray()
    
    @classmethod
    def fromFile(cls, path):
        
        pass
    
    @classmethod
    def _lameOptions(opts):
        return [self.LAME_PATH]
        
    @classmethod
    def runLAME(path):
        lameOptions = self._lameOptions({})
        
        print repr(lameOptions)
        retval = subprocess.call(lameOptions)
        
    def writeToFile(self, path):
        pass