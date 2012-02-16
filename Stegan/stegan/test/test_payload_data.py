import sys, os
import unittest

from stegan.payload import Payload

class TestWaveFile(unittest.TestCase):
    def setUp(self):
        pass
    
    def tearDown(self):
        pass

    def test__fromFile_whenFileNotExists_raiseException(self):
        self.assertRaises(IOError, Payload.fromFile, "/superawesomecatpic.jpg")

    def test_fromFile_ReadFileSuccessful_DataEqualsExpected(self):
        # write payload "hey"
        payloadBytes = bytearray("hey")
        testPayload = Payload(payloadBytes)
        testPayload.writeToFile("hey.txt")
        
        payload = Payload.fromFile("hey.txt")
        
        os.remove("hey.txt")
        self.assertEqual(payloadBytes, payload.data)

    def test_writeToFile_validPayload_FileContainsPayload(self):
        # write payload "hey"
        payloadBytes = bytearray("hey")
        testPayload = Payload(payloadBytes)
        testPayload.writeToFile("hey.txt")
        
        # read it back
        with open("hey.txt", mode="r") as f:
            data = bytearray(f.read())
        
        os.remove("hey.txt")
        self.assertEqual(payloadBytes, data)
        
    

if __name__ == "__main__":
    unittest.main()
