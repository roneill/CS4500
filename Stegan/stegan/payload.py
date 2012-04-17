
import os
import struct

class Payload(object):
    def __init__(self, size, filehandle):
        self.size = size
        self.filehandle = filehandle

    @classmethod
    def fromFile(cls, path):
        f = open(path, 'rb')
        size = os.path.getsize(path) 
        
        return Payload(size, f)

    @classmethod
    def openFile(cls, path):
        f = open(path, 'wb')
        size = os.path.getsize(path) 
        
        return Payload(size, f)
            
    def __len__(self):
        """ Return the file size of the payload """
        return self.size

    def payloadSize(self):
        """Returns a bytearray of the bytes representing
           the size of the payload"""
        payloadLength = struct.pack("I", self.size)
        payloadLengthBytes = bytearray(payloadLength)

        return payloadLengthBytes

    def nextChunk(self, size):
        """Gets the next n bytes of the payload file."""
        chunk = self._nextChunk(size)
        chunk_bytes = bytearray(chunk)
        
        if chunk == "":
            return None
        else:
            return chunk_bytes

    def _nextChunk(self, size):
        return self.filehandle.read(size)

    def writeChunk(self, chunk):
        self.filehandle.write(bytearray(chunk))
