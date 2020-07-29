#! /usr/bin/python3
'''
Created: 2020.06.24
@license: CC0 https://creativecommons.org/publicdomain/zero/1.0
@author: hm
'''
import sys
import time
import os.path
import re
import snakeboxx

import base.Const
import base.Scheduler
import base.FileHelper
import net.HttpClient
import app.BaseApp


class CloudTaskInfo(base.Scheduler.TaskInfo):
    '''Executes a task for the satellite.
    '''

    def __init__(self, cloud, application):
        '''Constructor.
        @param cloud: the full path of the cloud
        @param application: the calling parent
        '''
        self._application = application
        self._cloud = cloud

    def process(self, sliceInfo):
        '''Executes the task.
        @param sliceInfo: the entry of the scheduler list
        @return True: success
        '''
        base.StringUtils.avoidWarning(sliceInfo)
        self._application.sendCloudInfo(self._cloud)


class FilesystemTaskInfo(base.Scheduler.TaskInfo):
    '''Executes a task for the satellite.
    '''

    def __init__(self, filesystem, application):
        '''Constructor.
        @param filesystem: the mount path of the filesystem
        @param application: the calling parent
        '''
        self._application = application
        self._filesystem = filesystem

    def process(self, sliceInfo):
        '''Executes the task.
        @param sliceInfo: the entry of the scheduler list
        @return True: success
        '''
        base.StringUtils.avoidWarning(sliceInfo)
        self._application.sendFilesystemInfo(self._filesystem)


