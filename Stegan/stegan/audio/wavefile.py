#from .. import audio

import wave

class WaveFile(object):
    
    def __init__(self, header, data):
        self.header = header
        self.data = data
    
    @classmethod
    def fromFile(cls, path):
        f = wave.open(path, 'rb')
        
        header = f.getparams()
        data = f.readframes(header[3])
                
        f.close()
        
        return WaveFile(header, data)
        
    def writeToFile(self, path):
        f = wave.open(path, 'wb')
        
        f.setparams(self.header)
        f.writeframes(str(self.data))
        
        f.close()
