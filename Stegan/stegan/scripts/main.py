"""
The Steganographic Project: hide data inside music files

@author: Daniel Bostwick
"""

import sys
import traceback

from stegan.payload import Payload
from stegan.audio import audio, mp3
from stegan.audio.wavefile import WaveFile
from stegan.steganography import modify_lsb, tone_insertion, fft_encode

def parse_args():
    args = {}

    args['action'] = sys.argv[1][2:]
    
    if args['action'] == "encode":
        if len(sys.argv) == 5:
            args['container'] = sys.argv[2]
            args['payload'] = sys.argv[3]
            args['trojan'] = sys.argv[4]
        else:
            raise Exception("Unexpected number of arguments for --encode")
    elif args['action'] == "decode":
        if len(sys.argv) == 4:
            args['trojan'] = sys.argv[2]
            args['payload'] = sys.argv[3]
        else:
            raise Exception("Unexcepted number of arguments for --decode")
    else:
        raise Exception("Unknown action '%s'" % args['action'])
    
    return args

def print_usage():
    print """
Usage: 
  stegan --encode <container> <payload> <trojan>
  stegan --decode <trojan> <payload>

Options:
  --encode    Encode <payload> into the <container> audio file and write the 
              result to <trojan>.

  --decode    Decode the steganographic data hidden inside <trojan> and write
              it to <payload>.
"""

def run_encode(args):
    print "[Stegan] Encoding %s inside %s" % (args['payload'], args['container'])
    
    try:
        payload = Payload.fromFile(args['payload'])
        
        if audio.fileType(args['container']) == "mp3":
            wavpath = mp3.decode(args['container'])
            container = WaveFile.fromFile(wavpath)
        else:
            container = WaveFile.fromFile(args['container'])
        
        
        if audio.fileType(args['trojan']) == 'mp3':
            tempfile = args['trojan'].replace('.mp3', '.wav')

            trojan = WaveFile.emptyFile(tempfile, container.header)
            fft_encode.encode(payload, container, trojan)

            mp3path = mp3.encode(tempfile, args['trojan'])
        else:
            trojan = WaveFile.emptyFile(args['trojan'], container.header)
            fft_encode.encode(payload, container, trojan)
        
    except Exception as e:
        print "[Stegan] There was an error while encoding"
        print "[Stegan] %s" % e

def run_decode(args):
    print "[Stegan] Decoding from %s" % (args['trojan'])
    
    try:
        if audio.fileType(args['trojan']) == 'mp3':
            wavpath = mp3.decode(args['trojan'])
            trojan = WaveFile.fromFile(wavpath)
        else:
            trojan = WaveFile.fromFile(args['trojan'])

        payload = Payload.openFile(args['payload'])
            
        fft_encode.decode(trojan, payload)
        
    except Exception as e:
        print "[Stegan] There was an error while decoding"
        print "[Stegan] %s" % e

def run():
    try:
        args = parse_args()
    except IndexError:
        print "Stegan - The audio steganography project"
        print_usage()
        sys.exit(1)
    except Exception as e:
        print "Error:", e
        print_usage()
        sys.exit(1)
    
    if args['action'] == "encode":
        run_encode(args)
    elif args['action'] == "decode":
        run_decode(args)
