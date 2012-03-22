import sys, math
import numpy as np

from stegan.payload import Payload
from stegan.audio.wavefile import WaveFile
from stegan.utils.bitarray import BitArray
from stegan.utils.bits import get_bit, set_lsb, flip_lsb, get_lsb

def tone(freq, len, amp=1, rate=44100):
    """ Creates a tone at a given frequency for the given length. """
    t = np.linspace(0, len, len*rate)
    data = np.sin(2 * pi * freq * t) * amp
    return data.astype(np.int16) # two byte integers

def convert16bitTo8bit(x):
    ''' convert 16 bit int x into two 8 bit ints, coarse and fine.

    '''
    c = (x >> 8) & 0xff  # The value of x shifted 8 bits to the right, creating coarse.
    f = x & 0xff  # The remainder of x / 256, creating fine.
    return c, f

def expand16bitsToBytes(bits):
    """ Convert an array of 16 bit signed integers into an array of 8 bit unsigned integers"""
    resultArray = []
    for signedint in bits:
        c,f = convert16bitTo8bit(signedint)
        resultArray.append(c)
        resultArray.append(f)

    return resultArray
        


def encode(payload, container):
    """ Encode a payload inside an audio container using the tone insertion
    algorithm. Returns a Trojan AudioFile with the payload inside it.
    """
    trojan_data = []     # A list of integers that

    payload_size = len(payload)     # number of bytes in payload
    payload_size_in_bits = payload_size * 8
    payload_size_bits = BitArray(payload_size, size=32)

    # generate a tone to place in the file
    insertTone = tone(440,0.1,amp=2)
    tonebytearray = expand16bitsToBytes(insertTone)

    tonelen = len(tonebytearray)

    # Find a spacing width
    payload_spacing = int(math.floor((len(container.data) - 32) / payload_size_in_bits))

    print "[tone_insertion] encode - payload_spacing = %s" % payload_spacing
    print "[tone_insertion] encode - payload_size = %s" % payload_size
    print "[tone_insertion] encode - len(payload.data) = %s" % len(payload.data)

    print "[tone_insertion] encode - len(payload_size_bits) = %s" % len(payload_size_bits)
    print "[tone_insertion] encode - payload_size_bits = %s" % ''.join([str(b) for b in payload_size_bits])
    
    #print "[modify_lsb] bits written"    

    paybit_idx = 0
    paybit_space = 0

    print "Tone Length is: " + str(tonelen)
    print "Container file length is: " + str(len(container.data))
    toneidx = 0
    
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
            if paybit_idx < payload_size_in_bits and paybit_space == payload_spacing:

                payload_bit = get_bit(payload.data, paybit_idx)
                if(payload_bit == 1):
                    mixedByte = tonebytearray[toneidx] + cbyte
                    if(mixedByte > 255):
                        tbyte = 255
                    else:
                        tbyte = mixedByte
                    if(toneidx == (tonelen - 1)):
                        toneidx = 0
                    else:
                        toneidx += 1
                else:
                    tbyte = cbyte
                
                paybit_idx += 1
                paybit_space = 0
            else:
                if(toneidx == (tonelen - 1)):
                    mixedByte = tonebytearray[toneidx] + cbyte
                    if(mixedByte > 255):
                        tbyte = 255
                    else:
                        tbyte = mixedByte
                    toneidx = 0
                elif(toneidx > 0):
                    mixedByte = tonebytearray[toneidx] + cbyte
                    if(mixedByte > 255):
                        tbyte = 255
                    else:
                        tbyte = mixedByte
                    toneidx += 1
                else:
                    tbyte = cbyte
                
            paybit_space += 1    
                
                
        trojan_data.append(tbyte)
    
    return WaveFile(container.header, trojan_data)


def decode(trojan):
    """ Decode a payload from a trojan AudioFile that has been encoded 
    using the Modify LSB algorithm. Returns a Payload.
    """
    payload_data = []
    
    payload_size_bits = []
    payload_size = 0
    
    paybit_stack = []

    payload_spacing = 0
    paybit_space = 0
    
    toneLength = 882

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
            
        # There's no more payload data to be read from the trojan, let's break
        else:
            break

    # Get chunks of the tone size found at each spot as determined by spacing. Then get the fft of them.
    fftChunks = []
    for i in range(1, len(trojan.data) / payload_spacing):
        startIdx = i * payload_spacing
        endIdx = startIdx + toneLength
        wavChunk = trojan.data[startIdx:endIdx]
        fftChunk = np.fft.fft(wavChunk)
        fftChunks.append(fftChunk)

    freqs = np.fft.fftfreq(toneLength)
    sampleRate = trojan.header[2]

    # Find the frequencies for each chunk
    for chunk in fftChunks:
        freqIdx = np.argmax(np.abs(chunk) ** 2)
        print "freqIdx = " + str(freqIdx)
        freq = freqs[freqIdx]
        print "freq = " + str(freq)
        freq_in_hertz = abs(freq * sampleRate)
        print "frequency in hertz is: " + str(freq_in_hertz)
        
    return Payload(bytearray(payload_data))
