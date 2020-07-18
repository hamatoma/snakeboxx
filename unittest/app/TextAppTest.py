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

    def _createConfig(self):
        self._configFile = self.tempFile('satellite.conf', 'unittest.txt', 'textboxx')
        self._configDir = os.path.dirname(self._configFile)
        self._logFile = self._configDir + os.sep + 'test.log'
        base.StringUtils.toFile(self._configFile, '''# created by TextApp
logger={}
'''.format(self._logFile))

    def _finish(self):
        shutil.rmtree(self.tempDir('unittest.txt'))

    def testInstall(self):
        if DEBUG: return
        app.TextApp.main(['-v3', '--test-target=' + self._configDir, '--test-source=' + self._configDir, '-c' + self._configDir,
            'install', 'osboxx'
            ])
        application = app.BaseApp.BaseApp.lastInstance()
        self.assertEquals(0, application._logger._errors)
        fn = self._configDir + os.sep + 'text.conf'
        self.assertFileExists(fn)
        self.assertFileContent('''# created by TextApp
logfile=/var/log/local/textboxx.log
'''.format(), fn)

    def testUninstall(self):
        if DEBUG: return
        base.FileHelper.clearDirectory(self._configDir)
        fnApp = self._configDir + os.sep + 'textboxx'
        base.StringUtils.toFile(fnApp, 'application')
        app.TextApp.main(['-v3', '--test-target=' + self._configDir, '--test-source=' + self._configDir, '-c' + self._configDir,
            'uninstall', '--service=textboxx'
            ])
        email = app.BaseApp.BaseApp.lastInstance()
        self.assertEquals(0, email._logger._errors)
        self.assertFileNotExists(fnApp)

    def testHelp(self):
        if DEBUG: return
        app.TextApp.main(['-v3',
            'help', 'help'
            ])
        application = app.BaseApp.BaseApp.lastInstance()
        self.assertEquals(0, application._logger._errors)
        self.assertEquals('''textboxx <global-opts> <mode> [<opts>]
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
        if DEBUG: return
        fn =  self.tempFile('exec.test', 'execrules')
        base.StringUtils.toFile(fn, '''abc
xy123
def''')
        app.TextApp.main(['-v3',
            'exec-rules', '>/2/', fn
            ])
        application = app.BaseApp.BaseApp.lastInstance()
        self.assertEquals(0, application._logger._errors)
        state = application._processor._lastState
        self.assertEquals(1, state._cursor._line)
        self.assertEquals(3, state._cursor._col)

    def testCsvDescribe(self):
        if DEBUG: return
        app.TextApp.main(['-v3',
            'csv-describe'
            ])
        application = app.BaseApp.BaseApp.lastInstance()
        self.assertEquals(0, application._logger._errors)

    def testCsvExecute(self):
        if DEBUG: return
        fn =  self.tempFile('test.csv', 'csv')
        base.StringUtils.toFile(fn, '''id,name
1,jonny
2,eve
''')
        app.TextApp.main(['-v3',
            'csv-execute', 'info:summary', fn
            ])
        application = app.BaseApp.BaseApp.lastInstance()
        self.assertEquals(0, application._logger._errors)

    def testExecRules2(self):
        if DEBUG: return
        fn =  self.tempFile('exec.test', 'execrules')
        base.StringUtils.toFile(fn, '''abc
xy123
def''')
        app.TextApp.main(['-v3',
            'exec-rules', '>/2/ </Y/i', fn
            ])
        application = app.BaseApp.BaseApp.lastInstance()
        self.assertEquals(0, application._logger._errors)
        state = application._processor._lastState
        self.assertEquals(1, state._cursor._line)
        self.assertEquals(1, state._cursor._col)

    def testGrep(self):
        if DEBUG: return
        fn =  self.tempFile('test1.txt', 'grep')
        base.StringUtils.toFile(fn, '''abc
xy123
def''')
        app.TextApp.main(['-v3',
            'grep', r'\d+', fn
            ])
        application = app.BaseApp.BaseApp.lastInstance()
        self.assertEquals(0, application._logger._errors)
        self.assertEquals(1, len(application._resultLines))
        self.assertMatches('test1.txt:xy123', application._resultLines[0])

    def testGrepFormat(self):
        if DEBUG: return
        fn =  self.tempFile('test1.txt', 'grep')
        base.StringUtils.toFile(fn, '''abc
xy123
def''')
        app.TextApp.main(['-v3',
            'grep', r'\d+', fn, '-f%%%T%# %0', '--format-line=%%%T%# %0', '-F== File %p %n%L', '--format-file=== File %p %n%L'
            ])
        application = app.BaseApp.BaseApp.lastInstance()
        self.assertEquals(0, application._logger._errors)
        self.assertEquals(2, len(application._resultLines))
        self.assertMatches('== File \S+grep test1.txt\n', application._resultLines[0])
        self.assertEquals('%\t2 123', application._resultLines[1])

    def testGrepIgnoreInvertLineNumber(self):
        if DEBUG: return
        fn =  self.tempFile('test1.txt', 'grep')
        base.StringUtils.toFile(fn, '''abc
xy123
BCD''')
        app.TextApp.main(['-v3',
            'grep', r'B', fn, '-v', '--invert-match', '-i', '--ignore-case', '-n', '--line-number'
            ])
        application = app.BaseApp.BaseApp.lastInstance()
        self.assertEquals(0, application._logger._errors)
        self.assertEquals(1, len(application._resultLines))
        self.assertMatches('test1.txt-2:xy123', application._resultLines[0])

    def testGrepWordMatchOnly(self):
        if DEBUG: return
        fn =  self.tempFile('test1.txt', 'grep')
        base.StringUtils.toFile(fn, '''ab.c
xy123
B._C.D''')
        app.TextApp.main(['-v3',
            'grep', r'\w\w', fn, '-o', '-w', '-n', '--word-regexpr', '--only-matching'
            ])
        application = app.BaseApp.BaseApp.lastInstance()
        self.assertEquals(0, application._logger._errors)
        self.assertEquals(2, len(application._resultLines))
        self.assertMatches('test1.txt-1:ab', application._resultLines[0])
        self.assertMatches('test1.txt-3:_C', application._resultLines[1])

    def testGrepBeforeContext(self):
        #if DEBUG: return
        fn =  self.tempFile('test1.txt', 'grep')
        base.StringUtils.toFile(fn, 'a\nb\nc\nd\ne\nf')
        app.TextApp.main(['-v3',
            'grep', r'[abe]', fn, '--before-context=1', '--line-number'
            ])
        application = app.BaseApp.BaseApp.lastInstance()
        self.assertEquals(0, application._logger._errors)
        self.assertEquals(4, len(application._resultLines))
        self.assertMatches('test1.txt-1:a', application._resultLines[0])
        self.assertMatches('test1.txt-2:b', application._resultLines[1])
        self.assertMatches('test1.txt-4:d', application._resultLines[2])
        self.assertMatches('test1.txt-5:e', application._resultLines[3])

    def testGrepBeforeContext(self):
        if DEBUG: return
        fn =  self.tempFile('test1.txt', 'grep')
        base.StringUtils.toFile(fn, 'a\nb\nc\nd\ne\nf')
        app.TextApp.main(['-v3',
            'grep', r'[abe]', fn, '-B1', '--before-context=1', '--line-number'
            ])
        application = app.BaseApp.BaseApp.lastInstance()
        self.assertEquals(0, application._logger._errors)
        self.assertEquals(4, len(application._resultLines))
        self.assertMatches('test1.txt-1:a', application._resultLines[0])
        self.assertMatches('test1.txt-2:b', application._resultLines[1])
        self.assertMatches('test1.txt-4:d', application._resultLines[2])
        self.assertMatches('test1.txt-5:e', application._resultLines[3])

    def testGrepAfterContext(self):
        if DEBUG: return
        fn =  self.tempFile('test1.txt', 'grep')
        base.StringUtils.toFile(fn, 'a\nb\nc\nd\ne\nf\ng')
        app.TextApp.main(['-v3',
            'grep', r'[abef]', fn, '-A1', '--after-context=1', '--line-number'
            ])
        application = app.BaseApp.BaseApp.lastInstance()
        self.assertEquals(0, application._logger._errors)
        self.assertEquals(6, len(application._resultLines))
        self.assertMatches('test1.txt-1:a', application._resultLines[0])
        self.assertMatches('test1.txt-2:b', application._resultLines[1])
        self.assertMatches('test1.txt-3:c', application._resultLines[2])
        self.assertMatches('test1.txt-5:e', application._resultLines[3])
        self.assertMatches('test1.txt-6:f', application._resultLines[4])
        self.assertMatches('test1.txt-7:g', application._resultLines[5])

    def testGrepBeforeAfterContext(self):
        if DEBUG: return
        fn =  self.tempFile('test1.txt', 'grep')
        base.StringUtils.toFile(fn, 'a\nb\nc\nd\ne\nf\ng')
        app.TextApp.main(['-v3',
            'grep', r'[abf]', fn, '-C1', '--context=1', '--line-number'
            ])
        application = app.BaseApp.BaseApp.lastInstance()
        self.assertEquals(0, application._logger._errors)
        self.assertEquals(6, len(application._resultLines))
        self.assertMatches('test1.txt-1:a', application._resultLines[0])
        self.assertMatches('test1.txt-2:b', application._resultLines[1])
        self.assertMatches('test1.txt-3:c', application._resultLines[2])
        self.assertMatches('test1.txt-5:e', application._resultLines[3])
        self.assertMatches('test1.txt-6:f', application._resultLines[4])
        self.assertMatches('test1.txt-7:g', application._resultLines[5])

    def testGrepBeforeAfterChars(self):
        if DEBUG: return
        fn =  self.tempFile('test1.txt', 'grep')
        base.StringUtils.toFile(fn, '''Version: 12.33
1.1+2*4.99
''')
        app.TextApp.main(['-v3',
            'grep', r'\d+(\.\d+)?', fn, '-a1', '--after-chars=1', '--line-number', '-b2', '--before-chars=2', '-f%t'
            ])
        application = app.BaseApp.BaseApp.lastInstance()
        self.assertEquals(0, application._logger._errors)
        self.assertEquals(4, len(application._resultLines))
        self.assertEquals(': 12.33', application._resultLines[0])
        self.assertEquals('1.1+', application._resultLines[1])
        self.assertEquals('1+2*', application._resultLines[2])
        self.assertEquals('2*4.99', application._resultLines[3])

if __name__ == '__main__':
    # import sys;sys.argv = ['', 'Test.testName']
    tester = TextAppTest()
    tester.run()
