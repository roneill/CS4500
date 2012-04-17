#from .. import audio

import wave
import struct

class WaveFile(object):
    
    def __init__(self, header, fileHandle):
        # The container must be less than 80 minutes
        if(header[3] > (header[0] * header[2] * 80 * 60)):
            raise Exception("""ERROR!: The length of the container audio file is
                               greater than 80 minutes, which is not supported.
                               Please choose a shorter audio file.""")    
        self.header = header
        self.fileHandle = fileHandle

    def sampleWidth(self):
        return self.header[1]
        
    def samples(self):
	    return self.header[3]
	
    def channels(self):
    	return self.header[0]
	
    def sampleRate(self):
	    return self.header[2]

    def numChunks(self):
    	return self.samples() / float(self.sampleRate())

    def setHeader(self, header):
        self.header = header
    
    @classmethod
    def fromFile(cls, path):
        f = wave.open(path, 'rb')
        
        header = f.getparams()
        
        return WaveFile(header, f)

    @classmethod
    def emptyFile(cls, path, header):
        f = wave.open(path, "wb")
        f.setparams(header)
        return WaveFile(header, f)

    def getSizeChunk(self):
        chunk = self._nextChunk()
        unpacked_chunk = self._unpackChunk(chunk)

        return unpacked_chunk
    
    def chunks(self):
        chunk = self._nextChunk()
        while chunk:
            yield self._unpackChunk(chunk)
            chunk = self._nextChunk()

    def _nextChunk(self):
        return self.fileHandle.readframes(self.sampleRate() / 2)

    def _unpackChunk(self, chunk):
        chunkSize = len(chunk) / self.channels()
        chunkdata = struct.unpack('{n}h'.format(n=chunkSize), str(chunk))
	return chunkdata

    def unchunkData(self, chunk):
        """Convert the chunks of data back into a byte stream"""
        unchunkedBytes = []

        for byte in chunk:
            if byte > 32767:
                byte = 32767
            elif byte < -32768:
                byte = -32768
            
            unchunkedBytes.append(byte)
    
        return unchunkedBytes
    
    def _packChunk(self, chunk):
        unchunkedBytes = self.unchunkData(chunk)
        packedChunk = ''.join(struct.pack('h', b) for b in unchunkedBytes)

        return packedChunk
        
    def writeChunk(self, chunk):
        packedChunk = self._packChunk(chunk)
        self.fileHandle.writeframes(packedChunk)
        
