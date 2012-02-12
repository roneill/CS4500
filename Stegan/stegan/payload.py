class Payload(object):
    def __init__(self, data):
        self.data = data
        
    @classmethod
    def fromFile(cls, path):
        with open(path) as f:
            data = bytearray(f.read())
        
        return Payload(data)
    
    def writeToFile(self, path):
        with open(path, mode="wb") as f:
            f.write(self.data)
    
    def __len__(self):
        """ Return the file size of the payload """
        return len(self.data)