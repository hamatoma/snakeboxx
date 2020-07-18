'''
Created on 12.04.2018

@author: hm
'''
from unittest.UnitTestCase import UnitTestCase

import shutil
import os

import app.BaseApp
import app.DirApp
import base.StringUtils

debug = False

class DirAppTest(UnitTestCase):
    def __init__(self):
        UnitTestCase.__init__(self)
        app.BaseApp.BaseApp.setUnderTest(True)
        self._baseDir = self.tempDir('src', 'unittest.dir')
        self._finish()
        self._createConfig()

    def _createConfig(self):
        self._configFile = self.tempFile('dirapp.conf', 'unittest.dir', 'dirboxx')
        self._configDir = os.path.dirname(self._configFile)
        self._logFile = self._configDir + os.sep + 'test.log';
        base.StringUtils.toFile(self._configFile, '''# created by DirApp
logger={}
'''.format(self._logFile))

    def _finish(self):
        shutil.rmtree(self.tempDir('unittest.dir'))

    def testInstall(self):
        if debug: return
        app.DirApp.main(['-v3', '--test-target=' + self._configDir, '--test-source=' + self._configDir, '-c' + self._configDir,
            'install', 'osboxx'
            ])
        application = app.BaseApp.BaseApp.lastInstance()
        self.assertEquals(0, application._logger._errors)
        fn = self._configDir + os.sep + 'text.conf'
        self.assertFileExists(fn)
        self.assertFileContent('''# created by DirApp
logfile=/var/log/local/dirboxx.log
'''.format(), fn)

    def testUninstall(self):
        if debug: return
        base.FileHelper.clearDirectory(self._configDir)
        fnApp = self._configDir + os.sep + 'dirboxx'
        base.StringUtils.toFile(fnApp, 'application')
        app.DirApp.main(['-v3', '--test-target=' + self._configDir, '--test-source=' + self._configDir, '-c' + self._configDir,
            'uninstall', '--service=dirboxx'
            ])
        email = app.BaseApp.BaseApp.lastInstance()
        self.assertEquals(0, email._logger._errors)
        self.assertFileNotExists(fnApp)

    def testHelp(self):
        if debug: return
        app.DirApp.main(['-v3',
            'help', 'help'
            ])
        application = app.BaseApp.BaseApp.lastInstance()
        self.assertEquals(0, application._logger._errors)
        self.assertEquals('''dirboxx <global-opts> <mode> [<options>]
  Searching and modifying in text files.
<mode>:
  help [<pattern-mode> [<pattern-submode>]]
    Prints a description of the application
    <pattern-mode>
      if given: each mode is listed if the pattern matches
    <pattern-submode>:
      if given: only submodes are listed if this pattern matches
Examples:
dirboxx help
dirboxx help help sub
''', application._resultText)

    def testExtrema(self):
        if debug: return
        base.FileHelper.createFileTree('''file1.txt|this is in file 123456|664|2020-01-22 02:44:32
dir1/file2.txt|this is in file 1|664|2020-01-29 02:44:32
dir1/file3.txt|this is in file 123456789|664|2020-01-23 02:44:32
dir2/file4.txt|this is|123|2020-01-20 02:44:32
file5.txt|this is|664|2020-01-25 02:44:32
file6.txt||664|2020-01-23 02:44:32
dir2/file7.txt|Wow!|664|2020-02-23 02:44:32
dir1/file8.txt||664|2020-02-29 02:44:32
''', self._baseDir)
        app.DirApp.main(['-v3',
            'extrema', 'all', '--count=3', '--min-length=1', '--file-type=f', self._baseDir
            ])
        application = app.BaseApp.BaseApp.lastInstance()
        self.assertEquals(0, application._logger._errors)
        self.assertEquals('''dir(s): 3 file(s): 8 / 82 Byte
ignored: dir(s): 0 file(s): 0
== the oldest files:
2020.01.20 02:44:32       7 Byte /tmp/unittest.dir/src/dir2/file4.txt
2020.01.22 02:44:32      22 Byte /tmp/unittest.dir/src/file1.txt
2020.01.23 02:44:32       0 Byte /tmp/unittest.dir/src/file6.txt
== the smallest files:
      4 Byte 2020.02.23 02:44:32 /tmp/unittest.dir/src/dir2/file7.txt
      7 Byte 2020.01.25 02:44:32 /tmp/unittest.dir/src/file5.txt
      7 Byte 2020.01.20 02:44:32 /tmp/unittest.dir/src/dir2/file4.txt
== the youngest files:
2020.02.29 02:44:32       0 Byte /tmp/unittest.dir/src/dir1/file8.txt
2020.02.23 02:44:32       4 Byte /tmp/unittest.dir/src/dir2/file7.txt
2020.01.29 02:44:32      17 Byte /tmp/unittest.dir/src/dir1/file2.txt
== the largest files:
     25 Byte 2020.01.23 02:44:32 /tmp/unittest.dir/src/dir1/file3.txt
     22 Byte 2020.01.22 02:44:32 /tmp/unittest.dir/src/file1.txt
     17 Byte 2020.01.29 02:44:32 /tmp/unittest.dir/src/dir1/file2.txt
''', '\n'.join(application._resultLines))

if __name__ == '__main__':
    # import sys;sys.argv = ['', 'Test.testName']
    tester = DirAppTest()
    tester.run()
