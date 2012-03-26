import wave
import struct

import numpy as np

#from utils import plot
import plot


class WaveFile(object):

    @classmethod
    def fromFile(cls, path):
        f = wave.open(path, "rb")
        header = f.getparams()
        data = f.readframes(header[3])
        
        f.close()
        
        return WaveFile(header, data)


    def __init__(self, headers, frames):
        self.headers = headers
        self.rawframes = frames
        
        self._unpackFrames()
        self._separateChannels()

    
    def _unpackFrames(self):
        """ Unpack the raw string of bytes contained in rawframes
        into an array of ints. Each element of this array will correspond
        to one sample
        """
        print "[WaveFile] _unpackFrames"

        nbytes = self.sampwidth() * self.nframes()
        pack_fmt = "{nbytes}h".format(nbytes = nbytes)
        
        print "[WaveFile] nbytes = %s, len(rawframes) = %s" % (nbytes, len(self.rawframes))
        
        self.frames = struct.unpack(pack_fmt, self.rawframes)
        
        


    def _separateChannels(self):
        print "[WaveFile] _separateChannels"
        num_channels = self.nchannels()
        self.channel_data = [[],[]]
    
        for idx, sample in enumerate(self.frames):
            channel = idx % num_channels
            self.channel_data[channel].append(sample)
    
    def window(self, nsamples, offset=0):
        """ Returns a window of the data in this wave file. Everything
        except the request slice will be 0, and the requested slice
        will be unchanged.
        
        nsamples - the size of the window in samples
        offset   - the index of the sample to start with. Defaults to 0
        
        Returns a WaveFile
        """
        #newframes = []
        #zeroframe = "\x00"
        #for idx, frame in enumerate(self.rawframes):
            #if (idx >= offset and (idx - offset) < nsamples):
                #print repr(frame)
        #        newframes.append(frame)
            #else:
            #    newframes.append(zeroframe)

        newframes = []
        zeroframe = "\x00"
        for idx, frame in enumerate(self.rawframes):
            if (idx >= offset and (idx - offset) < nsamples):
                newframes.append(frame)
            else:
                newframes.append(zeroframe)
        
        newframes = ''.join(newframes)

        print "[window] type(rawframes) = %s" % type(self.rawframes)
        print "[window] type(newframes) = %s" % type(newframes)
        print "[window] len(rawframes) = %s" % len(self.rawframes)
        print "[window] len(newframes) = %s" % len(newframes)

        return WaveFile(self.headers, str(newframes))
    
    
    def nchannels(self):
        return self.headers[0]
    
    def sampwidth(self):
        return self.headers[1]
    
    def nframes(self):
        return self.headers[3]
    
    def freqs(self, channel=0):
        """ Returns a frequency analysis on the samples contained in this
        WaveFile
        
        channel - Which channel to perform the frequency analysis on
        
        Returns a result array whose elements are tuples of length 2 where
        the first element is a frequency in hertz and the second element
        is the power/amplitude of that frequency.
        """
        print "[freqs] Calculating frequencies"
        
        print 1
        signal = [x for x in self.channel_data[channel] if x != 0]
        
        print 2
        spectrum = abs(np.fft.fft(signal))
        
        print 3
        freqs = np.fft.fftfreq(len(spectrum), d=1/33.34)
        
        return zip(freqs, spectrum)
        
        #print 4
        #freq_idxs = (np.abs(fourier) ** 2)

        #print 5
        #result = []
        
        #for fidx in freq_idxs:
        #    print "fidx = %s" % fidx
        #    amp = fidx
        #    hertz = abs(freq[fidx] * samplerate)
        #    result.append((amp, hertz))
        
        #print 6
    
        #return result


if __name__ == "__main__":
    audio = WaveFile.fromFile("Stegan/test_audio/Pachelbels_Canon_Excerpt.wav")
    window = audio.window(2000000, 600000)
    
    plot.channels(zip(*window.channel_data))
    plot.frequency_distribution(window.freqs())
