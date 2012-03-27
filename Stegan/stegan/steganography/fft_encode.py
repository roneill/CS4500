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

def create_tone_byte_map():
    tone_byte_map = []
    
    for i in range(256):
        tone_byte_map.append(tone(15000.0 + i * 2))
    
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

    tdata = struct.unpack('{n}h'.format(n=container.header[1] *
                                        container.header[3]),
                          str(container.data2))
    
    tdata=np.array(tdata)
    
    chunks = chunk_data(tdata, tone_length)
    
    paybyte_idx = 0
    paybit_idx = 0
    payload_spacing_idx = 0
    
    encoded_chunks = []

    print str(len(chunks))
    
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
            
    unchunked_bytes = unchunk(encoded_chunks)

    print "Mixed chunks: " + str(paybyte_idx)
    
    thing = ''.join(struct.pack('h', v) for v in unchunked_bytes)

    print "Length of data " + str(len(str(thing)))
    
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
        
    payload_bits = []

    payload_bytes = []

    tones = []

    """
    for i in range(256):
        tone = 15000.0 + i * 2
        tones.append(tone / sampleRate)
        
    toneIndices = []

    for i, tone in enumerate(tones):

        index = get_index(freqs, tone)

        print index
        toneIndices.append(index)
        """
        
    #toneIndices = [13605, 13610, 13615, 13619, 13624, 13628, 13633, 13637, 13642, 13646, 13651, 13655, 13660, 13664, 13669, 13674, 13678, 13683, 13687, 13692, 13696, 13701, 13705, 13710, 13714, 13719, 13723, 13728, 13732, 13737, 13742, 13746, 13751, 13755, 13760, 13764, 13769, 13773, 13778, 13782, 13787, 13791, 13796, 13801, 13805, 13810, 13814, 13819, 13823, 13828, 13832, 13837, 13841, 13846, 13850, 13855, 13859, 13864, 13869, 13873, 13878, 13882, 13887, 13891, 13896, 13900, 13905, 13909, 13914, 13918, 13923, 13927, 13932, 13937, 13941, 13946, 13950, 13955, 13959, 13964, 13968, 13973, 13977, 13982, 13986, 13991, 13996, 14000, 14005, 14009, 14014, 14018, 14023, 14027, 14032, 14036, 14041, 14045, 14050, 14054, 14059, 14064, 14068, 14073, 14077, 14082, 14086, 14091, 14095, 14100, 14104, 14109, 14113, 14118, 14123, 14127, 14132, 14136, 14141, 14145, 14150, 14154, 14159, 14163, 14168, 14172, 14177, 14181, 14186, 14191, 14195, 14200, 14204, 14209, 14213, 14218, 14222, 14227, 14231, 14236, 14240, 14245, 14250, 14254, 14259, 14263, 14268, 14272, 14277, 14281, 14286, 14290, 14295, 14299, 14304, 14308, 14313, 14318, 14322, 14327, 14331, 14336, 14340, 14345, 14349, 14354, 14358, 14363, 14367, 14372, 14376, 14381, 14386, 14390, 14395, 14399, 14404, 14408, 14413, 14417, 14422, 14426, 14431, 14435, 14440, 14445, 14449, 14454, 14458, 14463, 14467, 14472, 14476, 14481, 14485, 14490, 14494, 14499, 14503, 14508, 14513, 14517, 14522, 14526, 14531, 14535, 14540, 14544, 14549, 14553, 14558, 14562, 14567, 14572, 14576, 14581, 14585, 14590, 14594, 14599, 14603, 14608, 14612, 14617, 14621, 14626, 14630, 14635, 14640, 14644, 14649, 14653, 14658, 14662, 14667, 14671, 14676, 14680, 14685, 14689, 14694, 14699, 14703, 14708, 14712, 14717, 14721, 14726, 14730, 14735, 14739, 14744, 14748, 14753, 14757, 14762 ]

    toneIndices = [13605, 13607, 13609, 13611, 13613, 13615, 13616, 13618, 13620, 13622, 13624, 13625, 13627, 13629, 13631, 13633, 13635, 13636, 13638, 13640, 13642, 13644, 13645, 13647, 13649, 13651, 13653, 13654, 13656, 13658, 13660, 13662, 13664, 13665, 13667, 13669, 13671, 13673, 13674, 13676, 13678, 13680, 13682, 13683, 13685, 13687, 13689, 13691, 13693, 13694, 13696, 13698, 13700, 13702, 13703, 13705, 13707, 13709, 13711, 13713, 13714, 13716, 13718, 13720, 13722, 13723, 13725, 13727, 13729, 13731, 13732, 13734, 13736, 13738, 13740, 13742, 13743, 13745, 13747, 13749, 13751, 13752, 13754, 13756, 13758, 13760, 13762, 13763, 13765, 13767, 13769, 13771, 13772, 13774, 13776, 13778, 13780, 13781, 13783, 13785, 13787, 13789, 13791, 13792, 13794, 13796, 13798, 13800, 13801, 13803, 13805, 13807, 13809, 13810, 13812, 13814, 13816, 13818, 13820, 13821, 13823, 13825, 13827, 13829, 13830, 13832, 13834, 13836, 13838, 13840, 13841, 13843, 13845, 13847, 13849, 13850, 13852, 13854, 13856, 13858, 13859, 13861, 13863, 13865, 13867, 13869, 13870, 13872, 13874, 13876, 13878, 13879, 13881, 13883, 13885, 13887, 13888, 13890, 13892, 13894, 13896, 13898, 13899, 13901, 13903, 13905, 13907, 13908, 13910, 13912, 13914, 13916, 13918, 13919, 13921, 13923, 13925, 13927, 13928, 13930, 13932, 13934, 13936, 13937, 13939, 13941, 13943, 13945, 13947, 13948, 13950, 13952, 13954, 13956, 13957, 13959, 13961, 13963, 13965, 13966, 13968, 13970, 13972, 13974, 13976, 13977, 13979, 13981, 13983, 13985, 13986, 13988, 13990, 13992, 13994, 13996, 13997, 13999, 14001, 14003, 14005, 14006, 14008, 14010, 14012, 14014, 14015, 14017, 14019, 14021, 14023, 14025, 14026, 14028, 14030, 14032, 14034, 14035, 14037, 14039, 14041, 14043, 14045, 14046, 14048, 14050, 14052, 14054, 14055, 14057, 14059, 14061, 14063, 14064, 14066, 14068 ]
        
    for i, chunk in enumerate(fft_chunks):

        if i == 83:
            break

        processed_values = np.abs(chunk)**2
        
        toneValues = [processed_values[i] for i in toneIndices]
        
        maxTone = max(toneValues)

        for i, tone in enumerate(toneValues):
            if tone == maxTone:
                print "Found a " + str(i)
                payload_bytes.append(i)
                
                break
        
    startIdx = 0
    for i in range(len(payload_bits)):
        endIdx = startIdx + 8
        s = payload_bits[startIdx:endIdx]
        if len(s) == 8: 
            nByte = BitArray.from_bits(s).to_int()
            payload_bytes.append(nByte)
        startIdx = endIdx

        
    return Payload(bytearray(payload_bytes))
