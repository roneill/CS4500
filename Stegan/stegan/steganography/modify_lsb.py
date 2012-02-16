import sys, math

from stegan.payload import Payload
from stegan.audio.wavefile import WaveFile
from stegan.utils.bitarray import BitArray
from stegan.utils.bits import get_bit, set_lsb, flip_lsb, get_lsb


def encode(payload, container):
    """ Encode a payload inside an audio container using the Modify 
    Least Significant Bit (LSB) algorithm. Returns a Trojan AudioFile
    with the payload inside it.
    """
    trojan_data = []     # A list of integers that

    payload_size = len(payload)     # number of bytes in payload
    payload_size_in_bits = payload_size * 8
    payload_size_bits = BitArray(payload_size, size=32)

    # Find a spacing width
    payload_spacing = int(math.floor((len(container.data) - 32) / payload_size_in_bits))

    print "[modify_lsb] encode - payload_spacing = %s" % payload_spacing
    print "[modify_lsb] encode - payload_size = %s" % payload_size

    #print "[modify_lsb] encode - len(payload_size_bits) = %s" % len(payload_size_bits)
    #print "[modify_lsb] encode - payload_size_bits = %s" % ''.join([str(b) for b in payload_size_bits])
    
    #print "[modify_lsb] bits written"    

    paybit_idx = 0
    paybit_space = 0
    
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

        elif 33 <= cidx:
            #paybit_idx = (cidx - 33)
            
            if paybit_idx < payload_size_in_bits and paybit_space == payload_spacing:
                payload_bit = get_bit(payload.data, paybit_idx)

                tbyte = set_lsb(cbyte, payload_bit)

                paybit_idx += 1
                paybit_space = 0
            else:
                tbyte = cbyte
                
            paybit_space += 1    
                
        trojan_data.append(tbyte)
        
    print ""
    
    return WaveFile(container.header, trojan_data)


def decode(trojan):
    """ Decode a payload from a trojan AudioFile that has been encoded 
    using the Modify LSB algorithm. Returns a Payload.
    """
    payload_data = []
    
    payload_size_bits = []
    payload_size = 0
    
    paybit_stack = []

    bits_read = 0

    payload_spacing = 0
    paybit_space = 0
    
    for tidx, tbyte in enumerate(trojan.data):
        
        # First 32 bytes of the trojan will have the file size of the 
        # payload encoded in their lsb. [0, 31]
        if 0 <= tidx <= 31:
            paysize_bit = get_lsb(tbyte)
            payload_size_bits.append(paysize_bit)
            
            #sys.stdout.write("%s" % paysize_bit)
            
        # There is no payload data at trojan byte index 32. Let's compute
        # the integer value of the payload_size here for use later.
        elif tidx == 32:
            payload_size = BitArray.from_bits(payload_size_bits).to_int()

            payload_spacing = int(math.floor((len(trojan.data) - 32) / (payload_size * 8)))

            print "[modify_lsb] Payload spacing is %s" % payload_spacing
            print "[modify_lsb] decode - payload_size = %s" % payload_size
            
            # print "[modify_lsb] decode - payload_size_bits = %s" % \
            #    ''.join([str(b) for b in payload_size_bits])
            #print "[modify_lsb] bits read"
            
        # Trojan bytes [33, n] will have the payload encoded in their lsbs,
        # where n is payload_size * 8, where payload_size is the number of 
        # bytes in payload.

        # this will no longer be bounded by the size of the payload data
        # it will be bounded by the size of the trojan data
        elif 33 <= tidx:

            if paybit_space == payload_spacing:
                payload_bit = get_lsb(tbyte)
                
                paybit_stack.append(payload_bit)
                
                paybit_space = 0
                
            # We've read enough bits to make a byte. DO IT.
            if len(paybit_stack) == 8:
                paybyte = BitArray.from_bits(paybit_stack).to_int()
                payload_data.append(paybyte)
                paybit_stack = []
                
            paybit_space += 1    
                
        # There's no more payload data to be read from the trojan, let's break
        else:
            print "Bits read is %s" % bits_read
            print "Out of %s" % payload_size
            break
        
    # print ""
    
    print "[modify_lsb] len(payload_data) = %s (result)" % len(payload_data)
    
    return Payload(bytearray(payload_data))
