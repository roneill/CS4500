class StegStrategy(object):
    """The class from which all Steganographic implementations derive
    """
    
    def encode(self, payload, container):
        """Encode the data in payload into container. Returns an AudioFile 
        containing the steganographic information"""
        raise Exception("Implement me.")
    
    def decode(self, trojan):
        """Decode the data inside a trojan AudioFile into a PayloadData
        """
        raise Exception("Implement me.")
        
class BitModify(StegStrategy):
    pass
    
class SpreadSpectrum(StegStrategy):
    pass