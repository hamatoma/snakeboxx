'''
Created on 12.04.2018

@author: hm
'''
from unittest.UnitTestCase import UnitTestCase

import shutil
import os

import app.BaseApp
import app.OperatingSystemApp
import base.StringUtils

DEBUG = False

class OperatingSystemAppTest(UnitTestCase):
    def __init__(self):
        UnitTestCase.__init__(self)
        app.BaseApp.BaseApp.setUnderTest(True)
        self._finish()
        self._createConfig()

    def debugFlag(self):
        base.StringUtils.avoidWarning(self)
        return DEBUG

    def _createConfig(self):
        self._configFile = self.tempFile('satellite.conf', 'unittest.os', 'osboxx')
        self._configDir = os.path.dirname(self._configFile)
        self._logFile = os.path.join(self._configDir, 'test.log')
        base.StringUtils.toFile(self._configFile, '''# created by OperatingSystemApp
logger={}
'''.format(self._logFile))

    def _finish(self):
        shutil.rmtree(self.tempDir('unittest.os'))

    def testInstall(self):
        if DEBUG: return
        app.OperatingSystemApp.main(['-v3', f'--dir-unittest={self._configDir}', f'-c{self._configDir}',
            'install', 'osboxx'
            ])
        application = app.BaseApp.BaseApp.lastInstance()
        self.assertIsEqual(0, application._logger._errors)
        fn = self._configDir + os.sep + 'operatingsystem.conf'
        self.assertFileExists(fn)
        self.assertFileContent('''# created by OperatingSystemApp
logfile=/var/log/local/osboxx.log
'''.format(), fn)

    def testUninstall(self):
        if DEBUG: return
        base.FileHelper.clearDirectory(self._configDir)
        fnApp = os.path.join(self._configDir, 'bin/osboxx')
        base.StringUtils.toFile(fnApp, 'application', ensureParent=True)
        app.OperatingSystemApp.main(['-v3', f'--dir-unittest={self._configDir}', f'-c{self._configDir}',
            'uninstall', '--service=osboxx'
            ])
        email = app.BaseApp.BaseApp.lastInstance()
        self.assertIsEqual(0, email._logger._errors)
        self.assertFileNotExists(fnApp)

    def testHelp(self):
        if DEBUG: return
        app.OperatingSystemApp.main(['-v3',
            'help', 'help'
            ])
        application = app.BaseApp.BaseApp.lastInstance()
        self.assertIsEqual(0, application._logger._errors)
        self.assertIsEqual('''osboxx <global-opts> <mode> [<opts>]
  Offers service round about the operating system.
<mode>:
  help [<pattern-mode> [<pattern-submode>]]
    Prints a description of the application
    <pattern-mode>
      if given: each mode is listed if the pattern matches
    <pattern-submode>:
      if given: only submodes are listed if this pattern matches
Examples:
osboxx help
osboxx help help sub
''', application._resultText)

    def testTestAuthFile(self):
        if DEBUG: return
        fnPublic = '/tmp/public.keys'
        base.StringUtils.toFile(fnPublic, '''ssh-rsa AAAAB3NIH...DnrEn09rg593stn/hm0blnUDBCr8AEZIj hm@caribou
command="/usr/local/bin/rrsync /tmp",no-X11-forwarding ssh-rsa AABCEDON9999248X...TeLwGVjM1XTw== exttmp@dragon
''')
        home = self._configDir + '/home/bupsupply'
        base.FileHelper.ensureDirectory(home)
        fnAuth = home + '/.ssh/authorized_keys'
        app.OperatingSystemApp.main(['-v3', f'--dir-unittest={self._configDir}',
            'auth-keys', 'bupsupply'
            ])
        application = app.BaseApp.BaseApp.lastInstance()
        self.assertIsEqual(0, application._logger._errors)
        content = base.StringUtils.fromFile(fnAuth)
        self.assertIsEqual('''ssh-rsa AAAAB3NIH...DnrEn09rg593stn/hm0blnUDBCr8AEZIj hm@caribou
command="/usr/local/bin/rrsync /tmp",no-X11-forwarding ssh-rsa AABCEDON9999248X...TeLwGVjM1XTw== exttmp@dragon
''', content)
        fnPublic2 = '/tmp/public2.keys'
        base.StringUtils.toFile(fnPublic2, '''ssh-rsa AAAAB3NIH...DnrEn09rg593stn/hm0blnUDBCr8AEZIj hm@caribou
ssh-rsa ACXART9IH...DnrEn09rg593stn/hm0blnUDBCr8AEZIj jonny@thor
command="/usr/local/bin/rrsync /tmp",no-X11-forwarding ssh-rsa AAAAB3NzaC1yc2EA...TeLwGVjM1XTw== exttmp@caribou
command="/usr/local/bin/rrsync /tmp",no-X11-forwarding ssh-rsa AABCEDON9999248X...TeLwGVjM1XTw== exttmp@dragon
''')
        base.FileHelper.ensureDirectory(self._configDir + '/bupsupply')
        app.OperatingSystemApp.main(['-v3', f'--dir-unittest={self._configDir}',
            'auth-keys', 'bupsupply', r'--filter=\@caribou', fnPublic2
            ])
        application = app.BaseApp.BaseApp.lastInstance()
        self.assertIsEqual(0, application._logger._errors)
        content = base.StringUtils.fromFile(fnAuth)
        self.assertIsEqual('''ssh-rsa AAAAB3NIH...DnrEn09rg593stn/hm0blnUDBCr8AEZIj hm@caribou
command="/usr/local/bin/rrsync /tmp",no-X11-forwarding ssh-rsa AABCEDON9999248X...TeLwGVjM1XTw== exttmp@dragon
command="/usr/local/bin/rrsync /tmp",no-X11-forwarding ssh-rsa AAAAB3NzaC1yc2EA...TeLwGVjM1XTw== exttmp@caribou
''', content)

if __name__ == '__main__':
    # import sys;sys.argv = ['', 'Test.testName']
    tester = OperatingSystemAppTest()
    tester.run()
