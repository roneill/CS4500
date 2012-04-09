#from .. import audio

import wave

class WaveFile(object):
    
    def __init__(self, header, data):
        self.header = header
        self.data = data
    
    def samples(self):
	return self.header[3]
	
    def channels(self):
	return self.header[0]
	
    def sampleRate(self):
	return self.header[2]

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
