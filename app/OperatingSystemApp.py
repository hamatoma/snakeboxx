#! /usr/bin/python3
'''
Created: 2020.06.24
@license: CC0 https://creativecommons.org/publicdomain/zero/1.0
@author: hm
'''
import sys
import os.path
import re
import snakeboxx

import base.Const
import app.BaseApp
import base.FileHelper


class OperatingSystemApp(app.BaseApp.BaseApp):
    '''Services for operating systems.
    '''

    def __init__(self, args):
        '''Constructor.
        @param args: the program arguments, e.g. ['test', 'a@bc.de']
        '''
        app.BaseApp.BaseApp.__init__(
            self, 'OperatingSystemApp', args, progName='osboxx')

    def authKeys(self):
        '''Handles the command authKeys: put public keys into a 'authorized-keys' file.
        '''
        def makeMap(lines, regExpr):
            rc = {}
            for line in lines:
                matcher = regExpr.search(line)
                if matcher is not None:
                    groupNo = len(matcher.groups())
                    key = matcher.group(groupNo)
                    rc[key] = line
            return rc
        user = self.shiftProgramArgument()
        fnKeys = self.shiftProgramArgument('/tmp/public.keys')
        home = '' if user is None else self.createPath('/home', user)
        if user is None:
            self.argumentError('missing <user>')
        elif not os.path.exists(fnKeys):
            self.argumentError('<private-key-file> not found: ' + fnKeys)
        elif not os.path.isdir(home):
            self.argumentError(f'missing home: {home}')
        elif self.handleOptions():
            regFilter = self._optionProcessor.valueOf('filter')
            publicLines = base.StringUtils.fromFile(fnKeys, '\n')
            baseSSH = home + '/.ssh'
            base.FileHelper.ensureDirectory(baseSSH, 0o700, base.LinuxUtils.userId(user, -1),
                                            base.LinuxUtils.groupId(user, -1))
            fnAuth = baseSSH + '/authorized_keys'
            authLines = [] if not os.path.exists(
                fnAuth) else base.StringUtils.fromFile(fnAuth, '\n')
            regExprKey = re.compile(r'ssh-rsa (\S+) ')
            mapAuthKeys = makeMap(authLines, regExprKey)
            filterLines = publicLines if regFilter is None else [
                x for x in makeMap(publicLines, regFilter).values()]
            filterKeys = makeMap(filterLines, regExprKey)
            regExprLabel = re.compile(r' \S+@\S+')
            for key in filterKeys:
                if key not in mapAuthKeys:
                    line = filterKeys[key]
                    label = (regExprLabel.search(line).group(0)
                             if regExprLabel.search(line) is not None else key[1:8] + '...' + key[-12:])
                    self._logger.log('adding ' + label,
                                     base.Const.LEVEL_SUMMARY)
                    authLines.append(line)
            base.StringUtils.toFile(fnAuth, authLines, '\n', fileMode=0o700,
                                    user=base.LinuxUtils.userId(user, -1), group=base.LinuxUtils.groupId(user, -1))

    def buildConfig(self):
        '''Creates an useful configuration example.
        '''
        content = '''# created by OperatingSystemApp
logfile=/var/log/local/{}.log
'''.format(self._programName)
        self.buildStandardConfig(content)

    def buildUsage(self):
        '''Builds the usage message.
        '''
        self._usageInfo.appendDescription('''APP-NAME <global-opts> <mode> [<opts>]
 Offers service round about the operating system.
''')
        self._usageInfo.addMode('auth-keys', '''auth-keys <user> [<private-key-file>] <options>
 put some public keys taken from a file into the .ssh/authorized-keys.
 <user>: the username: for that user the auth-keys will be modified
 <private-key-file>: a text file with the known public keys. Default: /tmp/public.keys
''', '''APP-NAME -v3 auth-keys bupsupply /home/data/my.public.keys -f(^ext|@caribou)
APP-NAME -v3 auth-keys bupsrv --pattern=@caribou
''')
        self._usageInfo.addMode('create-user', '''create-user <user-name>
creates the user (or the users).
 <user-name>: bupsrv bupsupply bupwiki extbup extcave extcloud extdata exttmp
 std: does the job for bupsupply extbup and exttmp
''', '''APP-NAME create-user exttmp
APP-NAME create-user std
''')

        self._usageInfo.addMode('php-reconfigure', '''php-reconfigure [<version>]
 Sets some values in the configuration file php.ini.
 <version>: the PHP version to reconfigure e.g. "7.3". Default: all installed versions
''', '''APP-NAME create-user exttmp
APP-NAME create-user std
''')

    def buildUsageOptions(self, mode=None):
        '''Adds the options for a given mode.
        @param mode: None or the mode for which the option is added
        '''
        def add(mode, opt):
            self._usageInfo.addModeOption(mode, opt)

        if mode is None:
            mode = self._mainMode
        if mode == 'auth-keys':
            add(mode, base.UsageInfo.Option('filter', 'f',
                                            ''''only lines with a label in <private-key-file> matching this regular expression will be respected
the label of the line is the last part with the form <user>@<host>''', 'regexpr'))
        elif mode == 'create-user':
            pass
        
    def createUser(self):
        '''Create a special os user.
        '''
        user = self.shiftProgramArgument()
        uid = None if user is None else base.LinuxUtils.userId(user)
        if not self._isRoot and not app.BaseApp.BaseApp.__underTest:
            self.abort('be root!')
        elif user is None:
            self.argumentError('too few arguments: ')
        elif uid is not None:
            self._logger.log('user {} already exists: uid={}'.format(
                user, uid), base.Const.LEVEL_SUMMARY)
        elif self.handleOptions():
            users = [user]
            if user == 'std':
                users = ['bupsupply', 'extbup', 'exttmp']
            elif not re.match(r'bupsrv|bupsupply|bupwiki|extbup|extcave|extcloud|extdata|exttmp', user):
                self.argumentError('unknown <user-name>')
            else:
                ids = {'bupsrv': 201, 'bupsupply': 203, 'bupwiki': 205, 'extbup': 211, 'extcave': 212,
                       'extcloud': 213, 'extdata': 214, 'exttmp': 215}
                for user in users:
                    uid = str(ids[user])
                    gid = uid
                    self._logger.log('creating user...',
                                     base.Const.LEVEL_SUMMARY)
                    self._processHelper.execute(
                        ['/usr/sbin/groupadd', '-g', gid, user], True)
                    self._logger.log('creating user...',
                                     base.Const.LEVEL_SUMMARY)
                    self._processHelper.execute(['/usr/sbin/useradd', '-s', '/usr/sbin/nologin',
                                                 '-d', '/home/' + user, '-u', uid, '-g', gid, user], True)
                    base.FileHelper.ensureDirectory('/home/' + user, 0o750)
                    base.FileHelper.ensureDirectory(
                        '/home/{}/.ssh'.format(user), 0o700)
                    if user.startswith('ext'):
                        self._logger.log(
                            'Please leave the password empty...', base.Const.LEVEL_SUMMARY)
                        self._processHelper.execute(['/usr/bin/ssh-keygen', '-t', 'rsa', '-b', '4096',
                                                     '-f', '/home/{}/.ssh/id_rsa'.format(user), '-N', ''], True)
                    self._processHelper.execute(
                        ['/usr/bin/chown', '-R', '{}.{}'.format(user, user), '/home/' + user], True)

    def phpReconfigure(self):
        '''Reconfigures PHP configuration.
        Sets some values in the php.ini.
        '''
        version = self.shiftProgramArgument()
        if not self._isRoot and not app.BaseApp.BaseApp.__underTest:
            self.abort('be root!')
        else:
            pass

    def run(self):
        '''Implements the tasks of the application
        '''
        if self._mainMode == 'create-user':
            self.createUser()
        elif self._mainMode == 'auth-keys':
            self.authKeys()
        elif self._mainMode == 'php-reconfigure':
            self.phpReconfigure()
        else:
            self.abort('unknown mode: ' + self._mainMode)


def main(args):
    '''Main function.
    @param args: the program arguments
    '''
    snakeboxx.startApplication()
    application = OperatingSystemApp(args)
    application.main()


if __name__ == '__main__':
    main(sys.argv[1:])
