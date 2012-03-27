import sys, math
import numpy as np
import struct
import wave

from stegan.payload import Payload
from stegan.audio.wavefile import WaveFile
from stegan.utils.bitarray import BitArray
from stegan.utils.bits import get_bit, set_lsb, flip_lsb, get_lsb

def tone(freq):
    data_size=40000
    sampling_rate = 44100.0
    amp=100.0
    
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

    zero = tone(550)
    one = tone(880)
    
    tone_bit_map.append(zero)
    tone_bit_map.append(one)

    return tone_bit_map

def create_tone_byte_map():
    tone_byte_map = []

    tone1 = tone(550)
    tone2 = tone(20)
    
    for i in range(128):
        tone_byte_map.append(tone(15000.0 + i * 30))

    """
    for i in range(128):
        tone_byte_map.append(tone(0 + i))

    for i in range(128, 256):
        tone_byte_map.append(tone(16000 + i))
    """
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
    
    payload_data = [0,1,0,1,1,1,0,1]

    #[get_bit(payload.data, i) for i in range(len(payload.data) * 8)]
    
    payload_bytes_length = len(payload.data)
    payload_bits_length = len(payload_data)
    payload_spacing = 2
    tone_length = len(tone_bit_map[0])

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

    """
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

def approx_equal(a, b, tol):
    return (abs(a-b) / (abs(a)+abs(b))/2) < tol

def get_index(freqs, tone):
    toneIdx = -1
    currTolerance = .1
    for i, freq in enumerate(freqs):
        if approx_equal(freq, tone, .1) and .1 <= currTolerance: 
            toneIdx = i
            currTolerance = .1
        if approx_equal(freq, tone, .01) and .01 <= currTolerance: 
            toneIdx = i
            currTolerance = .01
        if approx_equal(freq, tone, .001) and .001 <= currTolerance: 
            toneIdx = i
            currTolerance = .001
        if approx_equal(freq, tone, .0001) and .0001 <= currTolerance:
            toneIdx = i
            currTolerance = .0001
        if approx_equal(freq, tone, .00001) and .00001 <= currTolerance: 
            toneIdx = i
            currTolerance = .00001
        if approx_equal(freq, tone, .000001) and .000001 <= currTolerance: 
            toneIdx = i
            currTolerance = .000001

    return toneIdx
    
    """
    while(key == None):
        prec -= 1
        if prec == 7:
            rounded_tone = round(tone,7)#float('%.7f' % tone)
        elif prec == 6:      
            rounded_tone = round(tone,6)#float('%.6f' % tone)
        elif prec == 5:      
            rounded_tone = round(tone,5)#float('%.5f' % tone)
        elif prec == 4:      
            rounded_tone = round(tone,4)#float('%.4f' % tone)
        elif prec == 3:      
            rounded_tone = round(tone,3)#float('%.3f' % tone)
        elif prec == 2:      
            rounded_tone = round(tone,2)#float('%.2f' % tone)
        elif prec == 1:      
            rounded_tone = round(tone,1)#float('%.1f' % tone)
        else:
            print i
            raise Exception
                
        key = freqs.get(rounded_tone)
        """

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
    
    startIdx = 0
    for i in range(len(tdata) / 40000):
        endIdx = startIdx + 40000
        chunk = tdata[startIdx:endIdx]
        chunk = np.array(chunk)
        chunks.append(chunk)
        startIdx = endIdx
        
    print str(len(chunks))

    fft_chunks = []

    payload_chunk = 0
    
    for chunk in chunks:
        fft_chunk = np.fft.fft(chunk)
        fft_chunks.append(fft_chunk)
        
    freqs = np.fft.fftfreq(40000)
    sampleRate = trojan.header[2]

    freqsd = {}

    for i, freq in enumerate(freqs):
        freqsd[freq] = i
    
    """
    for i, freq in enumerate(freqs):
        for j in reversed(range(8)):
            rounded_freq = round(freq, j)
            freqsd[rounded_freq] = i

    freqsd2 = {}
            
    for i, freq in enumerate(freqs):
        truncated_freq = float('%.8f' % freq)
        freqsd2[truncated_freq] = i
        truncated_freq = float('%.7f' % freq)
        freqsd2[truncated_freq] = i
        truncated_freq = float('%.6f' % freq)
        freqsd2[truncated_freq] = i
        truncated_freq = float('%.5f' % freq)
        freqsd2[truncated_freq] = i
        truncated_freq = float('%.4f' % freq)
        freqsd2[truncated_freq] = i
        truncated_freq = float('%.3f' % freq)
        freqsd2[truncated_freq] = i
        truncated_freq = float('%.2f' % freq)
        freqsd2[truncated_freq] = i
        """
        
    payload_bits = []

    payload_bytes = []

    tones = []

    """
    for i in range(128):
        tone = 15000.0 + i * 30
        tones.append(tone / sampleRate)
        
    toneIndices = []

    for i, tone in enumerate(tones):

        index = get_index(freqs, tone)

        #print index
        toneIndices.append(index)
        """

    toneIndices = [13605, 13633, 13660, 13687, 13714, 13742, 13769, 13796, 13823, 13850, 13878, 13905, 13932, 13959, 13986, 14014, 14041, 14068, 14095, 14123, 14150, 14177, 14204, 14231, 14259, 14286, 14313, 14340, 14367, 14395, 14422, 14449, 14476, 14503, 14531, 14558, 14585, 14612, 14640, 14667, 14694, 14721, 14748, 14776, 14803, 14830, 14857, 14884, 14912, 14939, 14966, 14993, 15021, 15048, 15075, 15102, 15129, 15157, 15184, 15211, 15238, 15265, 15293, 15320, 15347, 15374, 15401, 15429, 15456, 15483, 15510, 15538, 15565, 15592, 15619, 15646, 15674, 15701, 15728, 15755, 15782, 15810, 15837, 15864, 15891, 15919, 15946, 15973, 16000, 16027, 16055, 16082, 16109, 16136, 16163, 16191, 16218, 16245, 16272, 16299, 16327, 16354, 16381, 16408, 16436, 16463, 16490, 16517, 16544, 16572, 16599, 16626, 16653, 16680, 16708, 16735, 16762, 16789, 16816, 16844, 16871, 16898, 16925, 16953, 16980, 17007, 17034, 17061]
    
    for toneIdx in toneIndices:
        print toneIdx
        
    for i,  chunk in enumerate(fft_chunks):

        if i == 52:
            break

        """
        for i in range(128):
            tone = 0.0 + i
            tones.append(tone / sampleRate)
            
        for i in range(128, 256):
            tone = 16000.0 + i
            tones.append(tone / sampleRate)
        """
        
        """
        # get the index of the frequency bin
        for i, tone in enumerate(tones):
            
            rounded_tone = round(tone, 8)#float('%.8f' % tone)
            key = freqsd.get(rounded_tone)
            prec = 8

            while(key == None):
                prec -= 1
                if prec == 7:
                    rounded_tone = round(tone,7)#float('%.7f' % tone)
                elif prec == 6:      
                    rounded_tone = round(tone,6)#float('%.6f' % tone)
                elif prec == 5:      
                    rounded_tone = round(tone,5)#float('%.5f' % tone)
                elif prec == 4:      
                    rounded_tone = round(tone,4)#float('%.4f' % tone)
                elif prec == 3:      
                    rounded_tone = round(tone,3)#float('%.3f' % tone)
                elif prec == 2:      
                    rounded_tone = round(tone,2)#float('%.2f' % tone)
                elif prec == 1:      
                    rounded_tone = round(tone,1)#float('%.1f' % tone)
                else:
                    print i
                    raise Exception
                
                key = freqsd.get(rounded_tone)

            truncated_tone = float('%.8f' % tone)
            key2 = freqsd2.get(truncated_tone)
            prec = 8

            while(key2 == None):
                prec -= 1
                if prec == 7:
                    truncated_tone = float('%.7f' % tone)
                elif prec == 6:      
                    truncated_tone = float('%.6f' % tone)
                elif prec == 5:      
                    truncated_tone = float('%.5f' % tone)
                elif prec == 4:      
                    truncated_tone = float('%.4f' % tone)
                elif prec == 3:      
                    truncated_tone = float('%.3f' % tone)
                elif prec == 2:      
                    truncated_tone = float('%.2f' % tone)
                elif prec == 1:      
                    truncated_tone = float('%.1f' % tone)
                else:
                    print i
                    raise Exception
                
                key2 = freqsd2.get(truncated_tone)

                #if key != None:
                 #   print "Found key: " + str(truncated_tone)

            if rounded_tone != truncated_tone:
                print "Found rounded_tone: " + str(rounded_tone) + " and truncated tone: " + str(truncated_tone)
            correct_tone = min([rounded_tone, truncated_tone])
                
            toneIndices.append(freqsd[correct_tone])

            """
        """
            for i, freq in enumerate(freqs):
                if approx_equal(freq, tone, .0001): #.0001
                    toneIdx = i
                    toneIndices.append(toneIdx)
                    print "Tone was: " + str(tone) + "Freq was: " + str(freq)
                    break
                    """
            
        if len(toneIndices) < 128:
            print "There were" + str(len(toneIndices)) + " indices"
            raise Exception

        processed_values = np.abs(chunk)**2
        
        toneValues = [processed_values[i] for i in toneIndices]
        
        maxTone = max(toneValues)

        for i, tone in enumerate(toneValues):
            if tone == maxTone:
                print "Found a " + str(i)
                payload_bytes.append(i)
                
                break
        
        """
        zeroIdx = 0
        for i, freq in enumerate(freqs):
            #print freq
            if approx_equal(freq, zero, .001): #.0001
                print "The freq bin was:" + str(freq)
                zeroIdx = i
                break
            
        oneIdx = 0
        for i, freq in enumerate(freqs):
            if approx_equal(freq, one, .001):
                print "The freq bin was:" + str(freq)
                oneIdx = i
                break
        
        processed_values = np.abs(chunk)**2

        zero_value = processed_values[zeroIdx]
        one_value = processed_values[oneIdx]
        
        if zero_value > one_value: 
            print "Found a zero"
        else:
            print "Found a one"
        """
        
        """
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
        """
        
    startIdx = 0
    for i in range(len(payload_bits)):
        endIdx = startIdx + 8
        s = payload_bits[startIdx:endIdx]
        if len(s) == 8: 
            nByte = BitArray.from_bits(s).to_int()
            payload_bytes.append(nByte)
        startIdx = endIdx

        
    return Payload(bytearray(payload_bytes))
