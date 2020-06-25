'''
Created on 12.04.2018

@author: hm
'''
from unittest.UnitTestCase import UnitTestCase
import base.StringUtils
import os
import re

class StringUtilsTest(UnitTestCase):

    def testJoin(self):
        self.assertEquals('1 2 3', base.StringUtils.join(' ', [1,2,3]))
        self.assertEquals('1,B,[]', base.StringUtils.join(',', [1, 'B', []]))
        self.assertEquals('A.B.C', base.StringUtils.join('.', ['A', 'B', 'C']))
        self.assertEquals('', base.StringUtils.join('.', None))

    def testToFile(self):
        fn = '/tmp/stringutils.tmp'
        if os.path.exists(fn):
            os.unlink(fn)
        content = 'line1\nline2'
        base.StringUtils.toFile(fn, content)
        self.assertTrue(os.path.exists(fn))
        self.assertFileContains('line1', fn)
        self.assertFileContains('line2', fn)

    def testToFileMode(self):
        fn = base.FileHelper.tempFile('modetest.txt', 'unittest.2')
        base.StringUtils.toFile(fn, 'Hi', fileMode=0o570)
        status = os.stat(fn)
        self.assertEquals(0o570, status.st_mode % 0o1000)

    def testToFileError(self):
        fn = '/tmp/not-existing-dir/stringutils.tmp'
        if os.path.exists(fn):
            os.unlink(fn)
        content = 'line1\nline2'
        logger = base.MemoryLogger.MemoryLogger(4)
        base.StringUtils.setLogger(logger)
        base.StringUtils.toFile(fn, content)
        self.assertFalse(os.path.exists(fn))
        self.assertEquals(1, logger._errors)
        self.assertMatches(r'cannot write to ', logger._firstErrors[0])

    def testFromFile(self):
        fn = '/tmp/stringutils.tmp'
        content = 'xline1\nxline2'
        base.StringUtils.toFile(fn, content)
        current = base.StringUtils.fromFile(fn)
        self.assertEquals(content, current)

    def testFromFileSep(self):
        fn = '/tmp/stringutils.tmp'
        content = 'xline1\nxline2'
        base.StringUtils.toFile(fn, content)
        current = base.StringUtils.fromFile(fn, '\n')
        self.assertEquals(content.split('\n'), current)

    def testTailOfWord(self):
        self.assertEquals('x', base.StringUtils.tailOfWord('-ax', '-a'))
        self.assertEquals('x', base.StringUtils.tailOfWord('-b -ax', '-a'))
        self.assertEquals('x', base.StringUtils.tailOfWord('-ax -b', '-a'))
        self.assertEquals('x', base.StringUtils.tailOfWord('-c -ax -b', '-a'))
        self.assertEquals('x', base.StringUtils.tailOfWord('-ax\t -b', '-a'))
        self.assertEquals('x', base.StringUtils.tailOfWord('y \t-ax\t -b', '-a'))

        self.assertNone(base.StringUtils.tailOfWord('--find-a-ax', '-a'))
        self.assertNone(base.StringUtils.tailOfWord('-b\t-c -d', '-a'))

    def testFormatSize(self):
        self.assertEquals('120 Byte', base.StringUtils.formatSize(120))
        self.assertEquals('123.456 KB', base.StringUtils.formatSize(123456))
        self.assertEquals('123.456 MB', base.StringUtils.formatSize(123456*1000))
        self.assertEquals('12.346 MB', base.StringUtils.formatSize(123456*100))
        self.assertEquals('1.235 MB', base.StringUtils.formatSize(123456*10))
        self.assertEquals('123.456 GB', base.StringUtils.formatSize(123456*1000*1000))
        self.assertEquals('123.456 TB', base.StringUtils.formatSize(123456*1000*1000*1000))

    def testHasContent(self):
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
        aList = ['# a=2', '#', 'b=3', '\t name = Jonny Cash ']
        regExpr = re.compile(r'^\s*(\w+)\s*=\s*(.*?)\s*$')
        matcher = base.StringUtils.firstMatch(aList, regExpr)
        self.assertNotNone(matcher)
        self.assertEquals('b', matcher.group(1))
        self.assertEquals('3', matcher.group(2))

        matcher = base.StringUtils.firstMatch(aList, regExpr, 3)
        self.assertNotNone(matcher)
        self.assertEquals('name', matcher.group(1))
        self.assertEquals('Jonny Cash', matcher.group(2))

    def testGrepInFile(self):
        filename = self.tempFile('grep.txt', 'stringutiltest')
        base.StringUtils.toFile(filename, """# Test
a = 1
# öäü b = 2
c=333
""")
        regExpr = re.compile(r'^\s*(\w+)\s*=\s*(.*?)\s*$')
        found = base.StringUtils.grepInFile(filename, regExpr)
        self.assertEquals(2, len(found))
        self.assertEquals('a = 1\n', found[0])
        self.assertEquals('c=333\n', found[1])

        found = base.StringUtils.grepInFile(filename, regExpr, 1)
        self.assertEquals(1, len(found))
        self.assertEquals("a = 1\n", found[0])

    def testGrepInFileGroup(self):
        filename = self.tempFile('grep.txt', 'stringutiltest')
        base.StringUtils.toFile(filename, """# Test
a = 1
# öäü b = 2
c=333
""")
        regExpr = re.compile(r'^\s*\w+\s*=\s*(.*?)\s*$')
        found = base.StringUtils.grepInFile(filename, regExpr, None, 1)
        self.assertEquals(2, len(found))
        self.assertEquals('1', found[0])
        self.assertEquals('333', found[1])

        found = base.StringUtils.grepInFile(filename, regExpr, 1)
        self.assertEquals(1, len(found))
        self.assertEquals("a = 1\n", found[0])

    def testLimitItemLength_WithoutElipsis(self):
        source = ['1', '22', '333', '4444']
        result = base.StringUtils.limitItemLength(source, 2)
        self.assertEquals(source[0], '1')
        self.assertEquals(source[3], '4444')
        self.assertEquals(len(source), len(result))
        for ix in range(len(source)):
            self.assertEquals(source[ix][0:2], result[ix])
        result = base.StringUtils.limitItemLength(source, 0)
        self.assertEquals('', ''.join(result))

    def testLimitItemLength(self):
        source = ['abcd1', 'abcd22', 'abcd333', 'abcd4444']
        result = base.StringUtils.limitItemLength(source, 5)
        self.assertEquals(source[0], 'abcd1')
        self.assertEquals(source[3], 'abcd4444')
        self.assertEquals(len(source), len(result))
        for ix in range(len(source)):
            if ix ==  0:
                self.assertEquals(source[ix], result[ix])
            else:
                self.assertEquals(source[ix][0:2] + '...', result[ix])
        result = base.StringUtils.limitItemLength(source, 0)
        self.assertEquals('', ''.join(result))

    def testToFloatAndTypeDate(self):
        [value, dataType] = base.StringUtils.toFloatAndType('2019.10.23')
        self.assertEquals(1571781600.0, value)
        self.assertEquals('date', dataType)
        [value, dataType] = base.StringUtils.toFloatAndType('1970-01-01')
        self.assertEquals(-3600.0, value)
        self.assertEquals('date', dataType)

    def testToFloatAndTypeTime(self):
        [value, dataType] = base.StringUtils.toFloatAndType('01:02:03')
        self.assertEquals(1*3600+2*60+3, value)
        self.assertEquals('time', dataType)
        [value, dataType] = base.StringUtils.toFloatAndType('2:17')
        self.assertEquals(2*3600+17*60, value)
        self.assertEquals('time', dataType)

    def testToFloatAndTypeDateTime(self):
        [value, dataType] = base.StringUtils.toFloatAndType('2019.10.23T01:02:03')
        self.assertEquals(1571785323.0, value)
        self.assertEquals('datetime', dataType)
        [value, dataType] = base.StringUtils.toFloatAndType('1970-01-02 5:17')
        self.assertEquals(101820.0, value)
        self.assertEquals('datetime', dataType)

    def testToFloatAndTypeHex(self):
        [value, dataType] = base.StringUtils.toFloatAndType('0x1234')
        self.assertEquals(float(0x1234), value)
        self.assertEquals('int', dataType)
        [value, dataType] = base.StringUtils.toFloatAndType('0XABCDEF0123456')
        self.assertEquals(float(0xABCDEF0123456), value)
        self.assertEquals('int', dataType)
        [value, dataType] = base.StringUtils.toFloatAndType('0Xabcdef0')
        self.assertEquals(float(0xABCDEF0), value)
        self.assertEquals('int', dataType)

    def testToFloatAndTypeOct(self):
        [value, dataType] = base.StringUtils.toFloatAndType('01234')
        self.assertEquals(float(0o1234), value)
        self.assertEquals('int', dataType)
        [value, dataType] = base.StringUtils.toFloatAndType('012345670')
        self.assertEquals(float(0o12345670), value)
        self.assertEquals('int', dataType)

    def testToFloatAndTypeInt(self):
        [value, dataType] = base.StringUtils.toFloatAndType('1234')
        self.assertEquals(1234.0, value)
        self.assertEquals('int', dataType)
        [value, dataType] = base.StringUtils.toFloatAndType('987654321')
        self.assertEquals(987654321.0, value)
        self.assertEquals('int', dataType)

    def testToFloatAndTypeFloat(self):
        [value, dataType] = base.StringUtils.toFloatAndType('1234.0')
        self.assertEquals(1234.0, value)
        self.assertEquals('float', dataType)
        [value, dataType] = base.StringUtils.toFloatAndType('987654321.0')
        self.assertEquals(987654321.0, value)
        self.assertEquals('float', dataType)
        [value, dataType] = base.StringUtils.toFloatAndType('1.23E+44')
        self.assertEquals(1.23E+44, value)
        self.assertEquals('float', dataType)

    def testToFloatAndTypeError(self):
        [value, dataType] = base.StringUtils.toFloatAndType('host3')
        self.assertEquals('float (or int or date(time)) expected, found: host3', value)
        self.assertEquals('undef', dataType)

    def testToFloatDate(self):
        value = base.StringUtils.toFloat('2019.10.23')
        self.assertEquals(1571781600.0, value)
        value = base.StringUtils.toFloat('1970-01-01')
        self.assertEquals(-3600.0, value)

    def testToFloatTime(self):
        value = base.StringUtils.toFloat('01:02:03')
        self.assertEquals(1*3600+2*60+3, value)
        value = base.StringUtils.toFloat('2:17')
        self.assertEquals(2*3600+17*60, value)

    def testToFloatDateTime(self):
        value = base.StringUtils.toFloat('2019.10.23T01:02:03')
        self.assertEquals(1571785323.0, value)
        value = base.StringUtils.toFloat('1970-01-02 5:17')
        self.assertEquals(101820.0, value)

    def testToFloatHex(self):
        value = base.StringUtils.toFloat('0x1234')
        self.assertEquals(float(0x1234), value)
        value = base.StringUtils.toFloat('0XABCDEF0123456')
        self.assertEquals(float(0xABCDEF0123456), value)
        value = base.StringUtils.toFloat('0Xabcdef0')
        self.assertEquals(float(0xABCDEF0), value)

    def testToFloatOct(self):
        value = base.StringUtils.toFloat('01234')
        self.assertEquals(float(0o1234), value)
        value = base.StringUtils.toFloat('012345670')
        self.assertEquals(float(0o12345670), value)

    def testToFloatInt(self):
        value = base.StringUtils.toFloat('1234')
        self.assertEquals(1234.0, value)
        value = base.StringUtils.toFloat('987654321')
        self.assertEquals(987654321.0, value)

    def testToFloatFloat(self):
        value = base.StringUtils.toFloat('1234.0')
        self.assertEquals(1234.0, value)
        value = base.StringUtils.toFloat('987654321.0')
        self.assertEquals(987654321.0, value)
        value = base.StringUtils.toFloat('1.23E+44')
        self.assertEquals(1.23E+44, value)

    def testToFloatError(self):
        value = base.StringUtils.toFloat('host3')
        self.assertEquals('float (or int or date(time)) expected, found: host3', value)

    def testAsInt(self):
        self.assertEquals(321, base.StringUtils.asInt('321'))
        self.assertEquals(0x321, base.StringUtils.asInt('0x321'))
        self.assertEquals(0o321, base.StringUtils.asInt('0321'))
        self.assertEquals(-33, base.StringUtils.asInt('-33', 777))
        self.assertEquals(77, base.StringUtils.asInt('99x', 77))
        self.assertEquals(777, base.StringUtils.asInt('x2', 777))

    def testRegExprCompile(self):
        rexpr = base.StringUtils.regExprCompile('\d', None, None, True)
        self.assertNotNone(rexpr.match('7'))
        rexpr = base.StringUtils.regExprCompile('Hi', None, None, False)
        self.assertNotNone(rexpr.match('hi'))

    def testRegExprCompileError(self):
        rexpr = base.StringUtils.regExprCompile('*.txt', 'test of wrong pattern', self._logger)
        self.assertNone(rexpr)
        self._logger.contains('error in regular expression in test of wrong pattern: nothing to repeat at position 0')
        rexpr = base.StringUtils.regExprCompile('(*.txt', 'test of wrong pattern')
        self.assertNone(rexpr)

    def testMinimizeArrayUtfError(self):
        list1 = [b'\xffabcdefghijklmnopqrstuvwxyz01234567890', b'abcdefghijklmnopqrstuvwxyz01234567890\xff']
        rc = base.StringUtils.minimizeArrayUtfError(list1, self._logger)
        self.assertEquals(2, len(rc))
        self.assertEquals(1, rc[0].find('abcdefghijklmnopqrstuvwxyz01234567890'))
        self.assertEquals(0, rc[1].find('abcdefghijklmnopqrstuvwxyz01234567890'))

    def testStringOption(self):
        self.assertEquals('', base.StringUtils.stringOption('a-b', 'c', '--a-b'))
        self.assertEquals('TrUe', base.StringUtils.stringOption('a-b', 'c', '--a-b=TrUe'))
        self.assertEquals('TrUe', base.StringUtils.stringOption('a-b', 'c', '-cTrUe'))
        self.assertNone(base.StringUtils.stringOption('a-b', 'c', '-CTrUe'))
        self.assertNone(base.StringUtils.stringOption('a-b', 'c', '-a-bc'))

    def testBoolOption(self):
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
        try:
            base.StringUtils.boolOption('a-b', 'c', '--a-b=blub')
            self.assertTrue(False)
        except:
            self.assertTrue(True)

    def testIntOption(self):
        self.assertEquals(34, base.StringUtils.intOption('a-b', 'c', '--a-b=34'))
        self.assertEquals(9, base.StringUtils.intOption('a-b', 'c', '-c9'))
        self.assertNone(base.StringUtils.boolOption('a-bc', 'd', '--ab=4'))
        self.assertNone(base.StringUtils.boolOption('a-bc', 'd', '-D99'))

    def testIntOptionError(self):
        try:
            base.StringUtils.intOption('a-b', 'c', '--a-b=34x')
            self.assertTrue(False)
        except:
            self.assertTrue(True)

    def testSecondsToString(self):
        self.assertEquals('00:00:00', base.StringUtils.secondsToString(0))
        self.assertEquals('03:04:15', base.StringUtils.secondsToString(3*3600+4*60+15))
        self.assertEquals('124:59:33', base.StringUtils.secondsToString(124*3600+59*60+33))

    def testPrivateConfig(self):
        config = base.StringUtils.privateConfig()
        self.assertEquals('xyz', config.getString('StringUtil.test.entry'))

    def testRegExprOption(self):
        regExpr = base.StringUtils.regExprOption('name', 'n', r'--name=^[a-z]+$')
        self.assertEquals("re.compile('^[a-z]+$', re.IGNORECASE)", str(regExpr))
        self.assertEquals('jonny', regExpr.match('jonny').group(0))
        self.assertNone(base.StringUtils.regExprOption('name', 'n', r'--iname=^[a-z]+$'))

    def testRegExprOptionError(self):
        self.assertEquals("not a regular expression in --name: --name=^[a-z+$", base.StringUtils.regExprOption('name', 'n', r'--name=^[a-z+$'))

    def testIndentLines(self):
        lines = '  abc\n  def'
        self.assertEquals(' abc\n def', base.StringUtils.indentLines(lines, 1))
        self.assertEquals('abc\ndef', base.StringUtils.indentLines(lines, 0))
        self.assertEquals('   abc\n   def', base.StringUtils.indentLines(lines, 3, ' '))
        self.assertEquals('\tabc\n\tdef', base.StringUtils.indentLines(lines, 1, '\t'))
        self.assertEquals('...abc\n...def', base.StringUtils.indentLines(lines, 1, '...'))

    def testLimitLength(self):
        self.assertEquals('abcd', base.StringUtils.limitLength('abcd', 4))
        self.assertEquals('a..', base.StringUtils.limitLength('abcd', 3))
        self.assertEquals('ab', base.StringUtils.limitLength('ab..', 2))
        self.assertEquals('a', base.StringUtils.limitLength('ab..', 1))
        self.assertEquals('', base.StringUtils.limitLength('abcd', 0))

    def testLimitLength2(self):
        self.assertEquals('ab..cd', base.StringUtils.limitLength2('ab1234cd', 6))
        self.assertEquals('ab..cd', base.StringUtils.limitLength2('ab12345cd', 6))
        self.assertEquals('a..cd', base.StringUtils.limitLength2('ab1234cd', 5))
        self.assertEquals('a..cd', base.StringUtils.limitLength2('ab12345cd', 5))
        self.assertEquals('abcd', base.StringUtils.limitLength2('abcd', 4))
        self.assertEquals('acd', base.StringUtils.limitLength2('abcd', 3))
        self.assertEquals('ad', base.StringUtils.limitLength2('abcd', 2))
        self.assertEquals('d', base.StringUtils.limitLength2('abcd', 1))
        self.assertEquals('', base.StringUtils.limitLength2('abcd', 0))

if __name__ == '__main__':
    #import sys;sys.argv = ['', 'Test.testName']
    tester = StringUtilsTest()
    tester.run()
