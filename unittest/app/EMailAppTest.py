'''
Created on 12.04.2018

@author: hm
'''
from unittest.UnitTestCase import UnitTestCase

import shutil
import os

import app.BaseApp
import app.EMailApp
import base.StringUtils

DEBUG = False

def usage(msg=None):
    base.StringUtils.avoidWarning(msg)
    return 'test usage'

class EMailAppTest(UnitTestCase):
    def __init__(self):
        UnitTestCase.__init__(self)
        app.BaseApp.BaseApp.setUnderTest(True)
        self._finish()
        self._configFile = self.tempFile('email.conf', 'unittest', 'etc')
        self._configDir = os.path.dirname(self._configFile)

    def _finish(self):
        shutil.rmtree(self.tempDir('unittest'))

    def debugFlag(self):
        base.StringUtils.avoidWarning(self)
        return DEBUG

    def testSend(self):
        if DEBUG: return
        app.EMailApp.main(['-v3',
            'send',
            'test@hamatoma.de',
            'testSend', '12345679 123456789 123456789'])
        #    'testSend', 'unittest EMailTest.testSend()'])
        #application = app.BaseApp.BaseApp.lastInstance()
        #self.assertIsEqual(self._fn2, email.result())

    def testInstall(self):
        if DEBUG: return
        app.EMailApp.main(['-v3', f'--dir-unittest={self._configDir}', f'-c{self._configDir}',
            'install', 'emailboxx'
            ])
        application = app.BaseApp.BaseApp.lastInstance()
        self.assertIsEqual(0, application._logger._errors)
        self.assertFileContent('''[Unit]
Description=Offers an email send service.
After=syslog.target
[Service]
Type=simple
User=emailboxx
Group=emailboxx
WorkingDirectory=/etc/snakeboxx
#EnvironmentFile=-/etc/snakeboxx/emailboxx.env
ExecStart=/usr/local/bin/emailboxx daemon emailboxx emailboxx
ExecReload=/usr/local/bin/emailboxx reload emailboxx emailboxx
SyslogIdentifier=emailboxx
StandardOutput=syslog
StandardError=syslog
Restart=always
RestartSec=3
[Install]
WantedBy=multi-user.target
''', os.path.join(self._configDir, 'system/emailboxx.service'))
        self.assertFileExists(os.path.join(self._configDir, 'bin/emailboxx'))
        self.assertFileContent('''# created by EMailApp
smtp.host=smtp.gmx.de
smtp.port=587
smtp.user=hm.neutral@gmx.de
smtp.code=TopSecret
smtp.with.tls=True
sender=hm.neutral@gmx.de
# jobs should be written to this dir:
job.directory=/tmp/emailboxx/jobs
# files older than this amount of seconds will be deleted (in job.directory):
job.clean.interval=3600
''', self._configDir + os.sep + 'email.conf')

    def testUninstall(self):
        if DEBUG: return
        base.FileHelper.clearDirectory(self._configDir)
        fnService = os.path.join(self._configDir, 'system/emailboxx.service')
        fnApp = os.path.join(self._configDir, 'bin/emailboxx')
        base.StringUtils.toFile(fnService, 'service...', ensureParent=True)
        base.StringUtils.toFile(fnApp, 'app', ensureParent=True)
        app.EMailApp.main(['-v3', f'--dir-unittest={self._configDir}', '-c{self._configDir',
            'uninstall', '--service=emailboxx'
            ])
        application = app.BaseApp.BaseApp.lastInstance()
        self.assertIsEqual(0, application._logger._errors)
        self.assertFileNotExists(fnService)
        self.assertFileNotExists(fnApp)

    def testHelp(self):
        if DEBUG: return
        app.EMailApp.main(['-v3',
            'help', 'help'
            ])
        application = app.BaseApp.BaseApp.lastInstance()
        self.assertIsEqual(0, application._logger._errors)
        self.assertIsEqual('''emailboxx <global-opts> <mode> [<opts>]
  Offers email services.
<mode>:
  help [<pattern-mode> [<pattern-submode>]]
    Prints a description of the application
    <pattern-mode>
      if given: each mode is listed if the pattern matches
    <pattern-submode>:
      if given: only submodes are listed if this pattern matches
Examples:
emailboxx help
emailboxx help help sub''', application._resultText)

    def testReload(self):
        if DEBUG: return
        self._logger.log('@tester: /tmp/emailboxx must have rwx rights')
        app.EMailApp.main(['-v4', '--log-file=',
            'reload', 'emailboxx'
            ])
        application = app.BaseApp.BaseApp.lastInstance()
        self.assertIsEqual(1, application._logger._errors)
        self.assertIsEqual('reload request was not processed', application._logger._firstErrors[0])
        if os.path.exists('/tmp/reload.emailboxx.request'):
            self.assertTrue(True)
        else:
            self.assertTrue(application._logger.contains('removing /tmp/emailboxx/reload.request'))

    def testDaemon(self):
        if DEBUG: return
        self._logger.log('@tester: ensure rw permission for <temp>/emailboxx/jobs')
        directory = self.tempDir('jobs', 'emailboxx')
        base.JobController.JobController.writeJob('test', ['test@hamatoma.de'], directory, self._logger)
        app.EMailApp.main(['-v3',
            'daemon', 'emailboxx', 'emailboxx'
            ])
        application = app.BaseApp.BaseApp.lastInstance()
        self.assertIsEqual(0, application._logger._errors)

    def testReloadRequest(self):
        if DEBUG: return
        self._logger.log('@precondition: ensure write permission on <tmp>/emailboxx/')
        self._logger.log('expecting 1 trial with no success...')
        app.EMailApp.main(['-v3',
            'reload', 'emailboxx'
            ])
        application = app.BaseApp.BaseApp.lastInstance()
        self.assertIsEqual(1, application._logger._errors)
        self.assertIsEqual('reload request was not processed', application._logger._firstErrors[0])

    def testHandleReloadRequest(self):
        if DEBUG: return
        fn = self.tempFile('reload.request', 'emailboxx')
        base.StringUtils.toFile(fn, '')
        app.EMailApp.main(['-v3',
            'daemon', 'emailboxx', 'emailboxx'
            ])
        application = app.BaseApp.BaseApp.lastInstance()
        self.assertIsEqual(0, application._logger._errors)
        self.assertFileNotExists(fn)

if __name__ == '__main__':
    # import sys;sys.argv = ['', 'Test.testName']
    tester = EMailAppTest()
    tester.run()