class SatelliteApp(app.BaseApp.BaseApp):
    '''REST client for WebDashFiller.
    '''

    def __init__(self, args):
        '''Constructor.
        @param args: the program arguments, e.g. ['test', 'a@bc.de']
        '''
        app.BaseApp.BaseApp.__init__(
            self, 'SatelliteApp', args, isService=True, progName='satboxx')
        self._clouds = None
        self._client = None
        self._scheduler = None
        self._webDashServer = None
        self._countClouds = 0
        self._filesystems = None
        self._countFilesystems = 0
        self._mapFilesystems = None
        self._rexprExcludedFilesystem = None
        self._rexprExcludedClouds = None
        self._stopAtOnce = False
        self._hostname = None

    def buildConfig(self):
        '''Creates an useful configuration example.
        '''
        content = '''# created by SatelliteApp
logfile=/var/log/local/satboxx.log
wdfiller.active=true
wdfiller.url=http://localhost:8080
# separator ' ': possible modes cloud filesystem stress
wdfiller.kinds=cloud
# interval between 2 send actions in seconds
wdfiller.cloud.interval=600
wdfiller.cloud.data.directory=/opt/clouds
wdfiller.cloud.main.directory=/opt/clouds
wdfiller.cloud.excluded=cloud.test|cloud.huber.de
wdfiller.filesystem.interval=600
wdfiller.filesystem.excluded=/mnt/|/media/usb
#wdfiller.filesystem.map=/:root,/tmp/fs.system:fs.system
#wdfiller.filesystem.map=
wdfiller.stress.interval=120
hostname=caribou
'''
        self.buildStandardConfig(content)

    def buildUsage(self):
        '''Builds the usage message.
        '''
        self._usageInfo.appendDescription('''APP-NAME <global-opts> <mode> [<opts>]
 Sends data via REST to some servers. Possible servers are WebDashFiller and Monitor.
''')
        self._usageInfo.addMode('test', '''test <kind> [<count> [<interval>]]
 <kind>: 'cloud', 'filesystem' or 'stress'
 <count>: number of send actions, default: 1
 <interval>: time between two send actions in seconds, default: 1
''', '''APP-NAME test cloud 3 5
''')
        del self._usageInfo._descriptions['daemon']
        self._usageInfo.addMode('daemon', '''daemon <servicename> [<options>]
 <servicename>: the name of the SystemD service
''', '''APP-NAME daemon satbutt --count=1 --interval=2
''')

    def buildUsageOptions(self, mode=None):
        '''Adds the options for a given mode.
        @param mode: None or the mode for which the option is added
        '''
        def add(mode, opt):
            self._usageInfo.addModeOption(mode, opt)

        if mode is None:
            mode = self._mainMode
        if mode == 'test':
            pass
        elif mode == 'daemon':
            add(mode, base.UsageInfo.Option('count', 'c',
                                            'number of rounds: in one round all cloud state infos will be sent default: forever', 'int'))
            add(mode, base.UsageInfo.Option('interval', 'i',
                                            'time (seconds) between two send rounds: default: see configuration file', 'int'))

    def cloudInit(self, startAtOnce=False, count=None, interval=None):
        '''Initializes the cloud sending actions.
        For each cloud: an task to send the cloud info will be inserted into the scheduler list.
        @param startAtOnce: True: the cloud infos will be sent at once too
        @param count: None or the number of rounds
        @param interval: the time of a round in seconds
        '''
        self.prepareClouds()
        interval = self._configuration.getInt(
            'wdfiller.cloud.interval', 600) if interval is None else interval
        self._logger.log('cloudInit: interval: {}'.format(
            interval), base.Const.LEVEL_SUMMARY)
        no = 0
        while True:
            no += 1
            cloud = self.nextCloud()
            if cloud is None:
                break
            taskInfo = CloudTaskInfo(cloud, self)
            sliceInfo = base.Scheduler.SliceInfo(
                taskInfo, self._scheduler, count, interval, 0.1)
            self._scheduler.insertSlice(sliceInfo, int(
                interval * no / self._countClouds), 0.0)
            if startAtOnce:
                taskInfo.process(sliceInfo)
            timestamp = time.strftime(
                '%H:%M:%S', time.localtime(sliceInfo._nextCall))
            self._logger.log('cloud: {} start: {}'.format(
                cloud, timestamp), base.Const.LEVEL_LOOP)

    def filesystemInit(self, startAtOnce=False, count=None, interval=None):
        '''Initializes the filesystem sending actions.
        For each cloud: an task to send the cloud info will be inserted into the scheduler list.
        @param startAtOnce: True: the cloud infos will be sent at once too
        @param count: None or the number of rounds
        @param interval: the time of a round in seconds
        '''
        self.prepareFilesystems()
        interval = self._configuration.getInt(
            'wdfiller.filesystem.interval', 600) if interval is None else interval
        self._logger.log('filesystemInit: interval: {}'.format(
            interval), base.Const.LEVEL_SUMMARY)
        no = 0
        while True:
            no += 1
            fs = self.nextFilesystem()
            if fs is None:
                break
            taskInfo = FilesystemTaskInfo(fs, self)
            sliceInfo = base.Scheduler.SliceInfo(
                taskInfo, self._scheduler, count, interval, 0.1)
            self._scheduler.insertSlice(sliceInfo, int(
                interval * no / self._countFilesystems), 0.0)
            if startAtOnce:
                taskInfo.process(sliceInfo)
            timestamp = time.strftime(
                '%H:%M:%S', time.localtime(sliceInfo._nextCall))
            self._logger.log('filesystem: {} start: {}'.format(
                fs, timestamp), base.Const.LEVEL_LOOP)

    def daemon(self):
        '''Runs the service, a never ending loop, processing the time controlled scheduler.
        '''
        serviceName = self.shiftProgramArgument()
        if serviceName is None:
            self.abort('missing <servicename>')
        elif self.handleOptions():
            base.FileHelper.ensureDirectory(
                os.path.dirname(self.reloadRequestFile(serviceName)))
            self._scheduler = base.Scheduler.Scheduler(self._logger)
            self._webDashServer = self._configuration.getString(
                'wdfiller.url', 'http://localhost')
            self._client = net.HttpClient.HttpClient(self._logger)
            count = self._optionProcessor.valueOf('count')
            interval = self._optionProcessor.valueOf('interval')
            kinds = self._configuration.getString('wdfiller.kinds', '')
            if kinds.find('cloud') >= 0:
                self.cloudInit(True, count, interval)
            if kinds.find('filesystem') >= 0:
                self.filesystemInit(True, count, interval)
            self._stopAtOnce = False
            fileReloadRequest = self.reloadRequestFile(serviceName)
            while not self._stopAtOnce:
                hasRequest = fileReloadRequest is not None and os.path.exists(
                    fileReloadRequest)
                if hasRequest:
                    if not self.handleReloadRequest(fileReloadRequest):
                        fileReloadRequest = None
                self._scheduler.checkAndProcess()
                if not self._scheduler._slices:
                    self._logger.log(
                        'daemon: empty list: stopped', base.Const.LEVEL_SUMMARY)
                    self._stopAtOnce = True
                time.sleep(1)
            self._logger.log('daemon regulary stopped',
                             base.Const.LEVEL_SUMMARY)

    def infoOfCloud(self, path):
        '''Collects the state data of a cloud given by the path.
        @param path: the base directory of the cloud
        @return: the state info as a JSON map
        '''
        curDir = os.curdir
        os.chdir(path)
        nodes = os.listdir('data')
        users = ''
        count = 0
        for node in nodes:
            if (os.path.isdir('data/' + node) and not node.startswith('appdata_')
                    and not node.startswith('updater.') and not node.startswith('updater-')
                    and node != 'files_external'):
                users += ' ' + node
                count += 1
        logs = ''
        fnLog = 'data/nextcloud.log'
        if os.path.exists(fnLog):
            lines = []
            maxCount = 5
            with open(fnLog, 'r') as fp:
                lineNo = 0
                for line in fp:
                    lineNo += 1
                    if len(lines) >= maxCount:
                        del lines[0]
                    lines.append(line)
            for ix in range(len(lines)):
                line = lines[len(lines) - ix - 1].strip().replace('"', "'")
                logs += '{}: '.format(lineNo - ix) + line + '\\n\\n'
        users = '[{}]:'.format(count) + users
        self._processHelper.execute(
            ['hmdu', '.', 'data', 'files_trashbin'], False, True)
        duInfo = self._processHelper._output
        # = files: 100 / 6 with 0.002999 MB / 0.000234 MB dirs: 25 / 3 ignored: 0/0 in cloud_1
        # = youngest: 2020.04.01-00:16:45 cloud_1/data/admin/dir_1/file1.txt
        # = oldest:   2020.04.01-00:11:27 cloud_1/data/nextcloud.log
        # = largest:  0.000068 MB cloud_1/data/nextcloud.log
        # = trash:
        # = youngest: 2020.04.01-00:14:35 cloud_1/data/admin/files_trashbin/f2.txt
        # = oldest:   2020.04.01-00:14:28 cloud_1/data/admin/files_trashbin/f1.txt
        # = largest:  0.000039 MB cloud_1/data/admin/files_trashbin/f1.txt
        info = '\\n'.join(duInfo)
        date = time.strftime('%Y-%m-%dT%H:%M:%S', time.localtime(time.time()))
        content = base.StringUtils.fromFile(path + os.sep + '.fs.size')
        total = int('64' if content == '' else content.strip()
                    [0:-1]) * 1024 * 1024 * 1024
        # ............................1...1...2...2......3......3......4......4..........5...5...6...6
        matcher = re.match(
            r'= files: (\d+) / (\d+) with ([\d.]+) MB / ([\d.]+) MB dirs: (\d+) / (\d+)', duInfo[0])
        used = int(float(matcher.group(3)) * 1E6)
        free = int(float(matcher.group(4)) * 1E6)
        fnConfig = (self._configuration.getString('wdfiller.cloud.main.directory') + os.sep
                    + os.path.basename(path) + '/config/config.php')
        version = ''
        if os.path.exists(fnConfig):
            version1 = base.StringUtils.grepInFile(fnConfig, re.compile(
                re.compile(r"^\s*'version'\s*=>\s*'([\d.]+)")), 1, 1)
            if version1:
                version = version1[0]
        rc = '''{}
"host": "{}",
"name": "{}",
"date": "{}",
"total": {},
"used": {},
"free": {},
"trash": {},
"trashDirs": {},
"trashFiles": {},
"users": "{}",
"info": "{}",
"log": "{}",
"version": "{}"
{}
'''.format('{', self._hostname, os.path.basename(path), date, total, used, total - used, free,
           int(matcher.group(6)), int(matcher.group(2)), users, info, logs, version, '}')
        os.chdir(curDir)
        return rc

    def infoOfFilesystem(self, path):
        '''Collects the state data of a filesystem given by the path.
        @param path: the base directory of the cloud
        @return: the state info as a JSON map
        '''
        info = base.LinuxUtils.diskInfo(path)
        if info is None:
            rc = None
        else:
            name = info[0]
            if path in self._mapFilesystems:
                name = self._mapFilesystems[path] if self._mapFilesystems[path] != '' else name
            elif path.startswith('/media/'):
                name = path[7:]
            elif path == '/':
                name = 'root'
            # info:..path, total, free, available
            total, available = info[1], info[3]
            used = total - available
            rc = '{} "date": "{}", "host": "{}", "name": "{}", "total": {}, "used": {}, "free": {} {}'.format(
                '{', time.strftime('%Y-%m-%dT%H:%M:%S',
                                   time.localtime(time.time())),
                self._hostname, name, total, used, available, '}')
        return rc

    def install(self):
        '''Installs the application and the related service.
        '''
        app.BaseApp.BaseApp.install(self)
        self.createSystemDScript('satboxx', 'satboxx', 'satboxx',
                                 'satboxx', 'satboxx: sends data via REST to servers')
        self.installAsService('satboxx', True)

    def nextCloud(self):
        '''Returns the info of the next cloud.
        @return: None: no cloud available otherwise: the info about the next cloud
        '''
        if self._clouds is None:
            base1 = self._configuration.getString(
                'wdfiller.cloud.data.directory')
            self._clouds = []
            if base1 is not None:
                nodes = os.listdir(base1)
                for node in nodes:
                    full = base1 + os.sep + node
                    if os.path.isdir(full) and (self._rexprExcludedClouds is None or not self._rexprExcludedClouds.search(node)):
                        self._clouds.append(full)
            self._countClouds = len(self._clouds)
        rc = None
        if self._clouds:
            rc = self._clouds[0]
            del self._clouds[0]
        return rc

    def nextFilesystem(self):
        '''Returns the info of the next filesystem.
        @return: None: no forther filesystem is available otherwise: the info about the filesystem
        '''
        if self._filesystems is None:
            self._filesystems = []
            fsList = base.LinuxUtils.disksMounted(self._logger)
            for fsInfo in fsList:
                mount = fsInfo
                if self._rexprExcludedFilesystem is None or self._rexprExcludedFilesystem.search(mount):
                    continue
                self._filesystems.append(fsInfo)
            self._countFilesystems = len(self._filesystems)
        rc = None
        if self._filesystems:
            rc = self._filesystems[0]
            del self._filesystems[0]
        return rc

    def prepareClouds(self):
        '''Prepares some data taken from the configuration file.
        '''
        excluded = self._configuration.getString('wdfiller.cloud.excluded')
        if excluded is not None and excluded != '':
            try:
                self._logger.log('clouds: excluded: ' +
                                 excluded, base.Const.LEVEL_LOOP)
                self._rexprExcludedClouds = re.compile(excluded)
            except Exception as exc:
                self._logger.error('wrong regular expr in "wdfiller.cloud.excluded": {} [{}]'.format(
                    str(exc), str(type(exc))))

    def prepareFilesystems(self):
        '''Prepares some data taken from the configuration file.
        '''
        self._mapFilesystems = {}
        value = self._configuration.getString('wdfiller.filesystem.map', '')
        if value != '':
            fsMapping = value.split(',')
            for item in fsMapping:
                parts = item.split(':')
                if len(parts) == 2:
                    self._mapFilesystems[parts[0]] = parts[1]
                else:
                    self._logger.error(
                        'wdfiller.filesystem.map has wrong syntax: ' + value)
        excluded = self._configuration.getString(
            'wdfiller.filesystem.excluded')
        if excluded is not None and excluded != '':
            try:
                self._logger.log('filesystems: excluded: ' +
                                 excluded, base.Const.LEVEL_LOOP)
                self._rexprExcludedFilesystem = re.compile(excluded)
            except Exception as exc:
                self._logger.error('wrong regular expr in "wdfiller.filesystem.excluded": {} [{}]'.format(
                    str(exc), str(type(exc))))

    def run(self):
        '''Implements the tasks of the application
        '''
        self._hostname = self._configuration.getString('hostname', '<host>')
        if self._mainMode == 'test':
            self.test()
        elif self._mainMode == 'daemon':
            self.daemon()
        else:
            self.abort('unknown mode: ' + self._mainMode)

    def sendCloudInfo(self, pathCloud):
        '''Sends the cloud state info to the REST server.
        @param pathCloud: the full path of the cloud directory
        '''
        self._logger.log('sending cloud info to ' +
                         self._webDashServer, base.Const.LEVEL_LOOP)
        self._client.putSimpleRest(
            self._webDashServer, 'cloud', 'db', self.infoOfCloud(pathCloud))

    def sendFilesystemInfo(self, pathFilesystem):
        '''Sends the cloud state info to the REST server.
        @param pathFilesystem: the mount path of the filesystem
        '''
        self._logger.log('sending fs info to ' +
                         self._webDashServer, base.Const.LEVEL_LOOP)
        info = self.infoOfFilesystem(pathFilesystem)
        if info is None:
            self._logger.log('info not available: ' +
                             pathFilesystem, base.Const.LEVEL_LOOP)
        else:
            self._client.putSimpleRest(self._webDashServer, 'fs', 'db', info)

    def test(self):
        '''Tests a function.
        '''
        kind = self.shiftProgramArgument()
        count = base.StringUtils.asInt(self.shiftProgramArgument('1'))
        interval = base.StringUtils.asInt(self.shiftProgramArgument('1'))
        if kind is None:
            self.abort('missing kind')
        elif count is None:
            self.abort('<count> is not an integer')
        elif interval is None:
            self.abort('<interval> is not an integer')
        elif self.handleOptions():
            for ix in range(count):
                if kind == 'cloud':
                    self.testCloud(count, interval)
                elif kind in ('filesystem', 'fs'):
                    self.testFilesystems(count, interval)
                else:
                    self.abort('unknown kind: ' + kind)
                    break
                time.sleep(interval)
            base.StringUtils.avoidWarning(ix)

    def testCloud(self, count, interval):
        '''Sends a limited count of cloud infos for test purposes.
        '''
        self.prepareClouds()
        self._webDashServer = self._configuration.getString(
            'wdfiller.url', 'http://localhost')
        self._client = net.HttpClient.HttpClient(self._logger)
        for ix in range(count):
            cloud = self.nextCloud()
            if cloud is None:
                continue
            else:
                self.sendCloudInfo(cloud)
            time.sleep(interval)
        base.StringUtils.avoidWarning(ix)

    def testFilesystems(self, count, interval):
        '''Sends a limited count of cloud infos for test purposes.
        '''
        self.prepareFilesystems()
        self._webDashServer = self._configuration.getString(
            'wdfiller.url', 'http://localhost')
        self._client = net.HttpClient.HttpClient(self._logger)
        for ix in range(count):
            fs = self.nextFilesystem()
            if fs is None:
                continue
            else:
                self.sendFilesystemInfo(fs)
            time.sleep(interval)
        base.StringUtils.avoidWarning(ix)


def main(args):
    '''Main function.
    @param args: the program arguments
    '''
    snakeboxx.startApplication()
    application = SatelliteApp(args)
    application.main()


if __name__ == '__main__':
    main(sys.argv[1:])
