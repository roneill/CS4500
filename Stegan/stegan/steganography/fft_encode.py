import sys, math
import numpy as np
import struct

from stegan.payload import Payload
from stegan.audio.wavefile import WaveFile

# This value controls the volume of the encoded frequencies into
# the carrier audio file. Decreasing this value improves 
# steganography but decreases reliability in MP3 conversion.
base_power_value = 1200000

# The maximum payload density
# (number of 256 frequency ranges we will encode in)
max_payload_density = 78

# An module level variable to store a list of the
# tone ranges that we will encode in
base = 100
tone_ranges = [[base + (offset * 256) + x for x in range(0, 256)]
               for offset in range(0, max_payload_density)]

# we should use the highest detectable frequencies first
tone_ranges.reverse()

def decode_data(sample_rate, chunk, encoding_depth):
    """Decode a byte from a chunk of data at the given depth"""
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

def decode_data_at_depth(sample_rate, chunk, furthest_depth):
    """Decode bytes from chunks of data up to the given depth"""
    fft_chunk = np.fft.rfft(chunk)
    freqs = np.fft.fftfreq(sample_rate)
    processed_values = np.abs(fft_chunk)**2
    
    payload_bytes = []
    payload_byte = 0

    for encoding_depth in range(0, furthest_depth):
    	# At the current depth, get the range of tones
        # that we will encode in
        toneIndices = tone_ranges[encoding_depth]
    
    	toneValues = {}
    
    	for i, toneIdx in enumerate(toneIndices):
            toneValues[processed_values[toneIdx]] = i
            
    	maxTone = max(toneValues)

        # The frequency with the highest power value should 
        # represent the encoded byte
    	payload_byte = toneValues[maxTone]
        payload_bytes.append(payload_byte)

    return payload_bytes

def test_encode_chunk(chunk, payload_byte, power_boost, encoding_depth):
    """Decodes a chunk in memory to determine if a was
       successfully encoded"""
    fft_chunk = np.fft.rfft(chunk)
    processed_values = np.abs(chunk)**2

    toneIndices = tone_ranges[encoding_depth]
	    
    power_values = [processed_values[i] for i in toneIndices]

    freq_index = toneIndices[payload_byte]
    max_tone = max(power_values)
    fft_chunk[freq_index] = math.sqrt(max_tone) + power_boost

    encoded_chunk = np.fft.irfft(fft_chunk)

    return encoded_chunk

def encode_chunk(chunk, payload_bytes, sample_rate):
    """Encodes payload bytes into a chunk"""
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
    
    return payload_byte == original_byte

def find_lowest_power_value(chunk, payload_byte, minimum_value,
                            sample_rate, encoding_depth):
    """Takes a chunk and a payload byte and attempts to encode at the
       minimum value. Keeps incrementing the minimum value by a factor
       of 1.5 in order to find the lowest value that can be successfully
       decoded."""
 
    encoded_chunk = chunk
    current_value = base_power_value
    min_value = current_value

    while(not can_decode_byte(encoded_chunk, payload_byte,
                              sample_rate, encoding_depth)):
        current_value = min_value
        encoded_chunk = test_encode_chunk(chunk, payload_byte,
                                          current_value, encoding_depth)
        min_value *= 1.5
    
    return current_value

def progress_bar_update(progress):
    sys.stdout.write('\r[{0}] {1}%'.format('#'*(progress), progress))
    sys.stdout.flush()
    
def encode(payload, container, trojan):
    """ Encode a payload inside an audio container using the fft encode.
    Write the trojan file to disk.
    """

    number_of_chunks = container.numChunks()

    # This is the lowest amount of bytes we can store in a each chunk
    # to encode the entire payload within the carrier audio file
    payload_density = int(math.ceil(len(payload) / number_of_chunks))

    print "[encode] len(payload) = %s" % len(payload)
    print "[encode] number_of_chunks = %s" % number_of_chunks
    print "[encode] payload_density = %s" % payload_density
    
    if(payload_density >= max_payload_density):
        raise Exception(
            "Error: Payload is too large! Please choose a smaller one.")
    
    # write payload size to the first chunk
    size_chunk = container.getSizeChunk()
    payload_size_bytes = payload.payloadSize()
    
    encoded_chunk = encode_chunk(size_chunk, payload_size_bytes,
                                 container.sampleRate())
    trojan.writeChunk(encoded_chunk)

    encoded_payload_length = 0

    # write the payload to the file
    for idx, chunk in enumerate(container.chunks()):
        payload_chunk = payload.nextChunk(payload_density)

        if payload_chunk is not None:
            encoded = encode_chunk(chunk, payload_chunk,
                                   container.sampleRate())
            trojan.writeChunk(encoded)
            encoded_payload_length += len(payload_chunk)

            progress_bar_update(encoded_payload_length * 100 / len(payload))
            
        else:
            trojan.writeChunk(chunk)
        
    print "Encoded " + str(encoded_payload_length) + " bytes"

def decode(trojan, payload):
    """ Decode a payload from a trojan AudioFile that has been encoded 
    using the fft encode method.
    """

    payload_len_bytes = bytearray()
    payload_bytes = []

    # get the size of the payload from the trojan
    size_chunk = trojan.getSizeChunk()

    for i in range(4):
        byte = decode_data(trojan.sampleRate(), size_chunk, i)
        payload_len_bytes.append(byte)

    payload_len = struct.unpack("I", str(payload_len_bytes))[0]

    print "Payload length is: " + str(payload_len)

    number_of_chunks = trojan.numChunks()
    payload_density = int(math.ceil(payload_len / number_of_chunks))
    
    for idx, chunk in enumerate(trojan.chunks()):

        if len(payload_bytes) < payload_len:

            # If the remaining number of bytes to decode is less than the
            # density, set the density to that value
    	    if((payload_len - len(payload_bytes)) < payload_density):
                payload_density = payload_len - len(payload_bytes)
                
            chunk_payload_bytes = decode_data_at_depth(trojan.sampleRate(),
                                                       chunk, payload_density)
            payload.writeChunk(chunk_payload_bytes)
            
            payload_bytes += chunk_payload_bytes

            progress_bar_update(len(payload_bytes) * 100 / payload_len)
            
        else:
            break

    print "\nDecoded " + str(len(payload_bytes)) + " bytes"
    
