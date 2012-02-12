import sys

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

    payload_size = len(payload)     # number of bytes in payload
    payload_size_in_bits = payload_size * 8
    payload_size_bits = BitArray(payload_size, size=32)

    print "[modify_lsb] encode - payload_size = %s" % payload_size
    print "[modify_lsb] encode - len(payload_size_bits) = %s" % len(payload_size_bits)
    print "[modify_lsb] encode - payload_size_bits = %s" % ''.join([str(b) for b in payload_size_bits])
    
    print "[modify_lsb] bits written"
    
    for cidx, cbyte in enumerate(container.data):

        # First 32 bytes of the trojan will have the file size of the 
        # payload encoded in their lsb. [0, 31]
        if 0 <= cidx <= 31:
            paysize_bit = payload_size_bits[cidx]
            
            #sys.stdout.write("%s" % paysize_bit)
            tbyte = set_lsb(cbyte, paysize_bit)
            
        # Skip writing any trojan data in byte at index 32
        elif cidx == 32:
            tbyte = cbyte
            
        # Trojan bytes [33, n] will have the payload encoded in their lsbs,
        # where n is payload_size * 8.
        elif 33 <= cidx:
            paybit_idx = (cidx - 33)
            
            if paybit_idx < payload_size_in_bits:
                payload_bit = get_bit(payload.data, paybit_idx)
                
                #print "paybit is %s, payload_bit is %s" % (paybit_idx, payload_bit)
                sys.stdout.write("%s" % payload_bit)

                tbyte = set_lsb(cbyte, payload_bit)
            else:
                tbyte = cbyte
            
        trojan_data.append(tbyte)
        
    print ""
    
    return WaveFile(container.header, trojan_data)

def decode(trojan):
    payload_data = []
    
    payload_size_bits = []
    payload_size = 0
    
    paybit_stack = []
    
    for tidx, tbyte in enumerate(trojan.data):
        
        # First 32 bytes of the trojan will have the file size of the 
        # payload encoded in their lsb. [0, 31]
        if 0 <= tidx <= 31:
            paysize_bit = get_lsb(tbyte)
            payload_size_bits.append(paysize_bit)
            
            sys.stdout.write("%s" % paysize_bit)
            
        # There is no payload data at trojan byte index 32. Let's compute
        # the integer value of the payload_size here for use later.
        elif tidx == 32:
            payload_size = BitArray.from_bits(payload_size_bits).to_int()
            
            print "[modify_lsb] decode - payload_size = %s" % payload_size
            print "[modify_lsb] decode - payload_size_bits = %s" % \
                ''.join([str(b) for b in payload_size_bits])
            print "[modify_lsb] bits read"
            
        # Trojan bytes [33, n] will have the payload encoded in their lsbs,
        # where n is payload_size * 8, where payload_size is the number of 
        # bytes in payload.
        elif 33 <= tidx <= (33 + (payload_size * 8)):
            payload_bit = get_lsb(tbyte)

            sys.stdout.write("%s" % payload_bit)            
            paybit_stack.append(payload_bit)
            
            # We've read enough bits to make a byte. DO IT.
            if len(paybit_stack) == 8:
                paybyte = BitArray.from_bits(paybit_stack).to_int()
                payload_data.append(paybyte)
                paybit_stack = []
            
        # There's no more payload data to be read from the trojan, let's break
        else:
            break
        
        
    print ""
    
    print "[modify_lsb] len(payload_data) = %s (result)" % len(payload_data)
    
    return Payload(bytearray(payload_data))