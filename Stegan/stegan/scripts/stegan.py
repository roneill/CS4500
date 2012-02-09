"""
The Steganographic Project: hide data inside music files

@author: Daniel Bostwick
"""

import sys

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
        print "encoding"
    elif args['action'] == "decode":
        print "decoding"
    
