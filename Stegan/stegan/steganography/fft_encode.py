import sys, math
import numpy as np
import struct
import wave

from stegan.payload import Payload
from stegan.audio.wavefile import WaveFile
from stegan.utils.bitarray import BitArray
from stegan.utils.bits import get_bit, set_lsb, flip_lsb, get_lsb

def decode_data(sample_rate, chunk):
    """Decode bytes from chunks of data"""
    fft_chunk = np.fft.rfft(chunk)
    freqs = np.fft.fftfreq(sample_rate)
    payload_byte = 0

    toneIndices = range(15000, 15256)
    
    processed_values = np.abs(fft_chunk)**2
    toneValues = {}
    
    for i, toneIdx in enumerate(toneIndices):
        toneValues[processed_values[toneIdx]] = i
            
    maxTone = max(toneValues)
    payload_byte = toneValues[maxTone]
        
    return payload_byte

def encode_chunk(chunk, payload_byte, power_value):

    toneIndices = range(15000, 15256)
            
    fft_chunk = np.fft.rfft(chunk)
    processed_values = np.abs(chunk)**2
            
    power_values = [processed_values[i] for i in range(15000, 15256)]

    index = toneIndices[payload_byte]
    max_tone = max(power_values)
    fft_chunk[index] = math.sqrt(max_tone) + power_value

    encoded_chunk = np.fft.irfft(fft_chunk)

    return encoded_chunk

def encode_chunk_for_realz(chunk, payload_byte, sample_rate):
    toneIndices = range(15000, 15256)
    fft_chunk = np.fft.rfft(chunk)
    processed_values = np.abs(chunk)**2
            
    power_values = [processed_values[i] for i in range(15000, 15256)]
    
    index = toneIndices[payload_byte]
    power_value = power_values[payload_byte]
    max_power_value = max(power_values)
    lowest_value = find_lowest_power_value(chunk,
                                           payload_byte,
                                           max_power_value,
                                           sample_rate) 
    fft_chunk[index] = math.sqrt(max_power_value) + lowest_value
    
    encoded_chunk = np.fft.irfft(fft_chunk)

    return encoded_chunk

def can_decode_byte(encoded_chunk, original_byte, sample_rate):
    """This predicate takes a chunk and determines if the given
       byte can be successfuly decoded from the chunk"""

    payload_byte = decode_data(sample_rate, encoded_chunk)
    print "Payload byte: "+ str(payload_byte)
    print "Original byte: " + str(original_byte)
    print "Equal" +  str(payload_byte == original_byte)
    
    return payload_byte == original_byte

def find_lowest_power_value(chunk, payload_byte, minimum_value, sample_rate):
    """Takes a chunk and a payload byte and attempts to encode at the
       minimum value. Keeps incrementing the minimum value by a factor
       of two in order to find the lowest value that can be successfully
       decoded."""

    encoded_chunk = chunk
    current_value = 300000
    min_value = current_value

    while(not can_decode_byte(encoded_chunk, payload_byte, sample_rate)):
        current_value = min_value
        encoded_chunk = encode_chunk(chunk, payload_byte, current_value)
        min_value *= 1.5
    
    return current_value

def encode(payload, container, trojan):
    """ Encode a payload inside an audio container using the tone insertion
    algorithm. Returns a Trojan AudioFile with the payload inside it.
    """
    toneIndices = range(15000, 15256)

    packed_payload_len = struct.pack("H", len(payload))
    packed_payload_len_bytes = bytearray(packed_payload_len)
    
    paybyte_idx = 0
    for idx, chunk in enumerate(container.chunks()):
        chunk_size = len(chunk) / container.sampleWidth()
        
        if chunk_size < container.sampleRate():
            print chunk_size
            trojan.writeChunk(chunk)

        elif idx < 2:
            paylen_byte = packed_payload_len_bytes[idx]
            encoded = encode_chunk_for_realz(chunk, paylen_byte, container.sampleRate())
            trojan.writeChunk(encoded)
            
        elif paybyte_idx < len(payload):
            payload_byte = payload.data[paybyte_idx]
            encoded = encode_chunk_for_realz(chunk, payload_byte, container.sampleRate())
            trojan.writeChunk(encoded)
            paybyte_idx +=1
            
        else:
            trojan.writeChunk(chunk)
            
    print "Mixed chunks: " + str(paybyte_idx)

def decode(trojan):
    """ Decode a payload from a trojan AudioFile that has been encoded 
    using the Modify LSB algorithm. Returns a Payload.
    """

    payload_len = 0

    payload_len_bytes = bytearray()
    payload_bytes = []
    
    for idx, chunk in enumerate(trojan.chunks()):
        print idx
        if idx < 2:
            byte = decode_data(trojan.sampleRate(), chunk)
            payload_len_bytes.append(byte)

            if idx == 1:
                payload_len = struct.unpack("H", str(payload_len_bytes))[0]
                print payload_len
        elif len(payload_bytes) < payload_len:
            payload_byte = decode_data(trojan.sampleRate(), chunk)
            payload_bytes.append(payload_byte)
        else:
            break
        
    return Payload(bytearray(payload_bytes))
