import sys, math
import numpy as np
import struct
import wave

from stegan.payload import Payload
from stegan.audio.wavefile import WaveFile
from stegan.utils.bitarray import BitArray
from stegan.utils.bits import get_bit, set_lsb, flip_lsb, get_lsb

# The maximum payload density (number of 256 frequency ranges we will encode in)
max_payload_density = 15

# An module level variable to store a list of the tone ranges that we will encode in
base = 15000
tone_ranges = [[base + (offset * 256) + x for x in range(0, 256)] for offset in range(0, max_payload_density)]


def decode_data(sample_rate, chunk, encoding_depth):
    """Decode a byte from a chunk of data"""
    fft_chunk = np.fft.rfft(chunk)
    freqs = np.fft.fftfreq(sample_rate)
    payload_byte = 0

    toneIndices = tone_ranges[encoding_depth]
    
    processed_values = np.abs(fft_chunk)**2
    toneValues = {}
    
    for i, toneIdx in enumerate(toneIndices):
        toneValues[processed_values[toneIdx]] = i
            
    maxTone = max(toneValues)
    payload_byte = toneValues[maxTone]
        
    return payload_byte

def decode_data_deep(sample_rate, chunk, furthest_depth):
    """Decode bytes from chunks of data"""
    fft_chunk = np.fft.rfft(chunk)
    freqs = np.fft.fftfreq(sample_rate)
    processed_values = np.abs(fft_chunk)**2

    payload_bytes = []
    payload_byte = 0

    for encoding_depth in range(0, furthest_depth):
    	toneIndices = tone_ranges[encoding_depth]
    
    	toneValues = {}
    
    	for i, toneIdx in enumerate(toneIndices):
        	toneValues[processed_values[toneIdx]] = i
            
    	maxTone = max(toneValues)
    	payload_byte = toneValues[maxTone]
        payload_bytes.append(payload_byte)

    return payload_bytes

def encode_chunk(chunk, payload_byte, power_value, encoding_depth):
    
    fft_chunk = np.fft.rfft(chunk)
    processed_values = np.abs(chunk)**2

    toneIndices = tone_ranges[encoding_depth]
	    
    power_values = [processed_values[i] for i in toneIndices]

    index = toneIndices[payload_byte]
    max_tone = max(power_values)
    fft_chunk[index] = math.sqrt(max_tone) + power_value

    encoded_chunk = np.fft.irfft(fft_chunk)

    return encoded_chunk

def encode_chunk_for_realz(chunk, payload_bytes, sample_rate):
    fft_chunk = np.fft.rfft(chunk)
    processed_values = np.abs(chunk)**2

    for payload_byte_index,payload_byte in enumerate(payload_bytes):

    	toneIndices = tone_ranges[payload_byte_index]
	    
    	power_values = [processed_values[i] for i in toneIndices]
    
    	index = toneIndices[payload_byte]
    	power_value = power_values[payload_byte]
    	max_power_value = max(power_values)
    	lowest_value = find_lowest_power_value(chunk,
                                               payload_byte,
                                               max_power_value,
                                               sample_rate,
					       payload_byte_index)
    	fft_chunk[index] = math.sqrt(max_power_value) + lowest_value
    
    encoded_chunk = np.fft.irfft(fft_chunk)

    return encoded_chunk

def can_decode_byte(encoded_chunk, original_byte, sample_rate, encoding_depth):
    """This predicate takes a chunk and determines if the given
       byte can be successfuly decoded from the chunk"""

    payload_byte = decode_data(sample_rate, encoded_chunk, encoding_depth)
    
    #print "Payload byte: "+ str(payload_byte)
    #print "Original byte: " + str(original_byte)
    #print "Equal" +  str(payload_byte == original_byte)
    print "{original} -> {payload}  ({equal})".format(
                original=str(original_byte),
                payload=str(payload_byte),
                equal=str(payload_byte == original_byte)
            )
    
    return payload_byte == original_byte

