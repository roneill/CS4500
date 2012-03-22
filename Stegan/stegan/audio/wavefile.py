#from .. import audio

import wave
import struct

class WaveFile(object):
    
    def __init__(self, header, data):
        #print "[WaveFile] New WaveFile"
        print "[WaveFile] Header\n%s" % repr(header)
        print "[WaveFile] len(data) = %s" % len(data)
	print "[WaveFile] len(str(data)) = %s" % len(str(data))
   	#print "[WaveFile] type(data) = %s" % type(self.data)

	samplewidth = header[1]
	nframes = header[3]

        self.header = header
        self.data = bytearray(data)
        self.unpacked = struct.unpack('{n}h'.format(n=samplewidth * nframes), str(data))

	# print "[WaveFile] HEY! header[3] = {header_size}, len(data) = {len_data}".format(
	#		header_size = header[3],
	#		len_data = len(data))

    def frate(self):
	""" Return the sample frequency rate """
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

	for v in self.data:
	    f.writeframes(struct.pack('h', int(v)))
        
        f.close()
