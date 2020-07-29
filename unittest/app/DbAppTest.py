'''
Created on 12.04.2018

@author: hm
'''
from unittest.UnitTestCase import UnitTestCase

import shutil
import os

import app.BaseApp
import app.DbApp
import base.StringUtils

DEBUG = False


class DbAppTest(UnitTestCase):
    def __init__(self):
        UnitTestCase.__init__(self)
        app.BaseApp.BaseApp.setUnderTest(True)
        self._baseDir = self.tempDir('unittest.db')
        self._finish()
        self._createConfig()

    def debugFlag(self):
        base.StringUtils.avoidWarning(self)
        return DEBUG

    def _createConfig(self):
        self._configFile = self.tempFile(
            'dirapp.conf', 'dbboxx')
        self._configDir = os.path.dirname(self._configFile)
        self._logFile = os.path.join(self._configDir, 'test.log')
        base.StringUtils.toFile(self._configFile, f'''# created by DbApp
logger={self._logFile}
''')

    def _finish(self):
        if os.path.isdir(self._baseDir):
            shutil.rmtree(self._baseDir)

    def testInstall(self):
        if DEBUG:
            return
        app.DbApp.main(['-v3', '--dir-unittest=' + self._configDir, '-c' + self._configDir,
                        'install', 'osboxx'
                        ])
        application = app.BaseApp.BaseApp.lastInstance()
        self.assertIsEqual(0, application._logger._errors)
        fn = self._configDir + os.sep + 'db.conf'
        self.assertFileExists(fn)
        self.assertFileContent('''# created by DbApp
logfile=/var/log/local/dbboxx.log
admin.user=dbadm
admin.code=TopSecret
webapp.base=/srv/www
''', fn)

    def testUninstall(self):
        if DEBUG:
            return
        base.FileHelper.clearDirectory(self._configDir)
        fnApp = os.path.join(self._configDir, 'bin/dbboxx')
        base.StringUtils.toFile(fnApp, 'application', ensureParent=True)
        app.DbApp.main(['-v3', f'--dir-unittest={self._configDir}', f'-c{self._configDir}',
                        'uninstall'
                        ])
        application = app.BaseApp.BaseApp.lastInstance()
        self.assertIsEqual(0, application._logger._errors)
        self.assertFileNotExists(fnApp)

    def testHelp(self):
        if DEBUG:
            return
        app.DbApp.main(['-v3',
                        'help', 'help'
                        ])
        application = app.BaseApp.BaseApp.lastInstance()
        self.assertIsEqual(0, application._logger._errors)
        self.assertIsEqual('''dbboxx <global-opts> <mode> [<options>]
  Info and manipulation of mysql databases.
<mode>:
  help [<pattern-mode> [<pattern-submode>]]
    Prints a description of the application
    <pattern-mode>
      if given: each mode is listed if the pattern matches
    <pattern-submode>:
      if given: only submodes are listed if this pattern matches
Examples:
dbboxx help
dbboxx help help sub
''', application._resultText)


    def testHelpAll(self):
        if 'test'.startswith('test'): return
        if DEBUG: return
        app.DbApp.main(['-v3',
                        'help'
                        ])
        application = app.BaseApp.BaseApp.lastInstance()
        self.assertIsEqual(0, application._logger._errors)
        self.assertIsEqual('''dbboxx <global-opts> <mode> [<options>]
  Info and manipulation of mysql databases.
  <global-opt>:
  -c<dir> or --config-directory=<dir>
    the directory containing the configuration file
  -r or --run-time
    the runtime will be displayed at the end of the program
  --test-source=<dir>
    a directory used for unit tests
  --test-target=<dir>
    a directory used for unit tests
  -v<level> or --verbose-level=<level>
    sets the amount of logs: only log messages with a level <= <level> will be displayed
<mode>:
  all-dbs <opts>
    Lists all databases.
      <options>:
      --adm-name=<string> or -N=<string>:
        name of a db user with admin rights
      --adm-password=<string> or -P=<string>:
        password of the admin
      --internal-too or -i:
        the internal databases will be listed too
  build-config
    Creates a useful configuration file.
  dbboxx create-admin <name> <password> [<options>]
    Create a database user with admin rights.
      <options>:
      --adm-name=<string> or -N=<string>:
        name of a db user with admin rights
      --adm-password=<string> or -P=<string>:
        password of the admin
      --readonly or -r:
        the admin gets only read rights (e.g. for backup)
  dbboxx create-db-and-user <db> [<user> <password>] [<options>]
    Create a database and a user with rights to modify this db.
      <options>:
      --adm-name=<string> or -N=<string>:
        name of a db user with admin rights
      --adm-password=<string> or -P=<string>:
        password of the admin
  help [<pattern-mode> [<pattern-submode>]]
    Prints a description of the application
    <pattern-mode>
      if given: each mode is listed if the pattern matches
    <pattern-submode>:
      if given: only submodes are listed if this pattern matches
  install
    Installs the application.
  uninstall [--service=<servicename>]
    Removes the application.
  version
    Prints the version number.
Examples:
dbboxx -v3 -r list
dbboxx all-dbs
dbboxx all-dbs --admin=jonny --adm-password=ForgetNever
dbboxx build-config
dbboxx create-admin dbadm TopSecret
dbboxx create-admin dbadmin MoreSecret --admin=root --adm-password=ForgetNever
dbboxx create-db-and-user app dbadm TopSecret
dbboxx create-admin dbadmin MoreSecret --admin=root --adm-password=ForgetNever
dbboxx help
dbboxx help help sub
dbboxx install
dbboxx uninstall --service=emailboxx
dbboxx version
''', application._resultText)


    def testAllDbs(self):
        if DEBUG: return
        app.DbApp.main(['-v3',
                        'all-dbs'
                        ])
        application = app.BaseApp.BaseApp.lastInstance()
        self.assertIsEqual(0, application._logger._errors)
        current = '\n'.join(application._resultLines)
        self.assertFalse(current == '')
        app.DbApp.main(['-v3',
                        'all-dbs', '--internal-too', '-i'
                        ])
        application = app.BaseApp.BaseApp.lastInstance()
        current = application._resultLines
        self.assertIsEqual(0, application._logger._errors)
        self.assertTrue(current.index('mysql') >= 0)
        self.assertTrue(current.index('information_schema') >= 0)

    def testCreateAdmin(self):
        if DEBUG: return
        app.DbApp.main(['-v4',
                        'create-admin', 'testadm', 'TopSecret'
                        ])
        application = app.BaseApp.BaseApp.lastInstance()
        self.assertIsEqual(0, application._logger._errors)
        app.DbApp.main(['-v4',
                        'create-admin', 'testadm', 'TopSecret', '--readonly', '-r'
                        ])
        application = app.BaseApp.BaseApp.lastInstance()
        self.assertIsEqual(0, application._logger._errors)

    def testCreateDbAndUser(self):
        if DEBUG: return
        app.DbApp.main(['-v4',
                        'create-db-and-user', 'dbutest1', 'utest1', 'TopSecret'
                        ])
        application = app.BaseApp.BaseApp.lastInstance()
        self.assertIsEqual(0, application._logger._errors)

    def testDeleteDb(self):
        if DEBUG: return
        target = self.tempFile('export-dbutest.sql')
        app.DbApp.main(['-v4',
                        'delete-db', 'dbutest1', target, '--force', '-f'
                        ])
        application = app.BaseApp.BaseApp.lastInstance()
        self.assertIsEqual(0, application._logger._errors)
        self.assertFileExists(target)

    def testDeleteUser(self):
        if DEBUG: return
        app.DbApp.main(['-v4',
                        'delete-user', 'utest1', '--force', '-f'
                        ])
        application = app.BaseApp.BaseApp.lastInstance()
        self.assertIsEqual(0, application._logger._errors)

    def testExportDb(self):
        if DEBUG: return
        fn = self.tempFile('mysql.sql.gz', 'unittest.db')
        self.ensureFileDoesNotExist(fn)
        app.DbApp.main(['-v4',
                        'export-db', 'mysql', fn
                        ])
        application = app.BaseApp.BaseApp.lastInstance()
        self.assertIsEqual(0, application._logger._errors)
        self.assertFileExists(fn)

    def testImportDb(self):
        if DEBUG: return
        db = 'dbuimp1'
        app.DbApp.main(['-v4',
                        'create-db-and-user', db
                        ])
        fn = self.tempFile('newdb.sql', 'unittest.db')
        base.StringUtils.toFile(fn, '''
DROP TABLE IF EXISTS `users`;
create table users (
  id int(10) unsigned NOT NULL AUTO_INCREMENT PRIMARY KEY,
  name varchar(128)
);
''')
        app.DbApp.main(['-v4',
                        'import-db', db, fn, '--force', '-f'
                        ])
        application = app.BaseApp.BaseApp.lastInstance()
        self.assertIsEqual(0, application._logger._errors)
        self.assertFileExists(fn)

    def testCreateWebapp(self):
        #if DEBUG: return
        db = 'dbuimp1'
        app.DbApp.main(['-v4', f'--dir-unittest={self._configDir}',
                        'create-db-and-user', db
                        ])
        fn = self.tempFile('newdb.sql', 'unittest.db')
        base.StringUtils.toFile(fn, '''DROP TABLE IF EXISTS `users`;
create table users (
  id int(10) unsigned NOT NULL AUTO_INCREMENT PRIMARY KEY,
  name varchar(128)
);
''')
        app.DbApp.main(['-v4',
                        'import-db', db, fn, '--force', '-f'
                        ])
        application = app.BaseApp.BaseApp.lastInstance()
        self.assertIsEqual(0, application._logger._errors)
        self.assertFileExists(fn)

if __name__ == '__main__':
    # import sys;sys.argv = ['', 'Test.testName']
    tester = DbAppTest()
    tester.run()
