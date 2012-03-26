import sys, math
import numpy as np
import struct
import wave

from stegan.payload import Payload
from stegan.audio.wavefile import WaveFile
from stegan.utils.bitarray import BitArray
from stegan.utils.bits import get_bit, set_lsb, flip_lsb, get_lsb

def tone(freq):
    data_size=1500
    sampling_rate = 44100.0
    amp=60000.0
    
    data=[math.sin(2*math.pi*freq*(x/sampling_rate))
          for x in range(data_size)]

    amps = []

    fadeIn = .2 * data_size
    fadeOut = .8 * data_size
    
    for i in range(data_size):
        if i <= fadeIn:
            amps.append(amp * (i / fadeIn))
        elif i > fadeIn and i <= fadeOut:
            amps.append(amp)
        else:
            
            amps.append(amp * ((data_size - i) / (data_size - fadeOut)))

    data_bytes = []
        
    for v, a in zip(data, amps):
        b = int(v*a/2)
        data_bytes.append(b)
    
    return data_bytes

def create_tone_bit_map():
    tone_bit_map = []

    one = tone(60)
    zero = tone(15)
    
    tone_bit_map.append(one)
    tone_bit_map.append(zero)

    return tone_bit_map

def create_tone_byte_map():
    tone_byte_map = []

    tone1 = tone(550)
    tone2 = tone(20)
    
    for i in range(256):
        tone_byte_map.append(tone2)
        

    return tone_byte_map

def mix_chunks(c1, c2):
    mixed_chunk = []
    for b1, b2 in zip(c1, c2):
        result = b1 + b2

        if result > 32767:
            result = 32767
        elif result < -32768:
            result = -32768

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

def test_chunk_data():
    data = [1,2,3,4,5,6,7,8, 9]
    chunks = [[1,2], [3,4], [5, 6], [7,8]]

    print chunk_data(data, 2)
    
    return chunk_data(data, 2) == chunks

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

    if not test_chunk_data():
        print "CHUNK DATA FAILED"
    
    trojan_audio_data = []
    tone_byte_map = create_tone_byte_map()

    tone_bit_map = create_tone_bit_map()
    
    payload_data = [get_bit(payload.data, i) for i in range(len(payload.data) * 8)]
    
    payload_bytes_length = len(payload.data)
    payload_bits_length = len(payload_data)
    payload_spacing = 2
    tone_length = len(tone_byte_map[0])

    tdata = struct.unpack('{n}h'.format(n=container.header[1] *
                                        container.header[3]),
                          str(container.data2))
    print "Size of audio data: " + str(container.header[1] * container.header[3])
    
    print "Length of data" + str(len(str(container.data2)))
    
    tdata=np.array(tdata)
    
    chunks = chunk_data(tdata, tone_length)
    
    paybyte_idx = 0
    paybit_idx = 0
    payload_spacing_idx = 0
    
    encoded_chunks = []

    print str(len(chunks))

    for chunk in chunks:
        if paybit_idx < payload_bits_length: # and payload_spacing_idx == payload_spacing:
            payload_bit = payload_data[paybit_idx]
            tone_byte_array = tone_bit_map[payload_bit]
             
            encoded_chunks.append(mix_chunks(chunk, tone_byte_array))
            payload_spacing_idx = 0
            paybit_idx +=1
        else:
            encoded_chunks.append(chunk)
            payload_spacing_idx += 1

    """
    for chunk in chunks:
        if paybyte_idx < payload_bytes_length: # and payload_spacing_idx == payload_spacing:
            payload_byte = payload.data[paybyte_idx]
            tone_byte_array = tone_byte_map[payload_byte]
             
            encoded_chunks.append(mix_chunks(chunk, tone_byte_array))
            payload_spacing_idx = 0
            paybyte_idx +=1
        else:
            encoded_chunks.append(chunk)
            payload_spacing_idx += 1
            """
            
    #**************************************************************
    fft_chunks = []
    for chunk in encoded_chunks:
        fft_chunk = np.fft.fft(chunk)
        fft_chunks.append(fft_chunk)
        
    freqs = np.fft.fftfreq(tone_length)
    sampleRate = container.header[2]
     
    for chunk in fft_chunks:
        freqIdx = np.argmax(np.abs(chunk)**2)
        freq = freqs[freqIdx]
        freq_in_hertz = abs(freq * sampleRate)
        
        #print "frequency in hertz is: " + str(freq_in_hertz)
     
     
    #**************************************************************
            
    unchunked_bytes = unchunk(encoded_chunks)

    print "Mixed chunks: " + str(paybyte_idx)
    
    thing = ''.join(struct.pack('h', v) for v in unchunked_bytes)

    print "Length of data" + str(len(str(thing)))
    
    return WaveFile(container.header, thing)

def decode(trojan):
    """ Decode a payload from a trojan AudioFile that has been encoded 
    using the Modify LSB algorithm. Returns a Payload.
    """
    payload_data = []

    payload_spacing = 0
    paybit_space = 0
    
    toneLength = 882

    chunks = []
    
    tdata = struct.unpack('{n}h'.format(n=trojan.header[1] * trojan.header[3]), str(trojan.data))
    tdata=np.array(tdata)

    print "Size of audio data: " + str(trojan.header[1] * trojan.header[3])

    """
    print "******************************************"
    w = np.fft.fft(tdata)
    freqs = np.fft.fftfreq(len(w))
    print(freqs.min(),freqs.max())
    # (-0.5, 0.cd499975)

    # Find the peak in the coefficients
    print w
    print "poop"
    idx=np.argmax(np.abs(w)**2)
    print idx
    freq=freqs[idx]    
    freq_in_hertz=abs(freq*44100)
    print(freq_in_hertz)
    # 439.8975
    print "******************************************"
    """
    
    startIdx = 0
    for i in range(len(tdata) / 1500):
        endIdx = startIdx + 1500
        chunk = tdata[startIdx:endIdx]
        chunk = np.array(chunk)
        chunks.append(chunk)
        startIdx = endIdx

    #for i, c in enumerate(chunks):
    #    wav_file=wave.open("part"+str(i)+".wav", 'w')    
    #    wav_file.setparams((2,2,44100,40000, "NONE", "not compressed"))
    #    for v in c:
    #        wav_file.writeframes(struct.pack('h', v))
    #    wav_file.close()
        
    print str(len(chunks))

    fft_chunks = []

    payload_chunk = 0
    
    for chunk in chunks:
        fft_chunk = np.fft.fft(chunk)
        fft_chunks.append(fft_chunk)
        
    freqs = np.fft.fftfreq(1500)
    sampleRate = trojan.header[2]

    payload_bits = []
    
    for i,  chunk in enumerate(fft_chunks):
        freqIdx = np.argmax(np.abs(chunk)**2)
        freq = freqs[freqIdx]
        freq_in_hertz = abs(freq * sampleRate)
        
        if i < 580 * 8:
            if freq_in_hertz == 0.0:
                payload_bits.append(1)
            else:
                payload_bits.append(0)
        
        print "frequency in hertz is: " + str(freq_in_hertz)
        print "Amplitude is: " + str(freqIdx)

    payload_bytes = []
        
    startIdx = 0
    for i in range(len(payload_bits)):
        endIdx = startIdx + 8
        s = payload_bits[startIdx:endIdx]
        if len(s) == 8: 
            nByte = BitArray.from_bits(s).to_int()
            payload_bytes.append(nByte)
        startIdx = endIdx

        
    return Payload(bytearray(payload_bytes))
