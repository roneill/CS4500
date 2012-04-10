import sys, os
import unittest

from stegan.audio.file import AudioFile

class TestWaveFile(unittest.TestCase):
    
    def test_detectFileType_whenMp3File_returnsMp3(self):
        path = "/path/to/an.mp3"    
        self.assertEqual(AudioFile._detectFileType(path), "mp3")
    
    def test_detectFileType_whenWaveFile_returnsWav(self):
        path = "/path/to/an.wav"    
        self.assertEqual(AudioFile._detectFileType(path), "wav")
