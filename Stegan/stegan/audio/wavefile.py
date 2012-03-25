#from .. import audio

import wave

class WaveFile(object):
    
    def __init__(self, header, data):
        self.header = header
        self.data = data
        self.data2 = data
        
        #print "[WaveFile] New WaveFile"
        print "[WaveFile] Header\n%s" % repr(self.header)
        print "[WaveFile] len(data) = %s" % len(self.data)
        #print "[WaveFile] type(data) = %s" % type(self.data)
    
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
