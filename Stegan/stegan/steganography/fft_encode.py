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
    
    return data_bytes

def create_tone_byte_map():
    tone_byte_map = []

    tone1 = tone(440)
    
    for i in range(256):
        tone_byte_map.append(tone(500 + 5 * i))

    return tone_byte_map

def mix_chunks(c1, c2):
    mixed_chunk = []
    for b1, b2 in zip(c1, c2):
        result = b1 + b2

        if result > 255 or result < 0:
            result = 255

        mixed_chunk.append(result)

    return mixed_chunk

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
            unchunked_bytes.append(byte)
    
    return unchunked_bytes

def encode(payload, container):
    """ Encode a payload inside an audio container using the tone insertion
    algorithm. Returns a Trojan AudioFile with the payload inside it.
    """
    trojan_audio_data = []
    tone_byte_map = create_tone_byte_map()
    
    payload_bytes_length = len(payload.data)
    payload_spacing = 2
    tone_length = len(tone_byte_map[0])

    chunks = chunk_data(container.data, tone_length)

    paybyte_idx = 0
    payload_spacing_idx = 0
    
    encoded_chunks = []
        
    for chunk in chunks:
        if paybyte_idx < payload_bytes_length and payload_spacing_idx == payload_spacing:
            payload_byte = payload.data[paybyte_idx]
            tone_byte_array = tone_byte_map[payload_byte]
             
            encoded_chunks.append(mix_chunks(chunk, tone_byte_array))
            payload_spacing_idx = 0
            paybyte_idx +=1
        else:
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

    payload_spacing = 2
    paybit_space = 0
    
    toneLength = 882

    chunks = []
    
    tdata = struct.unpack('{n}h'.format(n=trojan.header[1] * trojan.header[3]), str(trojan.data2))
    tdata=np.array(tdata)
    
    startIdx = 0
    for i in range(len(tdata) / 40000):
        endIdx = startIdx + 40000
        chunk = tdata[startIdx:endIdx]
        chunk = np.array(chunk)
        chunks.append(chunk)
        startIdx = endIdx
    
    fft_chunks = []
    
    for chunk in chunks:
        fft_chunk = np.fft.fft(chunk)
        fft_chunks.append(fft_chunk)
        
    freqs = np.fft.fftfreq(40000)
    sampleRate = trojan.header[2]
    
    for chunk in fft_chunks:
        freqIdx = np.argmax(np.abs(chunk)**2)
        print "freqIdx = " + str(freqIdx)
        freq = freqs[freqIdx]
        print "freq = " + str(freq)
        freq_in_hertz = abs(freq * sampleRate)
        print "frequency in hertz is: " + str(freq_in_hertz)
        
    return Payload(bytearray(payload_bytes))
