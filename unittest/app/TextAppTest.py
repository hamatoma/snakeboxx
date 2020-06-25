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

debug = False

class TextAppTest(UnitTestCase):
    def __init__(self):
        UnitTestCase.__init__(self)
        app.BaseApp.BaseApp.setUnderTest(True)
        self._finish()
        self._createConfig()

    def _createConfig(self):
        self._configFile = self.tempFile('satellite.conf', 'unittest.txt', 'textboxx')
        self._configDir = os.path.dirname(self._configFile)
        self._logFile = self._configDir + os.sep + 'test.log';
        base.StringUtils.toFile(self._configFile, '''# created by TextApp
logger={}
'''.format(self._logFile))

    def _finish(self):
        shutil.rmtree(self.tempDir('unittest.txt'))

    def testInstall(self):
        if debug: return
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
        if debug: return
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
        if debug: return
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
        if debug: return
        fn =  self.tempFile('exec.test', 'execrules');
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
        if debug: return
        app.TextApp.main(['-v3',
            'csv-describe'
            ])
        application = app.BaseApp.BaseApp.lastInstance()
        self.assertEquals(0, application._logger._errors)

    def testCsvExecute(self):
        if debug: return
        fn =  self.tempFile('test.csv', 'csv');
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
        #if debug: return
        fn =  self.tempFile('exec.test', 'execrules');
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

if __name__ == '__main__':
    # import sys;sys.argv = ['', 'Test.testName']
    tester = TextAppTest()
    tester.run()
