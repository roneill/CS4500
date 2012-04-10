import sys, math
import numpy as np
import struct
import wave

from stegan.payload import Payload
from stegan.audio.wavefile import WaveFile
from stegan.utils.bitarray import BitArray
from stegan.utils.bits import get_bit, set_lsb, flip_lsb, get_lsb

def chunk_data(data, tone_length):
    chunks = []
    
    startIdx = 0
    for i in range(len(data) / tone_length):
        endIdx = startIdx + tone_length
        chunk = data[startIdx:endIdx]
        chunks.append(chunk)
        startIdx = endIdx

    return chunks

def unchunk(chunks):
    unchunked_bytes = []

    for chunk in chunks:
        for byte in chunk:
            if byte > 32767:
                byte = 32767
            elif byte < -32768:
                byte = -32768
                
            unchunked_bytes.append(byte)
    
    return unchunked_bytes

def unpack_data(container):
    tdata = struct.unpack('{n}h'.format(n=container.header[1] *
                                        container.header[3]),
                          str(container.data))

    tdata = np.array(tdata)

    return tdata

def decode_data(sample_rate, chunks):
    fft_chunks = [np.fft.fft(chunk) for chunk in chunks]
    freqs = np.fft.fftfreq(sample_rate)
    payload_bytes = []

    toneIndices = range(15000, 15256)
    
    for i, chunk in enumerate(fft_chunks):
        if i >= 83:
            break

        processed_values = np.abs(chunk)**2
        toneValues = {}
    
        for i, toneIdx in enumerate(toneIndices):
            toneValues[processed_values[toneIdx]] = i
            
        maxTone = max(toneValues)
        payload_bytes.append(toneValues[maxTone])
        
    return payload_bytes

def encode_chunk(chunk, payload_byte, power_value):

    toneIndices = range(15000, 15256)
            
    fft_chunk = np.fft.fft(chunk)
    processed_values = np.abs(chunk)**2
            
    power_values = [processed_values[i] for i in range(15000, 15256)]

    index = toneIndices[payload_byte]
    max_tone = max(power_values)
    fft_chunk[index] = math.sqrt(max_tone) + power_value

    encoded_chunk = np.fft.ifft(fft_chunk)

    return encoded_chunk

def can_decode_byte(encoded_chunk, original_byte, sample_rate):
    """This predicate takes a chunk and determines if the given
       byte can be successfuly decoded from the chunk"""

    payload_bytes = decode_data(sample_rate, [encoded_chunk])
    
    return payload_bytes[0] == original_byte

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
    
def compare_payloads(payload, decoded):    
    bytes_different = 0
    for b1, b2 in zip(payload, decoded):
        if b1 != b2:
            bytes_different += 1.0

    return bytes_different

def encode(payload, container):
    """ Encode a payload inside an audio container using the tone insertion
    algorithm. Returns a Trojan AudioFile with the payload inside it.
    """

    # The container must be less than 80 minutes
    if(container.samples() > (container.channels() * container.sampleRate() * 80 * 60)):
	raise Exception("""ERROR!: The length of the container audio file is greater
                           than 80 minutes, which is not supported. Please choose
                           a shorter audio file.""")    
    
    payload_bytes_length = len(payload.data)
    unpacked_data = unpack_data(container)
    chunks = chunk_data(unpacked_data, 44100)
    paybyte_idx = 0
    encoded_chunks = []

    toneIndices = range(15000, 15256)
    
    for chunk in chunks:
        if paybyte_idx < payload_bytes_length:
            payload_byte = payload.data[paybyte_idx]
            
            fft_chunk = np.fft.fft(chunk)
            processed_values = np.abs(chunk)**2
            
            power_values = [processed_values[i] for i in range(15000, 15256)]

            index = toneIndices[payload_byte]
            power_value = power_values[payload_byte]
            max_power_value = max(power_values)
            lowest_value = find_lowest_power_value(chunk,
                                                   payload_byte,
                                                   max_power_value,
                                                   container.sampleRate()) 
            fft_chunk[index] = math.sqrt(max_power_value) + lowest_value
            
            encoded_chunk = np.fft.ifft(fft_chunk)
            encoded_chunks.append(encoded_chunk)

            paybyte_idx +=1
        else:
            encoded_chunks.append(chunk)

    decoded_payload = decode_data(container.sampleRate(), encoded_chunks)
    payload_delta = compare_payloads(payload.data, decoded_payload)
    percent_difference = ((payload_bytes_length - payload_delta) /
                          payload_bytes_length) * 100.0
    
    if payload_delta == 0:
        print "Payload encoded successfully"
    else:
        print "Warning: encoded file was different from original by %.2f%%" % (100 - percent_difference)
            
    unchunked_bytes = unchunk(encoded_chunks)

    print "Mixed chunks: " + str(paybyte_idx)
    
    thing = ''.join(struct.pack('h', v) for v in unchunked_bytes)
    
    return WaveFile(container.header, thing)

def decode(trojan):
    """ Decode a payload from a trojan AudioFile that has been encoded 
    using the Modify LSB algorithm. Returns a Payload.
    """
    
    tdata = unpack_data(trojan)
    tdata=np.array(tdata)
    chunks = chunk_data(tdata, trojan.sampleRate())
    payload_bytes = decode_data(trojan.sampleRate(), chunks)
        
    return Payload(bytearray(payload_bytes))
