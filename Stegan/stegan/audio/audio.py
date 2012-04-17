import os

def fileType(path):
    "Determine the type of file"
    
    ext = os.path.splitext(path)[1][1:].lower()

    if ext in ('mp3'):
        return 'mp3'
    elif ext in ('wav', 'wave'):
        return 'wave'
    else:
        raise Exception('Unknown format %s' % ext)
