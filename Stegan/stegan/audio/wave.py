#from .. import audio

import wave

class WaveFile(object):
    
    def __init__(self, header, data):
        self.header = {}
        self.data = bytearray()
    
    @classmethod
    def fromFile(cls, path):
        with wave.open(path, 'rb') as f:
            header = f.getparams()
            data = f.readFrames(header[3])
            return WaveFile(header, data)
        
    def writeToFile(self, path):
        with wave.open(path, 'wb') as f:
            f.setParams(self.header)
            f.writeFrames(self.data)
            
            
