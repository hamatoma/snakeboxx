'''
Created on 12.04.2018

@author: hm
'''
from unittest.UnitTestCase import UnitTestCase

import shutil
import os

import app.BaseApp
import app.TextApp
import base.StringUtils

DEBUG = False


class TextAppTest(UnitTestCase):
    def __init__(self):
        UnitTestCase.__init__(self)
        app.BaseApp.BaseApp.setUnderTest(True)
        self._finish()
        self._createConfig()

    def debugFlag(self):
        base.StringUtils.avoidWarning(self)
        return DEBUG

    def _createConfig(self):
        self._configFile = self.tempFile(
            'satellite.conf', 'unittest.txt', 'textboxx')
        self._configDir = os.path.dirname(self._configFile)
        self._logFile = self._configDir + os.sep + 'test.log'
        base.StringUtils.toFile(self._configFile, '''# created by TextApp
logger={}
'''.format(self._logFile))

    def _finish(self):
        shutil.rmtree(self.tempDir('unittest.txt'))

    def testInstall(self):
        if DEBUG:
            return
        app.TextApp.main(['-v3', '--test-target=' + self._configDir, '--test-source=' + self._configDir, '-c' + self._configDir,
                          'install', 'osboxx'
                          ])
        application = app.BaseApp.BaseApp.lastInstance()
        self.assertIsEqual(0, application._logger._errors)
        fn = self._configDir + os.sep + 'text.conf'
        self.assertFileExists(fn)
        self.assertFileContent('''# created by TextApp
logfile=/var/log/local/textboxx.log
'''.format(), fn)

    def testUninstall(self):
        if DEBUG:
            return
        base.FileHelper.clearDirectory(self._configDir)
        fnApp = self._configDir + os.sep + 'textboxx'
        base.StringUtils.toFile(fnApp, 'application')
        app.TextApp.main(['-v3', '--test-target=' + self._configDir, '--test-source=' + self._configDir, '-c' + self._configDir,
                          'uninstall', '--service=textboxx'
                          ])
        email = app.BaseApp.BaseApp.lastInstance()
        self.assertIsEqual(0, email._logger._errors)
        self.assertFileNotExists(fnApp)

    def testHelp(self):
        if DEBUG:
            return
        app.TextApp.main(['-v3',
                          'help', 'help'
                          ])
        application = app.BaseApp.BaseApp.lastInstance()
        self.assertIsEqual(0, application._logger._errors)
        self.assertIsEqual('''textboxx <global-opts> <mode> [<opts>]
  Searching and modifying in text files.
<mode>:
  help [<pattern-mode> [<pattern-submode>]]
    Prints a description of the application
    <pattern-mode>
      if given: each mode is listed if the pattern matches
    <pattern-submode>:
      if given: only submodes are listed if this pattern matches
Examples:
textboxx help
textboxx help help sub
''', application._resultText)

    def testExecRules(self):
        if DEBUG:
            return
        fn = self.tempFile('exec.test', 'execrules')
        base.StringUtils.toFile(fn, '''abc
xy123
def''')
        app.TextApp.main(['-v3',
                          'exec-rules', '>/2/', fn
                          ])
        application = app.BaseApp.BaseApp.lastInstance()
        self.assertIsEqual(0, application._logger._errors)
        state = application._processor._lastState
        self.assertIsEqual(1, state._cursor._line)
        self.assertIsEqual(3, state._cursor._col)

    def testCsvDescribe(self):
        if DEBUG:
            return
        app.TextApp.main(['-v3',
                          'csv-describe'
                          ])
        application = app.BaseApp.BaseApp.lastInstance()
        self.assertIsEqual(0, application._logger._errors)

    def testCsvExecute(self):
        if DEBUG:
            return
        fn = self.tempFile('test.csv', 'csv')
        base.StringUtils.toFile(fn, '''id,name
1,jonny
2,eve
''')
        app.TextApp.main(['-v3',
                          'csv-execute', 'info:summary', fn
                          ])
        application = app.BaseApp.BaseApp.lastInstance()
        self.assertIsEqual(0, application._logger._errors)

    def testExecRules2(self):
        if DEBUG:
            return
        fn = self.tempFile('exec.test', 'execrules')
        base.StringUtils.toFile(fn, '''abc
xy123
def''')
        app.TextApp.main(['-v3',
                          'exec-rules', '>/2/ </Y/i', fn
                          ])
        application = app.BaseApp.BaseApp.lastInstance()
        self.assertIsEqual(0, application._logger._errors)
        state = application._processor._lastState
        self.assertIsEqual(1, state._cursor._line)
        self.assertIsEqual(1, state._cursor._col)

    def testGrep(self):
        if DEBUG:
            return
        fn = self.tempFile('test1.txt', 'grep')
        base.StringUtils.toFile(fn, '''abc
xy123
def''')
        app.TextApp.main(['-v3',
                          'grep', r'\d+', fn
                          ])
        application = app.BaseApp.BaseApp.lastInstance()
        self.assertIsEqual(0, application._logger._errors)
        self.assertIsEqual(1, len(application._resultLines))
        self.assertMatches('test1.txt:xy123', application._resultLines[0])

    def testGrepFormat(self):
        if DEBUG:
            return
        fn = self.tempFile('test1.txt', 'grep')
        base.StringUtils.toFile(fn, '''abc
xy123
def''')
        app.TextApp.main(['-v3',
                          'grep', r'\d+', fn, '-f%%%T%# %0', '--format-line=%%%T%# %0', '-F== File %p %n%L', '--format-file=== File %p %n%L'
                          ])
        application = app.BaseApp.BaseApp.lastInstance()
        self.assertIsEqual(0, application._logger._errors)
        self.assertIsEqual(2, len(application._resultLines))
        self.assertMatches('== File \S+grep test1.txt\n',
                           application._resultLines[0])
        self.assertIsEqual('%\t2 123', application._resultLines[1])

    def testGrepIgnoreInvertLineNumber(self):
        if DEBUG:
            return
        fn = self.tempFile('test1.txt', 'grep')
        base.StringUtils.toFile(fn, '''abc
xy123
BCD''')
        app.TextApp.main(['-v3',
                          'grep', r'B', fn, '-v', '--invert-match', '-i', '--ignore-case', '-n', '--line-number'
                          ])
        application = app.BaseApp.BaseApp.lastInstance()
        self.assertIsEqual(0, application._logger._errors)
        self.assertIsEqual(1, len(application._resultLines))
        self.assertMatches('test1.txt-2:xy123', application._resultLines[0])

    def testGrepWordMatchOnly(self):
        if DEBUG:
            return
        fn = self.tempFile('test1.txt', 'grep')
        base.StringUtils.toFile(fn, '''ab.c
xy123
B._C.D''')
        app.TextApp.main(['-v3',
                          'grep', r'\w\w', fn, '-o', '-w', '-n', '--word-regexpr', '--only-matching'
                          ])
        application = app.BaseApp.BaseApp.lastInstance()
        self.assertIsEqual(0, application._logger._errors)
        self.assertIsEqual(2, len(application._resultLines))
        self.assertMatches('test1.txt-1:ab', application._resultLines[0])
        self.assertMatches('test1.txt-3:_C', application._resultLines[1])

    def testGrepAboveContext(self):
        # if DEBUG: return
        fn = self.tempFile('test1.txt', 'grep')
        base.StringUtils.toFile(fn, 'a\nb\nc\nd\ne\nf')
        app.TextApp.main(['-v3',
                          'grep', r'[abe]', fn, '-A1', '--above-context=1', '--line-number'
                          ])
        application = app.BaseApp.BaseApp.lastInstance()
        self.assertIsEqual(0, application._logger._errors)
        self.assertIsEqual(4, len(application._resultLines))
        self.assertMatches('test1.txt-1:a', application._resultLines[0])
        self.assertMatches('test1.txt-2:b', application._resultLines[1])
        self.assertMatches('test1.txt-4:d', application._resultLines[2])
        self.assertMatches('test1.txt-5:e', application._resultLines[3])

    def testGrepBelowContext(self):
        if DEBUG:
            return
        fn = self.tempFile('test1.txt', 'grep')
        base.StringUtils.toFile(fn, 'a\nb\nc\nd\ne\nf\ng')
        app.TextApp.main(['-v3',
                          'grep', r'[abef]', fn, '-B1', '--below-context=1', '--line-number'
                          ])
        application = app.BaseApp.BaseApp.lastInstance()
        self.assertIsEqual(0, application._logger._errors)
        self.assertIsEqual(6, len(application._resultLines))
        self.assertMatches('test1.txt-1:a', application._resultLines[0])
        self.assertMatches('test1.txt-2:b', application._resultLines[1])
        self.assertMatches('test1.txt-3:c', application._resultLines[2])
        self.assertMatches('test1.txt-5:e', application._resultLines[3])
        self.assertMatches('test1.txt-6:f', application._resultLines[4])
        self.assertMatches('test1.txt-7:g', application._resultLines[5])

    def testGrepBelowAboveContext(self):
        if DEBUG:
            return
        fn = self.tempFile('test1.txt', 'grep')
        base.StringUtils.toFile(fn, 'a\nb\nc\nd\ne\nf\ng')
        app.TextApp.main(['-v3',
                          'grep', r'[abf]', fn, '-C1', '--context=1', '--line-number'
                          ])
        application = app.BaseApp.BaseApp.lastInstance()
        self.assertIsEqual(0, application._logger._errors)
        self.assertIsEqual(6, len(application._resultLines))
        self.assertMatches('test1.txt-1:a', application._resultLines[0])
        self.assertMatches('test1.txt-2:b', application._resultLines[1])
        self.assertMatches('test1.txt-3:c', application._resultLines[2])
        self.assertMatches('test1.txt-5:e', application._resultLines[3])
        self.assertMatches('test1.txt-6:f', application._resultLines[4])
        self.assertMatches('test1.txt-7:g', application._resultLines[5])

    def testGrepAboveBelowChars(self):
        if DEBUG:
            return
        fn = self.tempFile('test1.txt', 'grep')
        base.StringUtils.toFile(fn, '''Version: 12.33
1.1+2*4.99
''')
        app.TextApp.main(['-v3',
                          'grep', r'\d+(\.\d+)?', fn, '-b1', '--bolow-chars=1', '--line-number', '-a2', '--above-chars=2', '-f%t'
                          ])
        application = app.BaseApp.BaseApp.lastInstance()
        self.assertIsEqual(0, application._logger._errors)
        self.assertIsEqual(4, len(application._resultLines))
        self.assertIsEqual(': 12.33', application._resultLines[0])
        self.assertIsEqual('1.1+', application._resultLines[1])
        self.assertIsEqual('1+2*', application._resultLines[2])
        self.assertIsEqual('2*4.99', application._resultLines[3])

    def testReplace(self):
        if DEBUG:
            return
        fn = self.tempFile('test1.txt', 'replace')
        base.StringUtils.toFile(fn, '''line 1
version: 12.33
bla bla
''')
        app.TextApp.main(['-v4',
                          'replace', r'Version: (\d+\.\d+)', 'V%1', fn, '-i', '-b%', '-B.bak', '--backup=.bak'
                          ])
        application = app.BaseApp.BaseApp.lastInstance()
        self.assertIsEqual(0, application._logger._errors)
        self.assertFileContent('''line 1
V12.33
bla bla
''', fn)
        self.assertFileExists(fn.replace('.txt', '.bak'))

    def testReplaceNotRegexpr(self):
        if DEBUG:
            return
        fn = self.tempFile('test2.txt', 'replace')
        base.StringUtils.toFile(fn, r'(\d+)')
        app.TextApp.main(['-v4',
                          'replace', r'(\d+)', '...', fn, '-R', '--not-regexpr'
                          ])
        application = app.BaseApp.BaseApp.lastInstance()
        self.assertIsEqual(0, application._logger._errors)
        self.assertFileContent('...', fn)

    def testReplaceString(self):
        if DEBUG:
            return
        app.TextApp.main(['-v4',
                          'replace-string', r'(Dirs|Files): (\d+)', '%2 %1', 'dirs: 3 files: 12', '-b%', '--ignore-case'
                          ])
        application = app.BaseApp.BaseApp.lastInstance()
        self.assertIsEqual(0, application._logger._errors)
        self.assertIsEqual('3 dirs 12 files', application._resultText)

    def testReplaceMany(self):
        if DEBUG: return
        fn = self.tempFile('test3.txt', 'replace')
        base.StringUtils.toFile(fn, r'''abc
a bcabc 11
 abc 1 a
''')
        fnData = self.tempFile('data.txt', 'replace')
        base.StringUtils.toFile(fnData, '''abc\tY
1\tXX
''')

        app.TextApp.main(['-v4',
                          'replace-many', fnData, fn
                          ])
        application = app.BaseApp.BaseApp.lastInstance()
        self.assertIsEqual(0, application._logger._errors)
        self.assertFileContent('''Y
a bcY XXXX
 Y XX a
''', fn)

    def testInsertOrReplace(self):
        # if DEBUG: return
        fn = self.tempFile('php.ini', 'replace')
        base.StringUtils.toFile(fn, r'''#
max_memory=2048M
# blub
''')
        app.TextApp.main(['-v4',
                          'insert-or-replace', r'^max_memory=', 'max_memory=1G', fn
                          ])
        application = app.BaseApp.BaseApp.lastInstance()
        self.assertIsEqual(0, application._logger._errors)
        self.assertFileContent('''#
max_memory=1G
# blub
''', fn)

if __name__ == '__main__':
    # import sys;sys.argv = ['', 'Test.testName']
    tester = TextAppTest()
    tester.run()
