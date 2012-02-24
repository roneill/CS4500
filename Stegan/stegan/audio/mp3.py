import os
import subprocess
from wavefile import WaveFile

LAME_PATH = "lame"

def decode(path):
    """ Decode an MP3 File into a WAVE File """
    newpath = path + ".wav"
    print "[MP3File] Decoding %s" % path
    
    subprocess.call([LAME_PATH, "--decode", path])
    print "[MP3File] Writing wave file to %s" % newpath
    
    return newpath
    
def encode(wavepath, resultpath):
    print "[MP3File] Encoding %s to %s" % (wavepath, resultpath)
    subprocess.call([LAME_PATH, wavepath, resultpath])
