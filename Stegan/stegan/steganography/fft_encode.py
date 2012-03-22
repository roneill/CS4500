import sys, math
import numpy as np
import struct

from stegan.payload import Payload
from stegan.audio.wavefile import WaveFile
from stegan.utils.bitarray import BitArray
from stegan.utils.bits import get_bit, set_lsb, flip_lsb, get_lsb

def tone(freq):
    data_size=40000
    sampling_rate = 44100.0
    amp=3.0
    data=[math.sin(2*math.pi*freq*(x/sampling_rate))
          for x in range(data_size)]
    
    data_bytes = [int(v*amp/2) for v in data]

    crap = struct.pack('h', int(v*amp/2))

    print "*******************"
    
    print data_bytes
    
    return data_bytes

def create_tone_byte_map():
    tone_byte_map = []

    tone1 = tone(100)
    
    for i in range(256):
        tone_byte_map.append(tone1)

    return tone_byte_map

def mix_chunks(c1, c2):
    mixed_chunk = []
    for b1, b2 in zip(c1, c2):
        result = b1 + b2

        if result > 255 or result < 0:
            result = 255

        mixed_chunk.append(result)

    return mixed_chunk

def unchunk(chunks):
    unchunked_bytes = []

    for chunk in chunks:
        for byte in chunk:
            if byte < 0 or byte > 255:
                print "Gotcha" + str(byte)
            unchunked_bytes.append(byte)
    

    return unchunked_bytes

def encode(payload, container):
    """ Encode a payload inside an audio container using the tone insertion
    algorithm. Returns a Trojan AudioFile with the payload inside it.
    """

    print "Got here"
    trojan_audio_data = []
    tone_byte_map = create_tone_byte_map()
    
    payload_bytes_length = len(payload.data)
    payload_spacing = 2 # arbitrary constant for now

    paybyte_idx = 0
    paybyte_space = 0

    payload_spacing_idx = 0

    print "Container file length is: " + str(len(container.data))
    print "Payload data is: " + str(len(payload.data))
    toneidx = 0

    # we need to get a tone array corresponding to a byte
    # we need to add every value of the tone array into
    # with bytes from the container

    # convert the container into chunks

    chunks = []

    startIdx = 0
    tone_length = len(tone_byte_map[0])

    print "Tone length is: " + str(tone_length)
    
    for i in range(len(container.data) / tone_length):
        endIdx = startIdx + tone_length
        chunk = container.data[startIdx:endIdx]
        chunks.append(chunk)
        startIdx = endIdx

    print "There are: " + str(len(chunks)) + " chunks"
        
    encoded_chunks = []
        
    for chunk in chunks:
        if paybyte_idx < payload_bytes_length and payload_spacing_idx == payload_spacing:
            payload_byte = payload.data[paybyte_idx]
            tone_byte_array = tone_byte_map[payload_byte]
             
            encoded_chunks.append(mix_chunks(chunk, tone_byte_array))
            payload_spacing_idx = 0
            paybyte_idx +=1
            #print "mixing chunks"
        else:
            #print "adding original chunk"
            encoded_chunks.append(chunk)
            payload_spacing_idx += 1
            
    unchunked_bytes = unchunk(encoded_chunks)

    return WaveFile(container.header, unchunked_bytes)


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
