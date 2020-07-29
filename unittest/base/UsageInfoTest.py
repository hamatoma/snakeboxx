'''
Created on 12.04.2018

@author: hm
'''
import datetime

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
        if DEBUG:
            return
        processor = base.UsageInfo.OptionProcessor(self._logger)
        processor.add(base.UsageInfo.Option('ignore-case', 'i', 'the search is case insensitive',
                                            'bool'))
        option = processor.optionByName('ignore-case')
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
        if DEBUG:
            return
        processor = base.UsageInfo.OptionProcessor(self._logger)
        processor.add(base.UsageInfo.Option('ignore-case', 'i', 'the search is case insensitive',
                                            'bool'))
        option = processor.optionByName('ignore-case')
        self.assertNotNone(option)
        self.assertFalse(option._value)
        self.assertFalse(option._defaultValue)
        self.assertFalse(processor.scan(['--ignore-case=yes']))
        self._logger.contains('not a bool value')
        self.assertFalse(processor.scan(['--ignore']))
        self._logger.contains('unknown option')

    def testIntOption(self):
        if DEBUG:
            return
        processor = base.UsageInfo.OptionProcessor(self._logger)
        processor.add(base.UsageInfo.Option(
            'index', 'i', 'index to inspect', 'int', 0))
        option = processor.optionByName('index')
        self.assertNotNone(option)
        self.assertIsEqual(0, option._value)
        self.assertIsEqual(0, option._defaultValue)
        self.assertTrue(processor.scan(['--index=-3']))
        self.assertIsEqual(-3, option._value)
        self.assertTrue(processor.scan(['-i0x33']))
        self.assertIsEqual(0x33, option._value)

    def testFloatOption(self):
        if DEBUG:
            return
        processor = base.UsageInfo.OptionProcessor(self._logger)
        processor.add(base.UsageInfo.Option(
            'sum', 's', 'sum to process', 'float', 0.0))
        option = processor.optionByName('sum')
        self.assertNotNone(option)
        self.assertIsEqual(0.0, option._value)
        self.assertIsEqual(0.0, option._defaultValue)
        self.assertTrue(processor.scan(['--sum=1E-2']))
        self.assertIsEqual(1E-2, option._value)
        self.assertTrue(processor.scan(['-s0xa']))
        self.assertIsEqual(10.0, option._value)

    def testRegExprOption(self):
        if DEBUG:
            return
        processor = base.UsageInfo.OptionProcessor(self._logger)
        processor.add(base.UsageInfo.Option(
            'file', 'f', 'File to process', 'regexpr'))
        option = processor.optionByName('file')
        self.assertNotNone(option)
        self.assertIsEqual(None, option._value)
        self.assertIsEqual(None, option._defaultValue)
        self.assertTrue(processor.scan([r'--file=^.*\.(txt|doc)$']))
        self.assertNotNone(option._value.match('x.txt'))
        self.assertNone(option._value.match('x.data'))
        self.assertTrue(processor.scan([r'-f^(blue|green)\.css$']))
        self.assertNotNone(option._value.match('blue.css'))
        self.assertNone(option._value.match('blue.html'))

    def testRegSizeOption(self):
        if DEBUG:
            return
        processor = base.UsageInfo.OptionProcessor(self._logger)
        processor.add(base.UsageInfo.Option(
            'min-size', 'm', 'minimal file size', 'size', '8kibyte'))
        option = processor.optionByName('min-size')
        self.assertNotNone(option)
        self.assertIsEqual(8 * 1024, option._value)
        self.assertIsEqual(8 * 1024, option._defaultValue)
        self.assertTrue(processor.scan([r'--min-size=3M']))
        self.assertIsEqual(3 * 1000 * 1000, option._value)
        self.assertTrue(processor.scan([r'-m123']))
        self.assertIsEqual(123, option._value)

    def testDateOption(self):
        if DEBUG: return
        processor = base.UsageInfo.OptionProcessor(self._logger)
        processor.add(base.UsageInfo.Option(
            'younger-than', 'y', 'minimal file date', 'date', '1.1.1970'))
        option = processor.optionByName('younger-than')
        epoche = datetime.datetime(1970, 1, 1)
        self.assertNotNone(option)
        self.assertIsEqual(str(epoche), str(option._value))
        self.assertIsEqual(str(epoche), str(option._defaultValue))
        self.assertTrue(processor.scan([r'--younger-than=2020-07-02']))
        self.assertIsEqual('2020-07-02 00:00:00', str(option._value))
        self.assertTrue(processor.scan([r'-y3.2.1999']))
        self.assertIsEqual('1999-02-03 00:00:00', str(option._value))

    def testDateTimeOption(self):
        if DEBUG: return
        processor = base.UsageInfo.OptionProcessor(self._logger)
        processor.add(base.UsageInfo.Option(
            'younger-than', 'y', 'minimal file date', 'datetime', '1.1.1970T0:0:0'))
        option = processor.optionByName('younger-than')
        epoche = datetime.datetime(1970, 1, 1)
        self.assertNotNone(option)
        self.assertIsEqual(str(epoche), str(option._value))
        self.assertIsEqual(str(epoche), str(option._defaultValue))
        self.assertTrue(processor.scan([r'--younger-than=2020.07.02T3:4']))
        self.assertIsEqual('2020-07-02 03:04:00', str(option._value))
        self.assertTrue(processor.scan([r'-y3.2.1999-23:59:59']))
        self.assertIsEqual('1999-02-03 23:59:59', str(option._value))

    def testStringOption(self):
        if DEBUG: return
        processor = base.UsageInfo.OptionProcessor(self._logger)
        processor.add(base.UsageInfo.Option(
            'name', 'n', 'name of the project', 'string', 'master'))
        option = processor.optionByName('name')
        self.assertNotNone(option)
        self.assertIsEqual('master', option._value)
        self.assertIsEqual('master', option._defaultValue)
        self.assertTrue(processor.scan([r'--name=Joe']))
        self.assertIsEqual('Joe', option._value)
        self.assertTrue(processor.scan([r'-nThea']))
        self.assertIsEqual('Thea', option._value)

    def testExtendUsageInfoWithOptions(self):
        if DEBUG: return
        info = base.UsageInfo.UsageInfo(self._logger)
        info.appendDescription('''example <mode>
 displays this example
''')
        info.addMode('help', '''help <pattern>
 display a help message
  <pattern>: only matching modes will be displayed
 ''', 'APP-NAME help')
        info.addModeOption('help', base.UsageInfo.Option(
            'verbose', 'v', 'display more information ("verbose")', 'bool'))
        info.addModeOption('help', base.UsageInfo.Option(
            'name', 'n', 'name of the project'))
        info.extendUsageInfoWithOptions('help')
        current = info._descriptions['help']
        self.assertIsEqual('''help <pattern>
 display a help message
  <pattern>: only matching modes will be displayed
  <options>:
  --name=<string> or -n=<string>:
   name of the project
  --verbose or -v:
   display more information ("verbose")
''', current)

if __name__ == '__main__':
    #import sys;sys.argv = ['', 'Test.testName']
    tester = UsageInfoTest()
    tester.run()
