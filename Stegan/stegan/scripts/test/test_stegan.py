import sys, os
import unittest

sys.path.insert(0, os.path.abspath(os.getcwd()))

from stegan.scripts import main

class TestStegan(unittest.TestCase):
    def setUp(self):
        del(sys.argv[1:])
    
    def tearDown(self):
        pass

    def test_parseArgs_whenNoArguments_raiseException(self):
        self.assertRaises(Exception, main.parse_args)
    
    def test_parseArgs_whenFirstArgNotEncodeOrDecode_raiseException(self):
        sys.argv.append('--unknown')
        
        self.assertRaises(Exception, main.parse_args)
        
        sys.argv.remove('--unknown')
        
    def test_parseArgs_whenEncodeWithTooFewArgs_raiseException(self):
        sys.argv.append('--encode')
        sys.argv.append('arg1')
        sys.argv.append('arg2')
        
        self.assertRaises(Exception, main.parse_args)
        
        sys.argv.remove('--encode')
        sys.argv.remove('arg1')
        sys.argv.remove('arg2')

    def test_parseArgs_whenEncodeWithTooManyArgs_raiseException(self):
        sys.argv.append('--encode')
        sys.argv.append('arg1')
        sys.argv.append('arg2')
        sys.argv.append('arg3')
        sys.argv.append('arg4')

        self.assertRaises(Exception, main.parse_args)

        sys.argv.remove('--encode')
        sys.argv.remove('arg1')
        sys.argv.remove('arg2')
        sys.argv.remove('arg3')
        sys.argv.remove('arg4')

    def test_parseArgs_whenEncodeWithCorrectParams_returnsDict(self):
        expectedArgs = {
            'action': 'encode',
            'container': 'arg1',
            'payload': 'arg2',
            'trojan': 'arg3'}
        
        sys.argv.append('--encode')
        sys.argv.append('arg1')
        sys.argv.append('arg2')
        sys.argv.append('arg3')
        
        self.assertEqual(expectedArgs, main.parse_args())
        
        sys.argv.remove('--encode')
        sys.argv.remove('arg1')
        sys.argv.remove('arg2')
        sys.argv.remove('arg3')
    
    def test_parseArgs_whenDecodeWithTooFewArgs_raiseException(self):
        sys.argv.append('--decode')
        sys.argv.append('arg1')

        self.assertRaises(Exception, main.parse_args)

        sys.argv.remove('--decode')
        sys.argv.remove('arg1')

    def test_parseArgs_whenDecodeWithTooManyArgs_raiseException(self):
        sys.argv.append('--decode')
        sys.argv.append('arg1')
        sys.argv.append('arg2')
        sys.argv.append('arg3')

        self.assertRaises(Exception, main.parse_args)

        sys.argv.remove('--decode')
        sys.argv.remove('arg1')
        sys.argv.remove('arg2')
        sys.argv.remove('arg3')

    def test_parseArgs_whenDecodeWithCorrectParams_returnsDict(self):
        expectedArgs = {
            'action': 'decode',
            'trojan': 'arg1',
            'payload': 'arg2'}

        sys.argv.append('--decode')
        sys.argv.append('arg1')
        sys.argv.append('arg2')

        self.assertEqual(expectedArgs, main.parse_args())

        sys.argv.remove('--decode')
        sys.argv.remove('arg1')
        sys.argv.remove('arg2')


if __name__ == "__main__":
    unittest.main()
        