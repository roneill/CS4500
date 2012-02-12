from stegan.payload import Payload
from stegan.audio.wavefile import WaveFile

def testBit(int_type, offset):
    """Return a non-zero result, 2 ** offset, if the bit at 'offset' is one"""
    mask = 1 << offset
    return(int_type & mask)

def set_bit(int_type, offset):
    """Return an integer with the bit at 'offset' set to 1"""
    mask = 1 << offset
    return(int_type | mask)

def clear_bit(int_type, offset):
    """Returns an integer with the bit at 'offset' cleared (set to 0)"""
    mask = ~(1 << offset)
    return(int_type & mask)

def toggle_bit(int_type, offset):
    """Returns an integer with the bit at 'offset' inverted. 0 -> 1 and 1-> 0"""
    mask = 1 << offset
    return(int_type ^ mask)

class BitArray(object):
    
    def __init__(self, bytes):
        """ byte must be an int 0 <= byte <= 256 """
        self.bits = [int(b) for b in bin(bytes)[2:]]
        
        if len(self.bits) < 8:
            self.bits = [0 for x in range(0, 8 - len(self.bits))] + self.bits
    
    def test_bit(self, offset):
        return self.bits[offset] == 1

    def set_bit(self, offset, val):
        self.bits[offset] == val
    
    def get_bit(self, offset):
        return self.bits[offset]
    
    def __str__(self):
        return "0b%s" % ''.join([str(b) for b in self.bits])

    def to_byte(self):
        return int(str(self), 2)
    
    def __iter__(self):
        return iter(self.bits)


def integer_to_bits(n):
    bits = []
    
    for idx in range(0, 31):
        bits.append(n % 2)
        n = n / 2
    
    bits.reverse()
    return bits
    
def bits_to_integer(bits):
    bitstr = "0b" + ''.join([str(b) for b in bits])
    return int(bitstr, 2)

def get_bit(bytearr, offset):
    """ Returns the bit at offset into a bytearray """
    byte_idx = offset / 8
    bit_idx = offset - (byte_idx * 8)
    byte = bytearr[byte_idx]
    bits = BitArray(byte)
    
    return bits.get_bit(bit_idx)

def set_lsb(byte, bit):
    if byte % 2 != bit:
        return flip_lsb(byte)
    else:
        return byte
        
def flip_lsb(byte):
    if byte % 2 == 0:
        return byte + 1
    else:
        return byte - 1

def get_lsb(byte):
    return (byte % 2)

def encode(payload, container):
    trojan_data = []     # A list of integers that

    payload_size = len(payload)
    payload_size_bits = integer_to_bits(payload_size)

    print "[modify_lsb] encode - payload_size = %s" % payload_size
    print "[modify_lsb] encode - len(payload_size_bits) = %s" % len(payload_size_bits)
    print "[modify_lsb] encode - payload_size_bits = %s" % ''.join([str(b) for b in payload_size_bits])
    
    for cidx, cbyte in enumerate(container.data):

        # First 32 bytes of the trojan will contain the file size of 
        # the payload.
        if cidx < 31:
            cbyte = set_lsb(cbyte, payload_size_bits[cidx])
            
        trojan_data.append(cbyte)

    return WaveFile(container.header, trojan_data)

def decode(trojan):
    payload_data = []
    
    payload_size_bits = []
    payload_size = 0
    
    for tidx, tbyte in enumerate(trojan.data):
        
        if tidx < 31:
            payload_size_bits.append(get_lsb(tbyte))
        elif tidx == 31:
            payload_size = bits_to_integer(payload_size_bits)
            print "[modify_lsb] decode - payload_size = %s" % payload_size
            print "[modify_lsb] encode - payload_size_bits = %s" % ''.join([str(b) for b in payload_size_bits])
    
    
    return Payload(bytearray(payload_data))