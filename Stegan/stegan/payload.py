class Payload(object):
    def __init__(self, payload):
        self.payload = payload
    
    @classmethod
    def fromFile(cls, path):
        with open(path) as f:
            payload = bytearray(f.read())
        
        return Payload(payload)
    
    def writeToFile(self, path):
        pass