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
                          str(container.data2))

    tdata = np.array(tdata)

    return tdata

def encode(payload, container):
    """ Encode a payload inside an audio container using the tone insertion
    algorithm. Returns a Trojan AudioFile with the payload inside it.
    """

    # Throw an exception if the container is too large to be encoded, over 80 minutes
    if(container.samples() > (container.channels() * container.sampleRate() * 80 * 60)):
	raise Exception("ERROR!: The length of the container audio file is greater than 80 minutes, which is not supported. Please choose a shorter audio file.")    
    
    trojan_audio_data = []
    
    payload_bytes_length = len(payload.data)

    unpacked_data = unpack_data(container)
    
    chunks = chunk_data(unpacked_data, 44100)

    # Throw an exception if the payload is too large for the container
    if(payload_bytes_length > len(chunks)):
	raise Exception("ERROR!: The length of the payload input is too large. The maximum number of bytes that can be stored in this container is: " + str(len(chunks)) + ". \n The size of this payload is: " + str(payload_bytes_length));
    
    paybyte_idx = 0
    
    encoded_chunks = []

    power_values = [393945810000.0, 539899162295.0, 612490081873.0, 623798167033.0, 505067660292.0, 361949695918.0, 479917644226.0, 592645741251.0, 613193537214.0, 566291394650.0, 406469417788.0, 433022069057.0, 548465946717.0, 621976251211.0, 598165832472.0, 469530365217.0, 320203171492.0, 515812421814.0, 597243245691.0, 606041667138.0, 524900334333.0, 372851824767.0, 466001023877.0, 575427054677.0, 617654823640.0, 566633194218.0, 426031074004.0, 408522222390.0, 548602199955.0, 612458930005.0, 603288157365.0, 490963349503.0, 335511069896.0, 509002808652.0, 605468066445.0, 615909169885.0, 538706915633.0, 398553706537.0, 454102429424.0, 576141236855.0, 624099015314.0, 573250763459.0, 452714820050.0, 383521941353.0, 526329634310.0, 593786434608.0, 593731642022.0, 511678063342.0, 363470129089.0, 486219618941.0, 581182725897.0, 619258451746.0, 560501967647.0, 425645666625.0, 426289317542.0, 567377659249.0, 610549316447.0, 575846347879.0, 474935295445.0, 320760712795.0, 512507097581.0, 616167075764.0, 608265625430.0, 523867184337.0, 382540699342.0, 464740229704.0, 587702154067.0, 616414169436.0, 565286880211.0, 451625434586.0, 406854040108.0, 547098613182.0, 612228702355.0, 592176096696.0, 487517244239.0, 341367730935.0, 489163601483.0, 590611774559.0, 608718248863.0, 545689968453.0, 406311232802.0, 437102241530.0, 568207164415.0, 611706735530.0, 580287024674.0, 458947465878.0, 302787301158.0, 541300058384.0, 606156219477.0, 600330956834.0, 523992784077.0, 359377703226.0, 488028543242.0, 587842031657.0, 622820200739.0, 548786817565.0, 433998788194.0, 422695413442.0, 563433953555.0, 615161749900.0, 591555669456.0, 481574652130.0, 322588738071.0, 505771170968.0, 612922411503.0, 610928284648.0, 522873984780.0, 387978774516.0, 465856949090.0, 584351863329.0, 619738421525.0, 572438949051.0, 438093400086.0, 406873432084.0, 553700513198.0, 627265425674.0, 598351838465.0, 501698344157.0, 348888581513.0, 489832622389.0, 595998622867.0, 600808109961.0, 532024491860.0, 402538896590.0, 437223665704.0, 560395328334.0, 611109531994.0, 574988005516.0, 450814697755.0, 306368594689.0, 519833063617.0, 606323553240.0, 605110255815.0, 501717261844.0, 362842144970.0, 485666150428.0, 576217512688.0, 612744042744.0, 548025303138.0, 425625353143.0, 415003100636.0, 554811040264.0, 619901933708.0, 590905761433.0, 485784292474.0, 324399676025.0, 511265609974.0, 599672552642.0, 606541839460.0, 529791846441.0, 388771104145.0, 456571176813.0, 582479518610.0, 624416268977.0, 575057267852.0, 448524311871.0, 396706989583.0, 546469396531.0, 608573797798.0, 596241514140.0, 489540289385.0, 347777295553.0, 496716412457.0, 596090468696.0, 619166859986.0, 544052728155.0, 402577928355.0, 440805427396.0, 565668463786.0, 606371434317.0, 577066811060.0, 465431200290.0, 310248714171.0, 530308815987.0, 607283054718.0, 613191840897.0, 516416577284.0, 367268412733.0, 465600145957.0, 589125363107.0, 626306482378.0, 565110176673.0, 423699558653.0, 419268586197.0, 553057513960.0, 620606775563.0, 601912661684.0, 488059121251.0, 339542450495.0, 518934959011.0, 603315301326.0, 613723982935.0, 536711726245.0, 388049746321.0, 454898777448.0, 574436067936.0, 615096268429.0, 580414377667.0, 451889776603.0, 402620158621.0, 532159127417.0, 613220172326.0, 599221087484.0, 499887794551.0, 361469790805.0, 479468507683.0, 604024703931.0, 622095176473.0, 549108464335.0, 415202158244.0, 428790809197.0, 566077619470.0, 624001627464.0, 579113111310.0, 485322347609.0, 308043537042.0, 508352491674.0, 615938352114.0, 602499662766.0, 503829031188.0, 372403288163.0, 463142942397.0, 580110189275.0, 622539341604.0, 572093385332.0, 432257377635.0, 410347714696.0, 536729358520.0, 613955738634.0, 594062040019.0, 484475916121.0, 331223222463.0, 502530038656.0, 604469798364.0, 609376428173.0, 544054777528.0, 386539586047.0, 444607954509.0, 573944281333.0, 624079036767.0, 566940942005.0, 457583142285.0, 292937487251.0, 537162769694.0, 597780676764.0, 595366660591.0, 513946407435.0, 354587313693.0, 487513284963.0, 586131866717.0, 614435812054.0, 551115703006.0, 418500708419.0, 430583864031.0, 567126145372.0, 618264961152.0 ]

    toneIndices = [i for i in range(15000, 15256)]

    for chunk in chunks:
        if paybyte_idx < payload_bytes_length:
            payload_byte = payload.data[paybyte_idx]
            
            fft_chunk = np.fft.fft(chunk)
            processed_values = np.abs(chunk)**2
	    
	    # Find the index of the frequency (of the frequencies in our byte map) with the highest power
            max_tone_power = 0;
	    for toneIdx in toneIndices:
		if(processed_values[toneIdx] > max_tone_power):
			max_tone_power = processed_values[toneIdx]
   	    

            byte_tone_index = toneIndices[payload_byte]
	    
  	    # Set the power of the frequency we are interested in to be 300,000 higher. This value is a guess and seems to work in practice. 
	    # The hope is that this value is the smallest peak we can reliably detect when decoding.
            power_value = max_tone_power + 300000
            fft_chunk[byte_tone_index] = math.sqrt(power_value)
	    

            encoded_chunk = np.fft.ifft(fft_chunk)
            encoded_chunks.append(encoded_chunk)

            paybyte_idx +=1
        else:
            encoded_chunks.append(chunk)
            
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

    chunks = chunk_data(tdata, 44100)

    fft_chunks = []
    
    for chunk in chunks:
        fft_chunk = np.fft.fft(chunk)
        fft_chunks.append(fft_chunk)
        
    freqs = np.fft.fftfreq(44100)
    sampleRate = trojan.header[2]

    payload_bytes = []
    tones = []

    toneIndices = [i for i in range(15000, 15256)]
    
    for i, chunk in enumerate(fft_chunks):

        processed_values = np.abs(chunk)**2
        
        toneValues = [processed_values[i] for i in toneIndices]
                    
	# Find the maximum of the tones we're interested in
        maxTone = max(toneValues)
        
        for i, tone in enumerate(toneValues):
            if tone == maxTone:
                print "Found a " + str(i)
                payload_bytes.append(i)
                break
        
    return Payload(bytearray(payload_bytes))
