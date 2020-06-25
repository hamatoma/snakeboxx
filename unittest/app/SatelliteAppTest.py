'''
Created on 12.04.2018

@author: hm
'''
from unittest.UnitTestCase import UnitTestCase

import shutil
import os

import app.BaseApp
import app.SatelliteApp
import base.StringUtils

debug = False

class SatelliteAppTest(UnitTestCase):
    def __init__(self):
        UnitTestCase.__init__(self)
        app.BaseApp.BaseApp.setUnderTest(True)
        self._finish()
        self._createConfig()

    def _createConfig(self):
        self._configFile = self.tempFile('satellite.conf', 'unittest', 'satboxx')
        base.StringUtils.toFile(self._configFile, '''# created by SatelliteApp
wdfiller.active=true
wdfiller.url=https://wiki.hamatoma.de
# separator ' ': possible modes cloud filesystem stress
wdfiller.kinds=cloud
# interval between 2 send actions in seconds
wdfiller.cloud.interval=2
wdfiller.cloud.directory=/opt/clouds
wdfiller.cloud.excluded=cloud.test|cloud.huber.de
wdfiller.filesystem.interval=2
wdfiller.filesystem.devices=sda6|
wdfiller.stress.interval=2
hostname=testhost
''')
        self._configDir = os.path.dirname(self._configFile)

    def _finish(self):
        shutil.rmtree(self.tempDir('unittest'))

    def testInstall(self):
        if debug: return
        app.SatelliteApp.main(['-v3', '--test-target=' + self._configDir, '--test-source=' + self._configDir, '-c' + self._configDir,
            'install', 'satboxx'
            ])
        application = app.BaseApp.BaseApp.lastInstance()
        self.assertEquals(0, application._logger._errors)
        self.assertFileContent('''[Unit]
Description=satboxx: sends data via REST to servers.
After=syslog.target
[Service]
Type=simple
User=satboxx
Group=satboxx
WorkingDirectory=/etc/snakeboxx
#EnvironmentFile=-/etc/snakeboxx/satboxx.env
ExecStart=/usr/local/bin/satboxx daemon satboxx satboxx
ExecReload=/usr/local/bin/satboxx reload satboxx satboxx
SyslogIdentifier=satboxx
StandardOutput=syslog
StandardError=syslog
Restart=always
RestartSec=3
[Install]
WantedBy=multi-user.target
''', self._configDir + os.sep + 'satboxx.service')
        fn = self._configDir + os.sep + 'satellite.conf'
        self.assertFileExists(fn)
        self.assertFileContent('''# created by SatelliteApp
wdfiller.active=true
wdfiller.url=https://wiki.hamatoma.de
# separator ' ': possible modes cloud filesystem stress
wdfiller.kinds=cloud
# interval between 2 send actions in seconds
wdfiller.cloud.interval=2
wdfiller.cloud.directory=/opt/clouds
wdfiller.cloud.excluded=cloud.test|cloud.huber.de
wdfiller.filesystem.interval=2
wdfiller.filesystem.devices=sda6|
wdfiller.stress.interval=2
hostname=testhost
''', fn)

    def testUninstall(self):
        if debug: return
        base.FileHelper.clearDirectory(self._configDir)
        fnService = self._configDir + os.sep + 'satboxx.service'
        fnApp = self._configDir + os.sep + 'satboxx'
        base.StringUtils.toFile(fnService, 'service...')
        base.StringUtils.toFile(fnApp, 'application')
        app.SatelliteApp.main(['-v3', '--test-target=' + self._configDir, '--test-source=' + self._configDir, '-c' + self._configDir,
            'uninstall', '--service=satboxx'
            ])
        email = app.BaseApp.BaseApp.lastInstance()
        self.assertEquals(0, email._logger._errors)
        self.assertFileNotExists(fnService)
        self.assertFileNotExists(fnApp)

    def testHelp(self):
        if debug: return
        app.SatelliteApp.main(['-v3',
            'help', 'help'
            ])
        application = app.BaseApp.BaseApp.lastInstance()
        self.assertEquals(0, application._logger._errors)
        self.assertEquals('''satboxx <global-opts> <mode> [<opts>]
  Sends data via REST to some servers. Possible servers are WebDashFiller and Monitor.
<mode>:
  help [<pattern-mode> [<pattern-submode>]]
    Prints a description of the application
    <pattern-mode>
      if given: each mode is listed if the pattern matches
    <pattern-submode>:
      if given: only submodes are listed if this pattern matches
Examples:
satboxx help
satboxx help help sub''', application._resultText)

    def testReload(self):
        if debug: return
        self._logger.log('=== expecting 1 error...')
        app.SatelliteApp.main(['-v3',
            'reload', 'satboxx'
            ])
        application = app.BaseApp.BaseApp.lastInstance()
        self.assertEquals(1, application._logger._errors)
        self.assertTrue(application._logger._firstErrors[0].find('not processed') > 0)

    def testDaemon(self):
        if debug: return
        self._createConfig()
        self._logger.log('=== expecting 4 errors...')
        app.SatelliteApp.main(['-v3', '-c' + self._configDir, '--test-target=' + self._configDir,
            'daemon', 'satboxx', 'satboxx', '--count=1', '--interval=2'
            ])
        application = app.BaseApp.BaseApp.lastInstance()
        self.assertEquals(4, application._logger._errors)
        for item in application._logger._firstErrors:
            self.assertMatches(r'status 405 \[Not Allowed\]', item)

    def testReloadRequest(self):
        if debug: return
        app.SatelliteApp.main(['-v3',
            'reload', 'satboxx'
            ])
        application = app.BaseApp.BaseApp.lastInstance()
        self.assertEquals(1, application._logger._errors)
        self.assertEquals('reload request was not processed', application._logger._firstErrors[0])

    def testTestFilesystem(self):
        #if debug: return
        fn = self.tempFile('reload.request', 'satboxx')
        base.StringUtils.toFile(fn, '')
        app.SatelliteApp.main(['-v3',
            'test', 'fs', '2', '2'
            ])
        application = app.BaseApp.BaseApp.lastInstance()
        self.assertEquals(6, application._logger._errors)

if __name__ == '__main__':
    # import sys;sys.argv = ['', 'Test.testName']
    tester = SatelliteAppTest()
    tester.run()
