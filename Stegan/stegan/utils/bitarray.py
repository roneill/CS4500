class BitArray(object):
    
    @classmethod
    def from_bits(cls, bits):
        arr = BitArray(0)
        arr.bits = bits
        return arr
    
    def __init__(self, n, size=8):
        """ n must be an integer. """
        self.bits = []

        for idx in range(0, size):
            self.bits.append(n % 2)
            n = n / 2

        self.bits.reverse()
    
    def test_bit(self, offset):
        return self.bits[offset] == 1

    def set_bit(self, offset, val):
        self.bits[offset] == val
    
    def get_bit(self, offset):
        return self.bits[offset]
    
    def get_lsb(self):
        return self.get_bit(-1)
    
    def set_lsb(self, val):
        return self.set_bit(-1, val)
    
    def __str__(self):
        return "0b%s" % ''.join([str(b) for b in self.bits])

    def to_int(self):
        return int(str(self), 2)
    
    def __iter__(self):
        return iter(self.bits)
        
    def __len__(self):
        return len(self.bits)
    
    def __getitem__(self, key):
        return self.get_bit(key)

    def __setitem__(self, key, value):
        return self.set_bit(key, value)