def find_lowest_power_value(chunk, payload_byte, minimum_value, sample_rate, encoding_depth):
    """Takes a chunk and a payload byte and attempts to encode at the
       minimum value. Keeps incrementing the minimum value by a factor
       of two in order to find the lowest value that can be successfully
       decoded."""

    encoded_chunk = chunk
    current_value = 600000
    min_value = current_value

    while(not can_decode_byte(encoded_chunk, payload_byte, sample_rate, encoding_depth)):
        current_value = min_value
        encoded_chunk = encode_chunk(chunk, payload_byte, current_value, encoding_depth)
        min_value *= 1.5
    
    return current_value

def encode(payload, container, trojan):
    """ Encode a payload inside an audio container using the tone insertion
    algorithm. Returns a Trojan AudioFile with the payload inside it.
    """

    number_of_chunks = container.numChunks()

    # Find the lowest required density of the payload, rounded up since if it is larger than the maximum payload density it cannot all be encoded
    payload_density = int(math.ceil(len(payload) / number_of_chunks))

    print "[encode] len(payload) = %s" % len(payload)
    print "[encode] number_of_chunks = %s" % number_of_chunks
    print "[encode] payload_density = %s" % payload_density
    print "[encode] max_payload_density = %s" 

    if(payload_density >= max_payload_density):
        raise Exception("Error: Payload is too large! Please choose a smaller one.")

    packed_payload_len = struct.pack("H", len(payload))
    packed_payload_len_bytes = bytearray(packed_payload_len)
    
    paybyte_idx = 0
    for idx, chunk in enumerate(container.chunks()):
        chunk_size = len(chunk) / container.sampleWidth()
        
        if chunk_size < container.sampleRate():
            print "[encode] chunk_size = %s, sampleRate = %s" % (chunk_size, container.sampleRate())
            trojan.writeChunk(chunk)

        elif idx < 2:
            print "[encode] writing payload length"
            paylen_byte = packed_payload_len_bytes[idx]
            encoded = encode_chunk_for_realz(chunk, [paylen_byte], container.sampleRate())
            trojan.writeChunk(encoded)
            
        elif paybyte_idx < len(payload):
            payload_bytes = payload.data[paybyte_idx:(paybyte_idx + payload_density)]

            print "[encode] (%s / %s) payload_bytes = %s" % (paybyte_idx, len(payload), payload_bytes)
            encoded = encode_chunk_for_realz(chunk, payload_bytes, container.sampleRate())
            trojan.writeChunk(encoded)
            paybyte_idx += payload_density
            
        else:
            print "[encode] writing unencoded chunk"
            trojan.writeChunk(chunk)
            
    print "[encode] Encoded " + str(paybyte_idx - payload_density) + " bytes of payload data."

def decode(trojan):
    """ Decode a payload from a trojan AudioFile that has been encoded 
    using the Modify LSB algorithm. Returns a Payload.
    """

    payload_len = 0

    payload_len_bytes = bytearray()
    payload_bytes = []
    
    for idx, chunk in enumerate(trojan.chunks()):
        # print idx

        if idx < 2:
            byte = decode_data(trojan.sampleRate(), chunk, 0)
            payload_len_bytes.append(byte)

            if idx == 1:
                payload_len = struct.unpack("H", str(payload_len_bytes))[0]

                number_of_chunks = trojan.numChunks()

    		    # Calculate the payload density
                payload_density = int(math.ceil(payload_len / number_of_chunks))

                print "[decode] payload_len = %s" % payload_len
                print "[decode] number_of_chunks = %s" % number_of_chunks
                print "[decode] payload_density = %s" % payload_density

        elif len(payload_bytes) < payload_len:

	        # If the remaining number of bytes to decode is less than the density, set the density to that value
    	    if((payload_len - len(payload_bytes)) < payload_density):
                print "Less bytes left than the density"
                payload_density = payload_len - len(payload_bytes)

            # print "Payload length is: " + str(payload_len) + "Current bytes length is: " + str(len(payload_bytes))
            chunk_payload_bytes = decode_data_deep(trojan.sampleRate(), chunk, payload_density)
            payload_bytes += chunk_payload_bytes

            print "[decode] Found bytes '%s'. len(payload_bytes) = %s, payload_len = %s" % (
                    chunk_payload_bytes, len(payload_bytes), payload_len)                    

        else:
            break
    
    return Payload(bytearray(payload_bytes))
