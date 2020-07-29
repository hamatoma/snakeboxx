#! /usr/bin/python3
'''
Created: 2020.06.24
@license: CC0 https://creativecommons.org/publicdomain/zero/1.0
@author: hm
'''
import sys
import os.path
import snakeboxx

import base.UsageInfo
import app.BaseApp


def removeFromArrayIfExists(anArray, item):
    '''Removes a given item from an array if the array contains that.
    @param anArray: the array to process
    @param item: the item to remove
    '''
    for ix in reversed(range(len(anArray))):
        if item == anArray[ix]:
            del anArray[ix]


class DbApp(app.BaseApp.BaseApp):
    '''Performs some tasks with mysql databases: creation, import, export...
    '''

    def __init__(self, args):
        '''Constructor.
        @param args: the program arguments, e.g. ['test', 'a@bc.de']
        '''
        app.BaseApp.BaseApp.__init__(self, 'DbApp', args, None, 'dbboxx')
        self._processTool = base.ProcessHelper.ProcessHelper(self._logger)

    def allDbs(self):
        '''Lists the databases.
        '''
        if self.handleOptions():
            argv = self.buildArgvMysql('mysql', True)
            sql = '''show databases;'''
            rc = self._processTool.executeInputOutput(argv, sql)
            if rc and rc[0] == 'Database':
                rc = rc[1:]
            removeFromArrayIfExists(rc, '')
            if not self._optionProcessor.valueOf('internal-too'):
                removeFromArrayIfExists(rc, 'mysql')
                removeFromArrayIfExists(rc, 'information_schema')
                removeFromArrayIfExists(rc, 'performance_schema')
        self._resultLines = rc
        print('\n'.join(rc))

    def buildConfig(self):
        '''Creates an useful configuration example.
        '''
        content = '''# created by DbApp
logfile=/var/log/local/dbboxx.log
admin.user=dbadm
admin.code=TopSecret
webapp.base=/srv/www
'''
        self.buildStandardConfig(content)

    def buildArgvMysql(self, command, needsAdmin=False):
        '''Builds an argument vector for a mysql relevant command (mysql or mysqldump...).
        @param command: 'mysql' or 'mysqldump'
        @param needsAdmin: True: the operation needs administrator rights
        '''
        rc = None
        user = self._optionProcessor.valueOf(
            'adm-name' if needsAdmin else 'user-name')
        if user is not None:
            code = self._optionProcessor.valueOf(
                'adm-password' if needsAdmin else 'user-password')
        else:
            user = self._configuration.getString('admin.user')
            code = self._configuration.getString('admin.code')
        if user is None:
            self.abort('missing user (option or configuration file)')
        elif code is None:
            self.abort('missing password (option or configuration file)')
        else:
            rc = [command]
            rc.append(f'-u{user}')
            if code != '':
                rc.append(f'-p{code}')
        return rc

    def buildUsage(self):
        '''Builds the usage message.
        '''
        self._usageInfo.appendDescription('''APP-NAME <global-opts> <mode> [<options>]
 Info and manipulation of mysql databases.
''')
        self._usageInfo.addMode('all-dbs', '''all-dbs <opts>
 Lists all databases.
 ''', '''APP-NAME all-dbs
APP-NAME all-dbs --admin=jonny --adm-password=ForgetNever
''')
        self._usageInfo.addMode('create-admin', '''APP-NAME create-admin <name> <password> [<options>]
 Create a database user with admin rights.
 ''', '''APP-NAME create-admin dbadm TopSecret
APP-NAME create-admin dbadmin MoreSecret --admin=root --adm-password=ForgetNever
''')
        self._usageInfo.addMode('create-db-and-user', '''APP-NAME create-db-and-user <db> [<user> <password>] [<options>]
 Create a database and a user with rights to modify this db.
 ''', '''APP-NAME create-db-and-user dbcompany
APP-NAME create-db-and-user dbcompany dbadmin MoreSecret --adm-name=root --adm-password=ForgetNever
''')
        self._usageInfo.addMode('create-webapp', '''APP-NAME create-webapp <domain> <db> <user> <password> [<options>]
 Create a web application with db, user and password.
 ''', '''APP-NAME create-webapp example.com dbexample example TopSecret
APP-NAME create-webapp example.com dbexample example TopSecret --no-dir
''')
        self._usageInfo.addMode('delete-db', '''APP-NAME delete-db <db> [<backup-file>] [<options>]
 Deletes a database (with or without a confirmation and/or a backup).
  <db>: name of the database
  <backup-file>: before deleting the database is dumped to this file. Should end with '.sql' or '.sql.gz'
   if ending with '.gz' the dump will be compressed via gzip. Default: <temp>/<db>.sql.gz
 ''', '''APP-NAME delete-db dbcompany ../db/dbcompany.sql.gz
APP-NAME delete-db dbcompany --no-backup --force --user-name=root --user-password=ForgetNever
''')
        self._usageInfo.addMode('delete-user', '''APP-NAME delete-user <user> <options>
 Deletes a database user with/without confirmation.
  <db>: name of the database
''', '''APP-NAME delete-user jonny
APP-NAME delete-user eve --force --user-name=root --user-password=ForgetNever
''')
        self._usageInfo.addMode('export-db', '''APP-NAME export-db <db> <file> [<options>]
 Exports a database into a file.
  <db>: name of the database
  <file>: the content is dumped to this file. If ending with '.gz' the content will be compressed with gzip
''', '''APP-NAME export-db dbcompany dbc.sql.gz
APP-NAME export-db dbcompany /data/version3.sql --force --user-name=root --user-password=ForgetNever
''')
        self._usageInfo.addMode('export-webapp', '''APP-NAME export-webapp <domain> [<file>] [<options>]
 Exports a database into a file.
  <domain>: the domain of the web application, e.g. 'example.com'
  <file>: the content is dumped to this file. If ending with '.gz' the content will be compressed with gzip
   if not given: it will be created in the tempororary directory with the name <domain>.sql.gz
''', '''APP-NAME export-webapp example.com
APP-NAME export-webapp example.com /data/version9.sql --force --user-name=root --user-password=ForgetNever
''')
        self._usageInfo.addMode('import-db', '''APP-NAME import-db <db> <file> [<options>]
 Imports a file into a database.
  <db>: name of the database
  <file>: the new content as SQL statements. If ending with '.gz' the content is compressed with gzip
''', '''APP-NAME export-db dbcompany dbc.sql.gz
APP-NAME import-db dbcompany company_update1.sql --user-name=root --user-password=ForgetNever
''')
        self._usageInfo.addMode('import-webapp', '''APP-NAME import-webapp <domain> <file> [<options>]
 Imports a file into a database of a web application.
  <domain>: domain of the web application, e.g. 'example.com'
  <file>: the new content as SQL statements. If ending with '.gz' the content is compressed with gzip
''', '''APP-NAME import-webapp www.example.com dbc.sql.gz
''')

    def buildUsageOptions(self, mode=None):
        '''Adds the options for a given mode.
        @param mode: None or the mode for which the option is added
        '''
        def add(mode, opt):
            self._usageInfo.addModeOption(mode, opt)

        def addAdminOpts(mode):
            add(mode, base.UsageInfo.Option('adm-name',
                                            'N', 'name of a db user with admin rights'))
            add(mode, base.UsageInfo.Option(
                'adm-password', 'P', 'password of the admin'))

        def addUserOpts(mode):
            add(mode, base.UsageInfo.Option('user-name', 'n',
                                            'name of a db user with rights for the related db'))
            add(mode, base.UsageInfo.Option(
                'user-password', 'P', 'password of the user'))

        def addForce(mode):
            add(mode, base.UsageInfo.Option('force', 'f',
                                            'delete without confirmation', 'bool'))

        def addNoBackup(mode):
            add(mode, base.UsageInfo.Option(
                'no-backup', 'n', 'no backup export is done', 'bool'))

        if mode is None:
            mode = self._mainMode
        if mode == 'all-dbs':
            addAdminOpts(mode)
            add(mode, base.UsageInfo.Option('internal-too', 'i',
                                            'the internal databases will be listed too', 'bool'))
        elif mode == 'create-admin':
            addAdminOpts(mode)
            add(mode, base.UsageInfo.Option('readonly', 'r',
                                            'the admin gets only read rights (e.g. for backup)', 'bool'))
        elif mode == 'create-db-and-user':
            addAdminOpts(mode)
        elif mode == 'delete-db':
            addUserOpts(mode)
            addForce(mode)
            addNoBackup(mode)
        elif mode == 'delete-user':
            addAdminOpts(mode)
            addForce(mode)
        elif mode == 'export-db':
            addUserOpts(mode)
        elif mode == 'export-webapp':
            pass
        elif mode == 'import-db':
            addUserOpts(mode)
            addForce(mode)
            addNoBackup(mode)
        elif mode == 'import-webapp':
            addForce(mode)
            addNoBackup(mode)
        elif mode == 'create-webapp':
            add(mode, base.UsageInfo.Option('no-dir', 'n',
                                            'the directory will not created', 'bool'))

    def confirm(self, message, expected):
        '''Confirms a critical action.
        @param message: the message of confirmation
        @param expected: this value must be typed by the user
        @return: True: confirmation successful
        '''
        answer = input(message + ': ')
        rc = answer.strip() == expected
        if not rc:
            self.abort('confirmation failed')
        return rc

    def createAdmin(self):
        '''Creates an user able to process all databases
        '''
        user = self.shiftProgramArgument()
        code = self.shiftProgramArgument()
        if code is None:
            self.abort('too few arguments')
        else:
            if self.handleOptions():
                readOnly = self._optionProcessor.valueOf('readonly')
                rights = 'SELECT, SHOW VIEW' if readOnly else 'ALL'
                tail = '' if readOnly else ' WITH GRANT OPTION'
                sql = f'''GRANT {rights} ON *.* TO '{user}'@'localhost' IDENTIFIED BY '{code}'{tail};
flush privileges;'''
                self._logger.log(
                    f'creating admin {user}...', base.Const.LEVEL_SUMMARY)
                self._logger.log(sql, base.Const.LEVEL_FINE)
                argv = self.buildArgvMysql('mysql', True)
                self._processTool.executeInput(
                    argv, self._logger._verboseLevel >= base.Const.LEVEL_DETAIL, sql)

    def createDbAndUser(self):
        '''Creates a database and a user with rights to modify this db.
        '''
        db = self.shiftProgramArgument()
        user = self.shiftProgramArgument()
        code = self.shiftProgramArgument()
        if db is None:
            self.abort('too few arguments')
        elif user is not None and code is None:
            self.abort('missing password')
        elif code is not None and code.find("'") >= 0:
            self.abort('password must not contain "\'"')
        else:
            if self.handleOptions():
                if user is not None:
                    sql = f'''GRANT ALL ON {db}.* TO '{user}'@'localhost' IDENTIFIED BY '{code}' WITH GRANT OPTION;
flush privileges;
create database if not exists {db};'''
                else:
                    sql = f'create database if not exists {db};'
                self._logger.log(
                    f'creating db {db}...', base.Const.LEVEL_SUMMARY)
                self._logger.log(sql, base.Const.LEVEL_FINE)
                argv = self.buildArgvMysql('mysql', True)
                self._processTool.executeInput(
                    argv, self._logger._verboseLevel >= base.Const.LEVEL_DETAIL, sql)

    def createWebApp(self):
        '''Creates a database and a user with rights to modify this db.
        '''
        domain = self.shiftProgramArgument()
        db = self.shiftProgramArgument()
        user = self.shiftProgramArgument()
        code = self.shiftProgramArgument()
        baseDir = self._configuration.getString(
            'webapp.base', '/srv/www') + os.sep + domain
        fnConfig = self._configDirectory + os.sep + f'webapp.d/{domain}'
        if code is None:
            self.abort('too few arguments')
        elif os.path.exists(fnConfig):
            self.abort(f'webapp {domain} already exist: {fnConfig}')
        elif os.path.exists(fnConfig + '.conf'):
            self.abort(f'webapp {domain} already exist: {fnConfig}.conf')
        else:
            self._logger.log(
                f'creating {fnConfig} ...', base.Const.LEVEL_SUMMARY)
            base.StringUtils.toFile(fnConfig, f'''db={db}
user={user}
password={code}
sql.file={domain}-{db}
directory={baseDir}
excluded=
''')
            sql = f'''GRANT ALL ON {db}.* TO '{user}'@'localhost' IDENTIFIED BY '{code}';
flush privileges;
create database if not exists {db};'''
            self._logger.log(
                f'creating db {db}...', base.Const.LEVEL_SUMMARY)
            self._logger.log(sql, base.Const.LEVEL_FINE)
            argv = self.buildArgvMysql('mysql', True)
            self._processTool.executeInput(
                argv, self._logger._verboseLevel >= base.Const.LEVEL_DETAIL, sql)
            if not self._optionProcessor.valueOf('no-dir') and not os.path.exists(baseDir):
                base.FileHelper.ensureDirectory(baseDir)

    def deleteDb(self):
        '''Creates a database and a user with rights to modify this db.
        '''
        db = self.shiftProgramArgument()
        backupFile = self.shiftProgramArgument()
        if db is None:
            self.abort('too few arguments')
        else:
            if self.handleOptions():
                force = self._optionProcessor.valueOf('force')
                if not self._optionProcessor.valueOf('no-backup'):
                    self.export(db, backupFile)
                if force or self.confirm('If you want to delete you must type the name of the db', db):
                    sql = f'DROP database {db};'
                    self._logger.log(
                        f'deleting db {db}...', base.Const.LEVEL_SUMMARY)
                    self._logger.log(sql, base.Const.LEVEL_FINE)
                    argv = self.buildArgvMysql('mysql', False)
                    self._processTool.executeInput(
                        argv, self._logger._verboseLevel >= base.Const.LEVEL_DETAIL, sql)

    def deleteUser(self):
        '''Deletes a database user.
        '''
        user = self.shiftProgramArgument()
        if user is None:
            self.abort('too few arguments')
        else:
            if self.handleOptions():
                force = self._optionProcessor.valueOf('force')
                if force or self.confirm('If you want to delete you must type the name of the user', user):
                    sql = f'''DROP user {user}@localhost;
flush privileges;
'''
                    self._logger.log(
                        f'deleting user {user}...', base.Const.LEVEL_SUMMARY)
                    self._logger.log(sql, base.Const.LEVEL_FINE)
                    argv = self.buildArgvMysql('mysql', True)
                    argv.append('mysql')
                    self._processTool.executeInput(
                        argv, self._logger._verboseLevel >= base.Const.LEVEL_DETAIL, sql)

    def export(self, db, target, user=None, code=None):
        '''Exports a database into a file.
        @param db: the name of the database
        @param target: the file to export. None: a file in the temp directory will be written
        @param user: None: will be got from options or configuration. Otherwise: a user with read rights for db
        @param code: None: will be got from options or configuration. Otherwise: the password of user
        '''
        if target is None:
            now = datetime.now().strftime('%y.%m.%d-%H_%M')
            target = base.FileHelper.tempFile(f'{db}.{now}.sql.gz')
        if user is None:
            user = self._optionProcessor.valueOf('user-name')
            if user is not None:
                code = self._optionProcessor.valueOf('user-password')
            else:
                user = self._configuration.getString('admin.user')
                code = self._configuration.getString('admin.code')
        self._logger.log(f'exporting {db} to {target}')
        if target.endswith('.gz'):
            self._processHelper.executeScript(f'''#! /bin/bash
/usr/bin/mysqldump --default-character-set=utf8mb4 --single-transaction -u{user} '-p{code}' {db} | gzip -c > {target}
''')
        else:
            self._processHelper.executeScript(f'''#! /bin/bash
/usr/bin/mysqldump --default-character-set=utf8mb4 --single-transaction -u{user} '-p{code}' {db} > {target}
''')

    def exportDb(self):
        '''Exports a database into a file.
        '''
        db = self.shiftProgramArgument()
        file = self.shiftProgramArgument()
        if db is None:
            self.abort('too few arguments')
        else:
            if self.handleOptions():
                self.export(db, file)

    def exportWebApp(self):
        '''Exports a database into a file.
        '''
        domain = self.shiftProgramArgument()
        file = self.shiftProgramArgument()
        if domain is None:
            self.abort('too few arguments')
        else:
            if self.handleOptions():
                config = self.webApp(domain)
                if config is None:
                    self.abort('missing configuration for {domain}')
                else:
                    self.export(config.getString('db'), file, config.getString(
                        'user'), config.getString('password'))

    def importDb(self):
        '''Imports a file into a database.
        '''
        db = self.shiftProgramArgument()
        file = self.shiftProgramArgument()
        if file is None:
            self.abort('too few arguments')
        else:
            if self.handleOptions():
                force = self._optionProcessor.valueOf('force')
                if not self._optionProcessor.valueOf('no-backup'):
                    self.export(db, None)
                if force or self.confirm('If you want to import you must type the name of the db', db):
                    self.importSql(db, file)

    def importSql(self, db, source, user=None, code=None):
        '''Exports a database into a file.
        @param db: the name of the database
        @param source: the file to import
        @param user: None: will be got from options or configuration. Otherwise: a user with read rights for db
        @param code: None: will be got from options or configuration. Otherwise: the password of user
        '''
        if user is None:
            user = self._optionProcessor.valueOf('user-name')
            if user is not None:
                code = self._optionProcessor.valueOf('user-password')
            else:
                user = self._configuration.getString('admin.user')
                code = self._configuration.getString('admin.code')
        self._logger.log(f'import {db} from {source}')
        if source.endswith('.gz'):
            self._processHelper.executeScript(f'''#! /bin/bash
/usr/bin/zcat {source} | /usr/bin/mysql -u{user} '-p{code}' {db}
''')
        else:
            self._processHelper.executeScript(f'''#! /bin/bash
/usr/bin/mysql -u{user} '-p{code}' {db} < {source}
''')

    def importWebApp(self):
        '''Imports a file into a database.
        '''
        domain = self.shiftProgramArgument()
        file = self.shiftProgramArgument()
        if file is None:
            self.abort('too few arguments')
        else:
            if self.handleOptions():
                config = self.webApp(domain)
                if config is None:
                    self.abort('missing configuration for {domain}')
                else:
                    db = config.getString('db')
                    force = self._optionProcessor.valueOf('force')
                    if not self._optionProcessor.valueOf('no-backup'):
                        self.export(db, None)
                    if force or self.confirm('If you want to import you must type the name of the db', db):
                        self.importSql(db, file, config.getString(
                            'user'), config.getString('password'))

    def run(self):
        '''Implements the tasks of the application.
        '''
        if self._mainMode == 'all-dbs':
            self.allDbs()
        elif self._mainMode == 'create-admin':
            self.createAdmin()
        elif self._mainMode == 'create-db-and-user':
            self.createDbAndUser()
        elif self._mainMode == 'create-webapp':
            self.createDbAndUser()
        elif self._mainMode == 'delete-db':
            self.deleteDb()
        elif self._mainMode == 'delete-user':
            self.deleteUser()
        elif self._mainMode == 'export-db':
            self.exportDb()
        elif self._mainMode == 'export-webapp':
            self.exportWebApp()
        elif self._mainMode == 'import-db':
            self.importDb()
        elif self._mainMode == 'import-webapp':
            self.importWebApp()
        else:
            self.abort('unknown mode: ' + self._mainMode)

    def webApp(self, domain):
        '''Returns the web application configuration.
        @param domain: the domain of the web application
        @return: None: not found Otherwise: the JavaConfig instance
        '''
        rc = None
        fnConfig = self.createPath(f'/etc/snakeboxx/webapps.d', domain)
        if not os.path.exists(fnConfig):
            fnConfig += '.conf'
        if os.path.exists(fnConfig):
            rc = base.JavaConfig.JavaConfig(fnConfig, self._logger)
            config = base.JavaConfig.JavaConfig(fnConfig, self._logger)
            db = config.getString('db')
            user = config.getString('user')
            code = config.getString('password')
            if db is None or user is None or code is None:
                self._logger.error(f'incomplete data in {fnConfig}')
                rc = None
        return rc


def main(args):
    '''Main function.
    @param args: the program arguments
    '''
    snakeboxx.startApplication()
    application = DbApp(args)
    application.main()


if __name__ == '__main__':
    main(sys.argv[1:])
