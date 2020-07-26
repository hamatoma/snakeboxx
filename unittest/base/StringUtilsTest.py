'''
Created on 12.04.2018

@author: hm
'''
from unittest.UnitTestCase import UnitTestCase
import os
import re
import base.StringUtils

DEBUG = False

class StringUtilsTest(UnitTestCase):

    def debugFlag(self):
        base.StringUtils.avoidWarning(self)
        return DEBUG

    def testJoin(self):
        if DEBUG: return
        self.assertIsEqual('1 2 3', base.StringUtils.join(' ', [1,2,3]))
        self.assertIsEqual('1,B,[]', base.StringUtils.join(',', [1, 'B', []]))
        self.assertIsEqual('A.B.C', base.StringUtils.join('.', ['A', 'B', 'C']))
        self.assertIsEqual('', base.StringUtils.join('.', None))

    def testToFile(self):
        if DEBUG: return
        fn = '/tmp/stringutils.tmp'
        if os.path.exists(fn):
            os.unlink(fn)
        content = 'line1\nline2'
        base.StringUtils.toFile(fn, content)
        self.assertTrue(os.path.exists(fn))
        self.assertFileContains('line1', fn)
        self.assertFileContains('line2', fn)

    def testToFileMode(self):
        if DEBUG: return
        fn = base.FileHelper.tempFile('modetest.txt', 'unittest.2')
        base.StringUtils.toFile(fn, 'Hi', fileMode=0o570)
        status = os.stat(fn)
        self.assertIsEqual(0o570, status.st_mode % 0o1000)

    def testToFileError(self):
        if DEBUG: return
        fn = '/tmp/not-existing-dir/stringutils.tmp'
        if os.path.exists(fn):
            os.unlink(fn)
        content = 'line1\nline2'
        logger = base.MemoryLogger.MemoryLogger(4)
        base.StringUtils.setLogger(logger)
        base.StringUtils.toFile(fn, content)
        self.assertFalse(os.path.exists(fn))
        self.assertIsEqual(1, logger._errors)
        self.assertMatches(r'cannot write to ', logger._firstErrors[0])

    def testFromFile(self):
        if DEBUG: return
        fn = '/tmp/stringutils.tmp'
        content = 'xline1\nxline2'
        base.StringUtils.toFile(fn, content)
        current = base.StringUtils.fromFile(fn)
        self.assertIsEqual(content, current)

    def testFromFileSep(self):
        if DEBUG: return
        fn = '/tmp/stringutils.tmp'
        content = 'xline1\nxline2'
        base.StringUtils.toFile(fn, content)
        current = base.StringUtils.fromFile(fn, '\n')
        self.assertIsEqual(content.split('\n'), current)

    def testTailOfWord(self):
        if DEBUG: return
        self.assertIsEqual('x', base.StringUtils.tailOfWord('-ax', '-a'))
        self.assertIsEqual('x', base.StringUtils.tailOfWord('-b -ax', '-a'))
        self.assertIsEqual('x', base.StringUtils.tailOfWord('-ax -b', '-a'))
        self.assertIsEqual('x', base.StringUtils.tailOfWord('-c -ax -b', '-a'))
        self.assertIsEqual('x', base.StringUtils.tailOfWord('-ax\t -b', '-a'))
        self.assertIsEqual('x', base.StringUtils.tailOfWord('y \t-ax\t -b', '-a'))

        self.assertNone(base.StringUtils.tailOfWord('--find-a-ax', '-a'))
        self.assertNone(base.StringUtils.tailOfWord('-b\t-c -d', '-a'))

    def testFormatSize(self):
        if DEBUG: return
        self.assertIsEqual('120 Byte', base.StringUtils.formatSize(120))
        self.assertIsEqual('123.456 KB', base.StringUtils.formatSize(123456))
        self.assertIsEqual('123.456 MB', base.StringUtils.formatSize(123456*1000))
        self.assertIsEqual('12.346 MB', base.StringUtils.formatSize(123456*100))
        self.assertIsEqual('1.235 MB', base.StringUtils.formatSize(123456*10))
        self.assertIsEqual('123.456 GB', base.StringUtils.formatSize(123456*1000*1000))
        self.assertIsEqual('123.456 TB', base.StringUtils.formatSize(123456*1000*1000*1000))

    def testHasContent(self):
        if DEBUG: return
        filename = self.tempFile('example.txt', 'stringutiltest')
        base.StringUtils.toFile(filename, '')
        self.assertFalse(base.StringUtils.hasContent(filename))
        base.StringUtils.toFile(filename, '# comment')
        self.assertFalse(base.StringUtils.hasContent(filename))
        base.StringUtils.toFile(filename, '# comment\n\t   \n\n#comment2')
        self.assertFalse(base.StringUtils.hasContent(filename))
        self.assertFalse(base.StringUtils.hasContent(filename + '.not.existing'))
        base.StringUtils.toFile(filename, '\t// comment\n\t   \n\n//comment2')
        self.assertFalse(base.StringUtils.hasContent(filename, '//'))

        base.StringUtils.toFile(filename, '\t// comment\n\t   \n\//comment2')
        self.assertTrue(base.StringUtils.hasContent(filename, '#'))
        base.StringUtils.toFile(filename, '# has content!\n\na=3')
        self.assertTrue(base.StringUtils.hasContent(filename, '#'))

    def testFirstMatch(self):
        if DEBUG: return
        aList = ['# a=2', '#', 'b=3', '\t name = Jonny Cash ']
        regExpr = re.compile(r'^\s*(\w+)\s*=\s*(.*?)\s*$')
        matcher = base.StringUtils.firstMatch(aList, regExpr)
        self.assertNotNone(matcher)
        self.assertIsEqual('b', matcher.group(1))
        self.assertIsEqual('3', matcher.group(2))

        matcher = base.StringUtils.firstMatch(aList, regExpr, 3)
        self.assertNotNone(matcher)
        self.assertIsEqual('name', matcher.group(1))
        self.assertIsEqual('Jonny Cash', matcher.group(2))

    def testGrepInFile(self):
        if DEBUG: return
        filename = self.tempFile('grep.txt', 'stringutiltest')
        base.StringUtils.toFile(filename, """# Test
a = 1
# öäü b = 2
c=333
""")
        regExpr = re.compile(r'^\s*(\w+)\s*=\s*(.*?)\s*$')
        found = base.StringUtils.grepInFile(filename, regExpr)
        self.assertIsEqual(2, len(found))
        self.assertIsEqual('a = 1\n', found[0])
        self.assertIsEqual('c=333\n', found[1])

        found = base.StringUtils.grepInFile(filename, regExpr, 1)
        self.assertIsEqual(1, len(found))
        self.assertIsEqual("a = 1\n", found[0])

    def testGrepInFileGroup(self):
        if DEBUG: return
        filename = self.tempFile('grep.txt', 'stringutiltest')
        base.StringUtils.toFile(filename, """# Test
a = 1
# öäü b = 2
c=333
""")
        regExpr = re.compile(r'^\s*\w+\s*=\s*(.*?)\s*$')
        found = base.StringUtils.grepInFile(filename, regExpr, None, 1)
        self.assertIsEqual(2, len(found))
        self.assertIsEqual('1', found[0])
        self.assertIsEqual('333', found[1])

        found = base.StringUtils.grepInFile(filename, regExpr, 1)
        self.assertIsEqual(1, len(found))
        self.assertIsEqual("a = 1\n", found[0])

    def testLimitItemLength_WithoutElipsis(self):
        if DEBUG: return
        source = ['1', '22', '333', '4444']
        result = base.StringUtils.limitItemLength(source, 2)
        self.assertIsEqual(source[0], '1')
        self.assertIsEqual(source[3], '4444')
        self.assertIsEqual(len(source), len(result))
        for ix in range(len(source)):
            self.assertIsEqual(source[ix][0:2], result[ix])
        result = base.StringUtils.limitItemLength(source, 0)
        self.assertIsEqual('', ''.join(result))

    def testLimitItemLength(self):
        if DEBUG: return
        source = ['abcd1', 'abcd22', 'abcd333', 'abcd4444']
        result = base.StringUtils.limitItemLength(source, 5)
        self.assertIsEqual(source[0], 'abcd1')
        self.assertIsEqual(source[3], 'abcd4444')
        self.assertIsEqual(len(source), len(result))
        for ix in range(len(source)):
            if ix ==  0:
                self.assertIsEqual(source[ix], result[ix])
            else:
                self.assertIsEqual(source[ix][0:2] + '...', result[ix])
        result = base.StringUtils.limitItemLength(source, 0)
        self.assertIsEqual('', ''.join(result))

    def testToFloatAndTypeDate(self):
        if DEBUG: return
        [value, dataType] = base.StringUtils.toFloatAndType('2019.10.23')
        self.assertIsEqual(1571781600.0, value)
        self.assertIsEqual('date', dataType)
        [value, dataType] = base.StringUtils.toFloatAndType('1970-01-01')
        self.assertIsEqual(-3600.0, value)
        self.assertIsEqual('date', dataType)

    def testToFloatAndTypeTime(self):
        if DEBUG: return
        [value, dataType] = base.StringUtils.toFloatAndType('01:02:03')
        self.assertIsEqual(1*3600+2*60+3, value)
        self.assertIsEqual('time', dataType)
        [value, dataType] = base.StringUtils.toFloatAndType('2:17')
        self.assertIsEqual(2*3600+17*60, value)
        self.assertIsEqual('time', dataType)

    def testToFloatAndTypeDateTime(self):
        if DEBUG: return
        [value, dataType] = base.StringUtils.toFloatAndType('2019.10.23T01:02:03')
        self.assertIsEqual(1571785323.0, value)
        self.assertIsEqual('datetime', dataType)
        [value, dataType] = base.StringUtils.toFloatAndType('1970-01-02 5:17')
        self.assertIsEqual(101820.0, value)
        self.assertIsEqual('datetime', dataType)

    def testToFloatAndTypeHex(self):
        if DEBUG: return
        [value, dataType] = base.StringUtils.toFloatAndType('0x1234')
        self.assertIsEqual(float(0x1234), value)
        self.assertIsEqual('int', dataType)
        [value, dataType] = base.StringUtils.toFloatAndType('0XABCDEF0123456')
        self.assertIsEqual(float(0xABCDEF0123456), value)
        self.assertIsEqual('int', dataType)
        [value, dataType] = base.StringUtils.toFloatAndType('0Xabcdef0')
        self.assertIsEqual(float(0xABCDEF0), value)
        self.assertIsEqual('int', dataType)

    def testToFloatAndTypeOct(self):
        if DEBUG: return
        [value, dataType] = base.StringUtils.toFloatAndType('01234')
        self.assertIsEqual(float(0o1234), value)
        self.assertIsEqual('int', dataType)
        [value, dataType] = base.StringUtils.toFloatAndType('012345670')
        self.assertIsEqual(float(0o12345670), value)
        self.assertIsEqual('int', dataType)

    def testToFloatAndTypeInt(self):
        if DEBUG: return
        [value, dataType] = base.StringUtils.toFloatAndType('1234')
        self.assertIsEqual(1234.0, value)
        self.assertIsEqual('int', dataType)
        [value, dataType] = base.StringUtils.toFloatAndType('987654321')
        self.assertIsEqual(987654321.0, value)
        self.assertIsEqual('int', dataType)

    def testToFloatAndTypeFloat(self):
        if DEBUG: return
        [value, dataType] = base.StringUtils.toFloatAndType('1234.0')
        self.assertIsEqual(1234.0, value)
        self.assertIsEqual('float', dataType)
        [value, dataType] = base.StringUtils.toFloatAndType('987654321.0')
        self.assertIsEqual(987654321.0, value)
        self.assertIsEqual('float', dataType)
        [value, dataType] = base.StringUtils.toFloatAndType('1.23E+44')
        self.assertIsEqual(1.23E+44, value)
        self.assertIsEqual('float', dataType)

    def testToFloatAndTypeError(self):
        if DEBUG: return
        [value, dataType] = base.StringUtils.toFloatAndType('host3')
        self.assertIsEqual('float (or int or date(time)) expected, found: host3', value)
        self.assertIsEqual('undef', dataType)

    def testToFloatDate(self):
        if DEBUG: return
        value = base.StringUtils.toFloat('2019.10.23')
        self.assertIsEqual(1571781600.0, value)
        value = base.StringUtils.toFloat('1970-01-01')
        self.assertIsEqual(-3600.0, value)

    def testToFloatTime(self):
        if DEBUG: return
        value = base.StringUtils.toFloat('01:02:03')
        self.assertIsEqual(1*3600+2*60+3, value)
        value = base.StringUtils.toFloat('2:17')
        self.assertIsEqual(2*3600+17*60, value)

    def testToFloatDateTime(self):
        if DEBUG: return
        value = base.StringUtils.toFloat('2019.10.23T01:02:03')
        self.assertIsEqual(1571785323.0, value)
        value = base.StringUtils.toFloat('1970-01-02 5:17')
        self.assertIsEqual(101820.0, value)

    def testToFloatHex(self):
        if DEBUG: return
        value = base.StringUtils.toFloat('0x1234')
        self.assertIsEqual(float(0x1234), value)
        value = base.StringUtils.toFloat('0XABCDEF0123456')
        self.assertIsEqual(float(0xABCDEF0123456), value)
        value = base.StringUtils.toFloat('0Xabcdef0')
        self.assertIsEqual(float(0xABCDEF0), value)

    def testToFloatOct(self):
        if DEBUG: return
        value = base.StringUtils.toFloat('01234')
        self.assertIsEqual(float(0o1234), value)
        value = base.StringUtils.toFloat('012345670')
        self.assertIsEqual(float(0o12345670), value)

    def testToFloatInt(self):
        if DEBUG: return
        value = base.StringUtils.toFloat('1234')
        self.assertIsEqual(1234.0, value)
        value = base.StringUtils.toFloat('987654321')
        self.assertIsEqual(987654321.0, value)

    def testToFloatFloat(self):
        if DEBUG: return
        value = base.StringUtils.toFloat('1234.0')
        self.assertIsEqual(1234.0, value)
        value = base.StringUtils.toFloat('987654321.0')
        self.assertIsEqual(987654321.0, value)
        value = base.StringUtils.toFloat('1.23E+44')
        self.assertIsEqual(1.23E+44, value)

    def testToFloatError(self):
        if DEBUG: return
        value = base.StringUtils.toFloat('host3')
        self.assertIsEqual('float (or int or date(time)) expected, found: host3', value)

    def testAsInt(self):
        if DEBUG: return
        self.assertIsEqual(321, base.StringUtils.asInt('321'))
        self.assertIsEqual(0x321, base.StringUtils.asInt('0x321'))
        self.assertIsEqual(0o321, base.StringUtils.asInt('0321'))
        self.assertIsEqual(-33, base.StringUtils.asInt('-33', 777))
        self.assertIsEqual(77, base.StringUtils.asInt('99x', 77))
        self.assertIsEqual(777, base.StringUtils.asInt('x2', 777))

    def testRegExprCompile(self):
        if DEBUG: return
        rexpr = base.StringUtils.regExprCompile('\d', None, None, True)
        self.assertNotNone(rexpr.match('7'))
        rexpr = base.StringUtils.regExprCompile('Hi', None, None, False)
        self.assertNotNone(rexpr.match('hi'))

    def testRegExprCompileError(self):
        if DEBUG: return
        rexpr = base.StringUtils.regExprCompile('*.txt', 'test of wrong pattern', self._logger)
        self.assertNone(rexpr)
        self._logger.contains('error in regular expression in test of wrong pattern: nothing to repeat at position 0')
        rexpr = base.StringUtils.regExprCompile('(*.txt', 'test of wrong pattern')
        self.assertNone(rexpr)

    def testMinimizeArrayUtfError(self):
        if DEBUG: return
        list1 = [b'\xffabcdefghijklmnopqrstuvwxyz01234567890', b'abcdefghijklmnopqrstuvwxyz01234567890\xff']
        rc = base.StringUtils.minimizeArrayUtfError(list1, self._logger)
        self.assertIsEqual(2, len(rc))
        self.assertIsEqual(1, rc[0].find('abcdefghijklmnopqrstuvwxyz01234567890'))
        self.assertIsEqual(0, rc[1].find('abcdefghijklmnopqrstuvwxyz01234567890'))

    def testStringOption(self):
        if DEBUG: return
        self.assertIsEqual('', base.StringUtils.stringOption('a-b', 'c', '--a-b'))
        self.assertIsEqual('TrUe', base.StringUtils.stringOption('a-b', 'c', '--a-b=TrUe'))
        self.assertIsEqual('TrUe', base.StringUtils.stringOption('a-b', 'c', '-cTrUe'))
        self.assertNone(base.StringUtils.stringOption('a-b', 'c', '-CTrUe'))
        self.assertNone(base.StringUtils.stringOption('a-b', 'c', '-a-bc'))

    def testBoolOption(self):
        if DEBUG: return
        self.assertTrue(base.StringUtils.boolOption('a-b', 'c', '--a-b'))
        self.assertTrue(base.StringUtils.boolOption('a-b', 'c', '--a-b=TrUe'))
        self.assertTrue(base.StringUtils.boolOption('a-b', 'c', '--a-b=t'))
        self.assertFalse(base.StringUtils.boolOption('a-b', 'c', '--a-b=fAlSe'))
        self.assertFalse(base.StringUtils.boolOption('a-b', 'c', '--a-b=f'))
        self.assertTrue(base.StringUtils.boolOption('a-b', 'c', '-c'))
        self.assertTrue(base.StringUtils.boolOption('a-b', 'c', '-ct'))
        self.assertTrue(base.StringUtils.boolOption('a-b', 'c', '-ctrue'))
        self.assertFalse(base.StringUtils.boolOption('a-b', 'c', '-cfAlSe'))
        self.assertFalse(base.StringUtils.boolOption('a-b', 'c', '-cf'))
        self.assertNone(base.StringUtils.boolOption('a-bc', 'd', '--a-b'))
        self.assertNone(base.StringUtils.boolOption('a-bc', 'e', '-c'))

    def testBoolOptionError(self):
        if DEBUG: return
        try:
            base.StringUtils.boolOption('a-b', 'c', '--a-b=blub')
            self.assertTrue(False)
        except:
            self.assertTrue(True)

    def testIntOption(self):
        if DEBUG: return
        self.assertIsEqual(34, base.StringUtils.intOption('a-b', 'c', '--a-b=34'))
        self.assertIsEqual(9, base.StringUtils.intOption('a-b', 'c', '-c9'))
        self.assertNone(base.StringUtils.boolOption('a-bc', 'd', '--ab=4'))
        self.assertNone(base.StringUtils.boolOption('a-bc', 'd', '-D99'))

    def testIntOptionError(self):
        if DEBUG: return
        try:
            base.StringUtils.intOption('a-b', 'c', '--a-b=34x')
            self.assertTrue(False)
        except:
            self.assertTrue(True)

    def testSecondsToString(self):
        if DEBUG: return
        self.assertIsEqual('00:00:00', base.StringUtils.secondsToString(0))
        self.assertIsEqual('03:04:15', base.StringUtils.secondsToString(3*3600+4*60+15))
        self.assertIsEqual('124:59:33', base.StringUtils.secondsToString(124*3600+59*60+33))

    def testPrivateConfig(self):
        if DEBUG: return
        config = base.StringUtils.privateConfig()
        self.assertIsEqual('xyz', config.getString('StringUtil.test.entry'))

    def testRegExprOption(self):
        regExpr = base.StringUtils.regExprOption('name', 'n', r'--name=^[a-z]+$')
        self.assertIsEqual("re.compile('^[a-z]+$', re.IGNORECASE)", str(regExpr))
        self.assertIsEqual('jonny', regExpr.match('jonny').group(0))
        self.assertNone(base.StringUtils.regExprOption('name', 'n', r'--iname=^[a-z]+$'))

    def testRegExprOptionError(self):
        if DEBUG: return
        self.assertIsEqual("not a regular expression in --name: --name=^[a-z+$", base.StringUtils.regExprOption('name', 'n', r'--name=^[a-z+$'))

    def testIndentLines(self):
        if DEBUG: return
        lines = '  abc\n  def'
        self.assertIsEqual(' abc\n def', base.StringUtils.indentLines(lines, 1))
        self.assertIsEqual('abc\ndef', base.StringUtils.indentLines(lines, 0))
        self.assertIsEqual('   abc\n   def', base.StringUtils.indentLines(lines, 3, ' '))
        self.assertIsEqual('\tabc\n\tdef', base.StringUtils.indentLines(lines, 1, '\t'))
        self.assertIsEqual('...abc\n...def', base.StringUtils.indentLines(lines, 1, '...'))

    def testLimitLength(self):
        if DEBUG: return
        self.assertIsEqual('abcd', base.StringUtils.limitLength('abcd', 4))
        self.assertIsEqual('a..', base.StringUtils.limitLength('abcd', 3))
        self.assertIsEqual('ab', base.StringUtils.limitLength('ab..', 2))
        self.assertIsEqual('a', base.StringUtils.limitLength('ab..', 1))
        self.assertIsEqual('', base.StringUtils.limitLength('abcd', 0))

    def testLimitLength2(self):
        if DEBUG: return
        self.assertIsEqual('ab..cd', base.StringUtils.limitLength2('ab1234cd', 6))
        self.assertIsEqual('ab..cd', base.StringUtils.limitLength2('ab12345cd', 6))
        self.assertIsEqual('a..cd', base.StringUtils.limitLength2('ab1234cd', 5))
        self.assertIsEqual('a..cd', base.StringUtils.limitLength2('ab12345cd', 5))
        self.assertIsEqual('abcd', base.StringUtils.limitLength2('abcd', 4))
        self.assertIsEqual('acd', base.StringUtils.limitLength2('abcd', 3))
        self.assertIsEqual('ad', base.StringUtils.limitLength2('abcd', 2))
        self.assertIsEqual('d', base.StringUtils.limitLength2('abcd', 1))
        self.assertIsEqual('', base.StringUtils.limitLength2('abcd', 0))

    def testParseSize(self):
        if DEBUG: return
        errors = []
        self.assertIsEqual(12, base.StringUtils.parseSize('12', errors))
        self.assertIsEqual(1, base.StringUtils.parseSize('1B', errors))
        self.assertIsEqual(33000, base.StringUtils.parseSize('33k', errors))
        self.assertIsEqual(12*1024, base.StringUtils.parseSize('12Ki', errors))
        self.assertIsEqual(4*1000*1000, base.StringUtils.parseSize('4mb', errors))
        self.assertIsEqual(4*1024*1024, base.StringUtils.parseSize('4MiByte', errors))
        self.assertIsEqual(6*1000*1000*1000, base.StringUtils.parseSize('6G', errors))
        self.assertIsEqual(6*1024*1024*1024, base.StringUtils.parseSize('6GiByte', errors))
        self.assertIsEqual(99*1000*1000*1000*1000, base.StringUtils.parseSize('99tbyte', errors))
        self.assertIsEqual(99*1024*1024*1024*1024, base.StringUtils.parseSize('99Ti', errors))
        self.assertIsEqual(0, len(errors))
        #self.log('expecting x errors:')
        self.assertNone(base.StringUtils.parseSize('', errors))
        self.assertIsEqual('size cannot be empty', errors[0])
        self.assertNone(base.StringUtils.parseSize('3x', errors))
        self.assertIsEqual('not a valid size 3x. Expected <number>[<unit>], e.g. 10Mi', errors[1])
        self.assertNone(base.StringUtils.parseSize('9mbx', errors))
        self.assertIsEqual('not a valid size 9mbx. Expected <number>[<unit>], e.g. 10Mi', errors[2])
        self.assertNone(base.StringUtils.parseSize('9Gibyt', errors))
        self.assertIsEqual('not a valid size 9Gibyt. Expected <number>[<unit>], e.g. 10Mi', errors[3])

    def testSizeOption(self):
        #if DEBUG: return
        errors = []
        self.assertIsEqual(12, base.StringUtils.sizeOption('min-size', 'm', '-m12B', errors))
        self.assertIsEqual(6*1024*1024*1024, base.StringUtils.sizeOption('min-size', 'm', '--min-size=6GiByte', errors))
        self.assertIsEqual(0, len(errors))
        #self.log('expecting x errors:')
        self.assertNone(base.StringUtils.sizeOption('min-size', 'm', '-m', errors))
        self.assertIsEqual('size cannot be empty', errors[0])


if __name__ == '__main__':
    #import sys;sys.argv = ['', 'Test.testName']
    tester = StringUtilsTest()
    tester.run()
