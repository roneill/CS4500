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