#from .. import audio

import wave

class WaveFile(object):
    
    def __init__(self, header, data):
        self.header = {}
        self.data = bytearray()
    
    @classmethod
    def fromFile(cls, path):
        f = wave.open(path, 'rb')
        
        header = f.getparams()
        data = f.readframes(header[3])
        
        f.close()
        
        return WaveFile(header, data)
        
    def writeToFile(self, path):
        with wave.open(path, 'wb') as f:
            f.setParams(self.header)
            f.writeFrames(self.data)
            
            
