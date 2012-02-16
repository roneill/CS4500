import sys, os
import unittest

from stegan.audio.wavefile import WaveFile

class TestWaveFile(unittest.TestCase):
    def setUp(self):
        pass
    
    def tearDown(self):
        pass

    def test_fromFile_whenFileNotExists_raiseException(self):
        self.assertRaises(IOError, WaveFile.fromFile, "/audiofilethatdoesntexist.wav")
    
    # We should test for successful reading of file

    # how to test writeToFile?
    

if __name__ == "__main__":
    unittest.main()
