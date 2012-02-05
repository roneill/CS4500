from stegan.audio import AudioFile

class WaveFile(AudioFile):
    
    def __init__(self):
        self.headers = {}
        self.data = bytearray()
    
    @classmethod
    def fromFile(cls, path):
        pass
    
    def writeToFile(self, path):
        pass