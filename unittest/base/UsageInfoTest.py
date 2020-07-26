'''
Created on 12.04.2018

@author: hm
'''
from unittest.UnitTestCase import UnitTestCase
import base.MemoryLogger
import base.UsageInfo

DEBUG = False

class UsageInfoTest(UnitTestCase):
    def debugFlag(self):
        base.StringUtils.avoidWarning(self)
        return DEBUG


    def testBasics(self):
        logger = base.MemoryLogger.MemoryLogger()
        info = base.UsageInfo.UsageInfo(logger)
        info.appendDescription('''example <mode>
 displays this example
''')
        info.addMode('help', '''help <pattern>
 display a help message
  <pattern>: only matching modes will be displayed
 ''', 'APP-NAME help')
        current = info.asString('help', 1)
        self.assertIsEqual('''example <mode>
  displays this example
<mode>:
    help <pattern>
      display a help message
        <pattern>: only matching modes will be displayed
Examples:
APP-NAME help''', current)

    def testBoolOption(self):
        #if DEBUG: return
        processor = base.UsageInfo.OptionProcessor(self._logger)
        processor.add(base.UsageInfo.Option('case', 'ignore-case', 'i', 'the search is case insensitive',
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
        #if DEBUG: return
        processor = base.UsageInfo.OptionProcessor(self._logger)
        processor.add(base.UsageInfo.Option('case', 'ignore-case', 'i', 'the search is case insensitive',
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
    tester = UsageInfoTest()
    tester.run()
