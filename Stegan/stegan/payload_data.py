class PayloadData(object):
    def __init__(self):
        self.payload = bytearray()
    
    @classmethod
    def fromFile(cls, path):
        pass
    
    def writeToFile(self, path):
        pass