from stegan.audio.wavefile import WaveFile

def testBit(int_type, offset):
    """Return a non-zero result, 2 ** offset, if the bit at 'offset' is one"""
    mask = 1 << offset
    return(int_type & mask)


def setBit(int_type, offset):
    """Return an integer with the bit at 'offset' set to 1"""
    mask = 1 << offset
    return(int_type | mask)


def clearBit(int_type, offset):
    """Returns an integer with the bit at 'offset' cleared (set to 0)"""
    mask = ~(1 << offset)
    return(int_type & mask)


def toggleBit(int_type, offset):
    """Returns an integer with the bit at 'offset' inverted. 0 -> 1 and 1-> 0"""
    mask = 1 << offset
    return(int_type ^ mask)


def encode(payload, container):
    trojan_data = []     # A list of integers that
    
    for byte in container.data:
        trojan_data.append(byte)
    
    return WaveFile(container.header, trojan_data)


def decode(payload, container):
    pass