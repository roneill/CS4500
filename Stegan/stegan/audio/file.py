import os

from stegan.audio.wavefile import WaveFile
from stegan.audio.mp3 import MP3File

class AudioFile(object):
    
    def __init__(self):
        self.headers = {}
        self.data = bytearray()
    
    @classmethod
    def fromFile(cls, path):
        filetype = cls._detectFileType(path)
        
        if fileType == "mp3":
            return MP3File.fromFile(path)
        elif fileType == "wav":
            return WaveFile.fromFile(path)
        else:
            raise Exception("Unsupported fileType '%s'" % fileType)
    
    @classmethod
    def _detectFileType(cls, path):
        return os.path.splitext(path)[1][1:]
    
    def writeToFile(self, path):
        pass