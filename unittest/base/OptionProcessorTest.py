'''
Created on 12.04.2018

@author: hm
'''
from unittest.UnitTestCase import UnitTestCase
import base.OptionProcessor

debug = False
class OptionProcessorTest(UnitTestCase):

    def __init__(self):
        UnitTestCase.__init__(self)

    def testBasics(self):
        if debug: return
        processor = base.OptionProcessor.OptionProcessor(self._logger)
        self.assertEquals(0, processor._logger._errors)

    def testBoolOption(self):
        #if debug: return
        processor = base.OptionProcessor.OptionProcessor(self._logger)
        processor.add(base.OptionProcessor.Option('case', 'ignore-case', 'i', 'the search is case insensitive',
            None, 'bool'))
        option = processor.optionByName('case')
        self.assertNotNone(option)
        self.assertFalse(option._value)
        self.assertFalse(option._defaultValue)
        self.assertTrue(processor.scan(['--ignore-case']))
        self.assertTrue(option._value)
        self.assertTrue(processor.scan(['--ignore-case=FALSE']))
        self.assertFalse(option._value)
        self.assertTrue(processor.scan(['--ignore-case=True']))
        self.assertTrue(option._value)
        self.assertTrue(processor.scan(['--ignore-case=f']))
        self.assertFalse(option._value)
        self.assertTrue(processor.scan(['--ignore-case=t']))
        self.assertTrue(option._value)

        self.assertTrue(processor.scan(['-i']))
        self.assertTrue(option._value)
        self.assertTrue(processor.scan(['-iFALSE']))
        self.assertFalse(option._value)
        self.assertTrue(processor.scan(['-iTrue']))
        self.assertTrue(option._value)
        self.assertTrue(processor.scan(['-if']))
        self.assertFalse(option._value)
        self.assertTrue(processor.scan(['-it']))
        self.assertTrue(option._value)

    def testBoolOptionError(self):
        #if debug: return
        processor = base.OptionProcessor.OptionProcessor(self._logger)
        processor.add(base.OptionProcessor.Option('case', 'ignore-case', 'i', 'the search is case insensitive',
            None, 'bool'))
        option = processor.optionByName('case')
        self.assertNotNone(option)
        self.assertFalse(option._value)
        self.assertFalse(option._defaultValue)
        self.assertFalse(processor.scan(['--ignore-case=yes']))
        self._logger.contains('not a bool value')
        self.assertFalse(processor.scan(['--ignore']))
        self._logger.contains('unknown option')

if __name__ == '__main__':
    #import sys;sys.argv = ['', 'Test.testName']
    tester = OptionProcessorTest()
    tester.run()
