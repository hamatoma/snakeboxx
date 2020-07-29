'''
Created: 2020.06.24
@license: CC0 https://creativecommons.org/publicdomain/zero/1.0
@author: hm
'''
import time
import os.path
import posix
import pwd
import tempfile
import traceback

import base.Const
import base.Logger
import base.StringUtils
import base.FileHelper
import base.UsageInfo
import base.ProcessHelper
from base.UsageInfo import OptionProcessor

VERSION = '2020.08.07.00'


class BaseApp:
    '''The base class of all applications.
    '''
    __appLatestInstance = None
    __underTest = False

    def __init__(self, mainClass, args, isService=False, progName=None):
        '''Constructor.
        @param mainClass the application name, e.g. dbtool
        @param args: the program arguments
        @param isService: True: the application offers a systemd service
        @param progName: name of the binary None: built from the mainClass
        '''
        BaseApp.__appLatestInstance = self
        self._mainClass = mainClass
        self._appName = (
            mainClass[0:-3] if mainClass.endswith('App') else mainClass).lower()
        self._programName = self._appName + 'boxx' if progName is None else progName
        self._args = args
        self._logger = base.MemoryLogger.MemoryLogger(1)
        base.FileHelper.setLogger(self._logger)
        self._appBaseDirectory = '/usr/share/snakeboxx'
        self._programArguments = []
        self._programOptions = []
        self._start = time.process_time()
        self._startReal = time.time()
        self._doExit = True
        self._usageInfo = None
        self._configDirectory = '/etc/snakeboxx'
        self._mainMode = None
        self._processHelper = None
        self._resultText = None
        self._resultLines = None
        self._configuration = None
        self._start = time.clock()
        self._startReal = time.time()
        self._userId = posix.getuid()
        self._isRoot = self._userId == 0
        self._usageInfo = base.UsageInfo.UsageInfo(self._logger)
        self._serviceName = None
        self._isService = isService
        self._baseTestDir = None
        self._daemonSteps = 0x100000000 if not BaseApp.__underTest else 1
        self._optionProcessor = None

    def abort(self, message):
        '''Displays a message and stops the programm.
        @param message: the error message
        '''
        self._logger.error(message)
        if self._doExit:
            exit(1)

    def argumentError(self, message):
        '''Handles a severe error with program exit.
        @param message: the error message
        '''
        print('Tip: try "{} help [pattern [pattern2]]"'.format(
            self._programName))
        self.abort(message)

    def buildConfig(self):
        '''Dummy method.
        '''
        base.StringUtils.avoidWarning(self)
        raise Exception('BaseApp.buildConfig() is not overridden')

    def buildStandardConfig(self, content):
        '''Writes a useful configuration into the application specific configuration file.
        @param content: the configuration content
        '''
        fn = f'{self._configDirectory}{os.sep}{self._appName}.conf'
        if os.path.exists(fn):
            fn = fn.replace('.conf', '.example')
        self._logger.log('creating {} ...'.format(fn),
                         base.Const.LEVEL_SUMMARY)
        base.StringUtils.toFile(fn, content)

    def buildUsage(self):
        '''Builds the usage message.
        '''
        raise NotImplementedError('buildUsage() not implemented by sub class')

    def buildUsageOptions(self, mode=None):
        '''Adds the options for a given mode.
        @param mode: None or the mode for which the option is added
        '''
        raise NotImplementedError(
            'buildUsageOptions() not implemented by sub class')

    def buildUsageCommon(self, isService=False):
        '''Appends usage info common for all applications.
        @param isService: True: the application is already used as service
        '''
        self._usageInfo.addMode(
            'install', 'install\n Installs the application.', 'APP-NAME install')
        self._usageInfo.addMode('uninstall',
                                'uninstall [--service=<servicename>]\n Removes the application.',
                                'APP-NAME uninstall --service=emailboxx')
        self._usageInfo.addMode(
            'build-config', 'build-config\n Creates a useful configuration file.', 'APP-NAME build-config')
        self._usageInfo.addMode(
            'version', 'version\n Prints the version number.', 'APP-NAME version')
        if isService:
            self._usageInfo.addMode(
                'daemon', 'daemon <servicename>\n start the service daemon')
            self._usageInfo.addMode(
                'reload', 'reload <servicename>\n requests to reload configuration data')
        self._usageInfo.addMode('help', r'''help [<pattern-mode> [<pattern-submode>]]
 Prints a description of the application
 <pattern-mode>
  if given: each mode is listed if the pattern matches
 <pattern-submode>:
  if given: only submodes are listed if this pattern matches
''', 'APP-NAME help\nAPP-NAME help help sub')

    def createPath(self, directory, node=None):
        '''Returns a full name of a file or directory depending on normal or unittest environment.
        In normal environment the result is [directory] or [directory]/[node].
        If the the global parameter --dir-unittest exists: this option defines the base directory.
        In this base directory will be created a subdirectory with the last node of the parameter directory.
        For unit tests the result is taken from the global options (_testTargetDir)
        @param directory: the original directory's name, e.g. '/etc/nginx'
        @param node: None or the filename without path, e.g. 'nginx.conf'
        @return: the directory name (node is None) or the filename (directory + os.sep + node)
        '''
        if self._baseTestDir is None:
            rc = directory
        else:
            rc = self._baseTestDir + os.sep
            rc += 'root' if directory == '/' else os.path.basename(directory)
            base.FileHelper.ensureDirectory(rc)
        if node is not None:
            if rc.endswith(os.sep):
                rc += node
            else:
                rc += os.sep + node
        return rc

    def createSystemDScript(self, serviceName, starter, user, group, description):
        '''Creates the file controlling a systemd service.
        @param serviceName: used for syslog and environment file
        @param starter: name of the starter script without path, e.g. 'pymonitor'
        @param user: the service is started with this user
        @param group: the service is started with this group
        @param description: this string is showed when the status is requestes.
        '''
        systemDPath = self.createPath('/etc/systemd/system', None)
        systemdFile = f'{systemDPath}{os.sep}{serviceName}.service'
        script = '''[Unit]
Description={}.
After=syslog.target
[Service]
Type=simple
User={}
Group={}
WorkingDirectory=/etc/snakeboxx
#EnvironmentFile=-/etc/snakeboxx/{}.env
ExecStart=/usr/local/bin/{} daemon {} {}
ExecReload=/usr/local/bin/{} reload {} {}
SyslogIdentifier={}
StandardOutput=syslog
StandardError=syslog
Restart=always
RestartSec=3
[Install]
WantedBy=multi-user.target
'''.format(description, user, group, serviceName, starter, serviceName, user, starter, serviceName, user, serviceName)
        with open(systemdFile, 'w') as fp:
            fp.write(script)
        print('systemd script created: ' + systemdFile)
        uid = None
        try:
            uid = pwd.getpwnam(user)
            self._logger.log('user {} ({}) already exists'.format(
                user, uid), base.Const.LEVEL_DETAIL)
        except KeyError:
            if self._isRoot:
                self._logger.log('creating user {} ...'.format(
                    user), base.Const.LEVEL_SUMMARY)
                self._processHelper.execute(['/usr/sbin/useradd', user], True)

    def defaultConfigurationFile(self):
        '''Returns the name of the file for the configuration example.
        '''
        rc = f'{self._configDirectory}{os.sep}{self._appName}.conf'
        if os.path.exists(rc):
            rc = rc[0:-4] + 'example'
        return rc

    def daemon(self):
        '''Waits for jobs and executes them
        '''
        serviceName = self._programArguments[0] if len(
            self._programArguments) >= 1 else self._appName
        self._logger.log('starting {} with version {}'.format(
            serviceName, VERSION), base.Const.LEVEL_SUMMARY)
        fileReloadRequest = self.reloadRequestFile(serviceName)
        if self._daemonSteps is None:
            self._daemonSteps = 0x7fffffffffff
        while self._daemonSteps > 0:
            self._daemonSteps -= 1
            hasRequest = fileReloadRequest is not None and os.path.exists(
                fileReloadRequest)
            if hasRequest:
                if not self.handleReloadRequest(fileReloadRequest):
                    fileReloadRequest = None
            self.daemonAction(hasRequest)
            interval = self._configuration.getInt('daemon.interval', 3)
            time.sleep(interval)

    def daemonAction(self, reloadRequest):
        '''Does the real thing in the daemon (= service).
        @param reloadRequest: True: a reload request has been done
        '''
        base.StringUtils.avoidWarning(self)
        base.StringUtils.avoidWarning(reloadRequest)
        raise Exception('BaseApp.daemonAction() is not overridden')

    def handleCommonModes(self):
        '''Handles the modes common to all application like 'install'
        @return: True: mode is a common mode and already handled
        '''
        rc = True
        if self._mainMode is None:
            self.help()
        else:
            if self._mainMode == 'install':
                self.install()
            elif self._mainMode == 'uninstall':
                self.uninstall()
            elif self._mainMode == 'build-config':
                self.buildConfig()
            elif self._mainMode == 'help':
                self.help()
            elif self._mainMode == 'reload':
                self.requestReload()
            elif self._mainMode == 'version':
                print('version: ' + VERSION)
            else:
                rc = False
        return rc

    def handleReloadRequest(self, fileReloadRequest):
        '''Handles a request for reloading configuration inside the daemon.
        @param fileReloadRequest: the name of the file defining a request
        @return: True: success False: the file could not be deleted/modified
        '''
        rc = True
        try:
            os.unlink(fileReloadRequest)
        except OSError:
            base.StringUtils.toFile(fileReloadRequest, 'found')
        self._configuration.readConfig(self._configuration._filename)
        if os.path.exists(fileReloadRequest) and os.path.getsize(fileReloadRequest) == 0:
            self._logger.error(
                'cannot delete/rewrite reload request file: ' + fileReloadRequest)
            rc = False
        return rc

    def handleGlobalOptions(self):
        '''Search for the global options and handles it.
        Divides the rest of arguments into _programArguments and _programOptions
        '''
        runtime = False
        mode = '<global-option>'
        self._usageInfo.addMode(mode,
                                r'''<global-options>: this options can be used for all modes and must positioned in front of the mode.
''', '')
        option = base.UsageInfo.Option('config-directory', 'c', 'the directory containing the configuration file',
                                       'string', self._configDirectory)
        self._usageInfo.addModeOption(mode, option)
        option = base.UsageInfo.Option('runtime', 'r', 'the runtime will be displayed at the end of the program',
                                       'bool')
        self._usageInfo.addModeOption(mode, option)
        option = base.UsageInfo.Option(
            'dir-unittest', None, 'a directory used for unit tests')
        self._usageInfo.addModeOption(mode, option)
        option = base.UsageInfo.Option(
            'log-file', None, 'the file for logging messages. If empty the MemoryLogger will be used', mayBeEmpty=True)
        self._usageInfo.addModeOption(mode, option)
        option = base.UsageInfo.Option('verbose-level', 'v', 'sets the amount of logs: only log messages with a level <= <level> will be displayed',
                                       'int', base.Const.LEVEL_SUMMARY)
        self._usageInfo.addModeOption(mode, option)
        opts = []
        while self._args and self._args[0].startswith('-'):
            opts.append(self._args[0])
            self._args = self._args[1:]
        optionProcessor = self._usageInfo._optionProcessors[mode]
        if not optionProcessor.scan(opts):
            self.abort('error on global options')
        else:
            self._configDirectory = optionProcessor.valueOf('config-directory')
            self._baseTestDir = optionProcessor.valueOf('dir-unittest')
            if self._args:
                self._mainMode = self._args[0]
                self._args = self._args[1:]
            for arg in self._args:
                if arg.startswith('-'):
                    self._programOptions.append(arg)
                else:
                    self._programArguments.append(arg)
            # === configuration
            fn = None
            if self._mainMode not in ['install', 'uninstall', 'help']:
                fn = f'{self._configDirectory}{os.sep}{self._appName}.conf'
                if not os.path.exists(fn):
                    self.buildConfig()
                if not os.path.exists(fn):
                    fn = None
            self._configuration = base.JavaConfig.JavaConfig(fn, self._logger)
            # === logger
            logFile = optionProcessor.valueOf('log-file')
            if (self._appName == '!unittest' or self.__underTest) and logFile is not None:
                self._logger._verboseLevel = base.Const.LEVEL_FINE
            else:
                if logFile is None:
                    logFile = self._configuration.getString('logfile')
                if logFile is None:
                    logFile = f'/var/log/local/{self._programName}.log'
                # '' or '-' means memory logger
                if logFile != '' or logFile == '-':
                    oldLogger = self._logger
                    self._logger = base.Logger.Logger(
                        logFile, optionProcessor.valueOf('verbose-level'))
                    oldLogger.derive(self._logger)
            base.FileHelper.setLogger(self._logger)
            base.StringUtils.setLogger(self._logger)
            self._processHelper = base.ProcessHelper.ProcessHelper(
                self._logger)
            if not optionProcessor.valueOf('runtime'):
                self._start = None

    def handleOptions(self):
        '''Compares the current options with the specified options.
        @return: True: success
        '''
        self.buildUsageOptions()
        self._optionProcessor = processor = self._usageInfo._optionProcessors[self._mainMode]
        rc = processor.scan(self._programOptions)
        return rc

    def help(self):
        '''Prints the usage message.
        '''
        self.buildUsageCommon(self._isService)
        self.buildUsage()
        for mode in self._usageInfo._descriptions:
            self.buildUsageOptions(mode)
            self._usageInfo.extendUsageInfoWithOptions(mode)
        self._usageInfo.replaceMacro('APP-NAME', self._programName)
        pattern = '' if not self._programArguments else self._programArguments[0]
        pattern2 = '' if len(
            self._programArguments) < 2 else self._programArguments[1]
        info = self._usageInfo.asString(pattern, 0, pattern2)
        self._resultText = info
        print(info)

    def install(self):
        '''Installs the program.
        '''
        if not self._isRoot and not self.__underTest:
            self.argumentError('be root!')
        else:
            configDir = self._configDirectory
            base.FileHelper.ensureDirectory(configDir)
            self.buildConfig()
            app = self.createPath('/usr/local/bin', self._programName)
            source = f'{self._appBaseDirectory}{os.sep}app{os.sep}{self._mainClass}.py'
            if os.path.exists(app):
                base.FileHelper.ensureFileDoesNotExist(app)
            self._logger.log(
                r'creating starter {app} -> {source}', base.Const.LEVEL_SUMMARY)
            os.symlink(source, app)
            fn = '/usr/lib/python3/dist-packages/snakeboxx.py'
            if not os.path.exists(fn):
                self._logger.log('creating {} ...'.format(fn))
                base.StringUtils.toFile(fn, """'''Prepare for usage of snakeboxx modules.
'''
import sys

if '/usr/share/snakeboxx' not in sys.path:
    sys.path.insert(0, '/usr/share/snakeboxx')

def startApplication():
    '''Starts the application.
    In this version: do nothing
    '''
""")

    def installAsService(self, service, startAtOnce=False):
        '''Enables the service and start it (if wanted):
        @param service: name of the service
        @param startAtOnce: True: the service will be started False: do not start the service
        '''
        if self._isRoot:
            self._processHelper.execute(
                ['/usr/bin/systemctl', 'enable', service], True)
            if startAtOnce:
                self._processHelper.execute(
                    ['/usr/bin/systemctl', 'start', service], True)
                self._processHelper.execute(
                    ['/usr/bin/systemctl', 'status', service], True)
            else:
                print(
                    'please inspect the configuration and then execute "/usr/bin/systemctl start {}"'.format(service))

    @staticmethod
    def lastInstance():
        '''Returns the last instantiated instance of BaseApp.
        @returns: the last instantiated instance of BaseApp
        '''
        return BaseApp.__appLatestInstance

    def main(self):
        '''The main function: handles the complete application process.
        '''
        try:
            self.handleGlobalOptions()
            if not self.handleCommonModes():
                if self._mainMode is None:
                    self.help()
                else:
                    self.run()
            if self._start is not None:
                real = base.StringUtils.secondsToString(
                    int(time.time() - self._startReal))
                cpu = base.StringUtils.secondsToString(
                    int(time.clock() - self._start))
                self._logger.log(
                    'runtime (real/process): {}/{}'.format(real, cpu), base.Const.LEVEL_SUMMARY)
        except Exception as exc:
            self._logger.error(f'{type(exc)}: {exc}')
            traceback.print_exc()

    def reloadRequestFile(self, serviceName):
        '''Return the name of the file for request a reload.
        @param serviceName: name of the service
        @return the filename
        '''
        base.StringUtils.avoidWarning(self)
        rc = '{}/{}/reload.request'.format(tempfile.gettempdir(), serviceName)
        return rc

    def requestReload(self):
        '''Requests a reading of the configuration data.
        '''
        service = self.shiftProgramArgument(self._programName)
        fn = self.reloadRequestFile(service)
        base.FileHelper.ensureDirectory(os.path.dirname(fn), 0o777)
        self._logger.log('reload requested', base.Const.LEVEL_SUMMARY)
        base.StringUtils.toFile(fn, '')
        os.chmod(fn, 0o666)
        if not self._isRoot:
            count = 10 if not self.__underTest else 1
            self._logger.log(
                f'waiting for answer (max {count} sec)', base.Const.LEVEL_SUMMARY)
            for ix in range(count):
                if not os.path.exists(fn):
                    self._logger.log(f'{ix+1}: request not processed',
                                     base.Const.LEVEL_SUMMARY)
                    break
                time.sleep(1)
            if ix <= 0:
                self._logger.error('reload request was not processed')
            base.FileHelper.ensureFileDoesNotExist(fn)

    def run(self):
        '''Starts the application specific work.
        Note: must be overwritten by the sub class.
        '''
        raise NotImplementedError('BaseApp.run() is not overridden')

    @staticmethod
    def setUnderTest(status=True):
        ''' Marks the application to run under a unittest.
        @param status: True: set test status False: release test status
        '''
        BaseApp.__underTest = status

    def shiftProgramArgument(self, defaultValue=None):
        '''Returns the next program argument.
        @param defaultValue: the return value if no program argument is available
        @return None: no more arguments otherwise: the next program argument which is already removed from _programArguments
        '''
        rc = defaultValue
        if self._programArguments:
            rc = self._programArguments[0]
            del self._programArguments[0]
        return rc

    def uninstall(self):
        '''Uninstalls the program.
        '''
        if not self._isRoot and not self.__underTest:
            self.argumentError('be root!')
        else:
            app = self.createPath('/usr/local/bin', self._programName)
            if os.path.exists(app):
                self._logger.log(
                    f'removing starter {app} ...', base.Const.LEVEL_SUMMARY)
                base.FileHelper.ensureFileDoesNotExist(app)
            if self._programOptions and self._programOptions[0].startswith('--service='):
                serviceName = self._programOptions[0][10:]
                serviceFile = self.createPath(
                    '/etc/systemctl/system', f'{serviceName}.service')
                if os.path.exists(serviceFile):
                    self._logger.log('removing service file {} ...'.format(
                        serviceFile), base.Const.LEVEL_SUMMARY)
                    os.unlink(serviceFile)
                else:
                    self._logger.log('not found: ' + serviceFile,
                                     base.Const.LEVEL_SUMMARY)

    def unknownMode(self):
        '''Handles the error "unknown mode".
        '''
