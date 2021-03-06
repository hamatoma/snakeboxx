#! /usr/bin/python3
'''
Created: 2020.06.24
@license: CC0 https://creativecommons.org/publicdomain/zero/1.0
@author: hm
'''
import sys
import os.path
import time
import fnmatch
import snakeboxx


import base.DirTraverser
import base.FileHelper
import app.BaseApp


class MetaData:
    '''Stores the meta data of a file.
    '''

    def __init__(self, name, statInfo, value):
        '''Adds a file to the list if it is a extremum.
        @param name: the filename
        @param statInfo: the meta data of the file
        @param value: the value of the sort criterion
        '''
        self._name = name
        self._stat = statInfo
        self._value = value


class ExtremaList:
    '''Stores a list of files sorted by a given criteria.
    '''

    def __init__(self, size, criterion, descending):
        '''Constructor.
        @param size: maximal length of the internal list
        @param criterion: t(ime), s(ize)
        @param descending: True:
        '''
        self._list = []
        self._size = size
        self._criterion = criterion
        self._descending = descending
        self._limit = None
        self._factor = -1 if self._descending else 1
        self._minLength = 0

    def merge(self, name, statInfo):
        '''Adds a file to the list if it is a extremum.
        @param name: the filename
        @param statInfo: the meta data of the file
        '''
        sortIt = False
        if len(self._list) < self._size:
            value = self._factor * \
                (statInfo.st_mtime if self._criterion == 't' else statInfo.st_size)
            self._list.append(MetaData(name, statInfo, value))
            sortIt = True
        else:
            value = self._factor * \
                (statInfo.st_mtime if self._criterion == 't' else statInfo.st_size)
            if value > self._limit:
                sortIt = True
                # replace the "smallest" element:
                self._list[0] = MetaData(name, statInfo, value)
        if sortIt:
            self._list.sort(key=lambda info: info._value)
            self._limit = self._list[0]._value

    def show(self, title, lines):
        '''Shows the list of files
        @param title: the text above the file list
        @param lines: IN/OUT: the info is stored there
        '''
        lines.append('== ' + title)
        self._list.reverse()
        for item in self._list:
            info = base.FileHelper.listFile(
                item._stat, item._name, self._criterion == 't', True)
            lines.append(info)


class DirApp(app.BaseApp.BaseApp):
    '''Performs some tasks with text files: searching, modification...
    '''

    def __init__(self, args):
        '''Constructor.
        @param args: the program arguments, e.g. ['test', 'a@bc.de']
        '''
        app.BaseApp.BaseApp.__init__(self, 'DirApp', args, None, 'dirboxx')
        self._traverser = None
        self._processor = None
        self._hostname = None

    def adjust(self):
        '''Adjusts the file modifcation datetime in a given directory.
        '''
        self._resultLines = []
        source = self.shiftProgramArgument()
        target = self.shiftProgramArgument()
        if target is None:
            self.abort('too few arguments')
        elif not os.path.isdir(source):
            self.abort(f'not a directory: {source}')
        elif not os.path.isdir(target):
            self.abort(f'not a directory: {target}')
        if self.handleOptions():
            pattern = self._optionProcessor.valueOf('pattern')
            self.adjustDir(pattern, source, target)

    def adjustDir(self, pattern, source, target):
        '''For all files in target: if a file exists in source the modification time is transfered from source to target.
        @param source: the directory with files having the needed modification time
        @param target: the directory with the files to change
        @param pattern: a shell pattern for the files to process, e.g. "*.jpg"
        '''
        info = f'= {target}:'
        self._resultLines.append(info)
        self._logger.log(info, base.Const.LEVEL_DETAIL)
        dirs = []
        for file in os.listdir(target):
            full = os.path.join(target, file)
            if os.path.isdir(full):
                if self._optionProcessor.valueOf('recursive'):
                    dirs.append(file)
            elif not fnmatch.fnmatch(file, pattern):
                info = f'{file} ignored'
                self._resultLines.append(info)
                self._logger.log(info, base.Const.LEVEL_FINE)
            else:
                src = os.path.join(source, file)
                if os.path.exists(src):
                    timeSrc = os.stat(src).st_mtime
                    timeTrg = os.stat(full).st_mtime
                    base.FileHelper.setModified(full, timeSrc)
                    info = f'{file}: {time.strftime("%Y.%m.%d-%H:%M:%S", time.localtime(timeTrg))} -> {time.strftime("%Y.%m.%d-%H:%M:%S", time.localtime(timeSrc))}'
                    self._resultLines.append(info)
                    self._logger.log(info, base.Const.LEVEL_LOOP)
        for item in dirs:
            self.adjustDir(pattern, os.path.join(source, item), os.path.join(target, item))

    def buildConfig(self):
        '''Creates an useful configuration example.
        '''
        content = '''# created by DirApp
logfile=/var/log/local/dirboxx.log
'''
        self.buildStandardConfig(content)

    def buildUsage(self):
        '''Builds the usage message.
        '''
        self._usageInfo.appendDescription('''APP-NAME <global-opts> <mode> [<options>]
 Searching and modifying in text files.
''')
        self._usageInfo.addMode('describe-rules', '''
 Describes the syntax and the meaning of the rules
 ''', '''APP-NAME describe-rules
''')
        self._usageInfo.addMode('extrema', '''extrema [<what> [<directory>]] [<options>]
 Find the oldest, youngest, largest, smallest files.
 <what>: 'all' or a comma separated list of requests: o or oldest, y or youngest, l or largest, s or smallest
 <directory>: the base directory for searching. Default: the current directory
 ''', '''APP-NAME extrema o,y,l
APP-NAME extrema oldest,largest /home --exclude-dir=.git
''')

        self._usageInfo.addMode('list', '''list [<pattern>] [<options>]
 Displays the metadata (size, date/time...) of the specified dirs/files.
 <pattern>: defines the files/dirs to display. Default: the current directory
 ''', '''APP-NAME list
APP-NAME list *.txt --exclude-dirs=.git --file-type=fl --min-size=20k --younger-than=2020.01.30-05:00:00
''')
        self._usageInfo.addMode('adjust', '''adjust <source-dir> <target-dir> [<options>]
 Search for each file in <target-dir> a file with the same name in <source-dir> and sets the modification datetime of the 2nd file to the first. 
 <source-dir>: the modifiction datetime is taken from the file in this directory 
 <target-dir>: files in this directory will be changed (modifiction datetime) 
 ''', '''APP-NAME list
APP-NAME adjust Bilder Bilder/fullsize
APP-NAME adjust /tmp/pic/eastern /home/pictures/eastern/fullhd
''')

    def buildUsageOptions(self, mode=None):
        '''Adds the options for a given mode.
        @param mode: None or the mode for which the option is added
        '''
        def add(mode, opt):
            self._usageInfo.addModeOption(mode, opt)

        if mode is None:
            mode = self._mainMode
        if mode == 'describe-rules':
            pass
        elif mode == 'extrema':
            base.DirTraverser.addOptions(mode, self._usageInfo)
            add(mode, base.UsageInfo.Option('count', None,
                                            'max. count of elements in the extrema list', 'int', 5))
            add(mode, base.UsageInfo.Option('min-length', None,
                                            'relevant for "smallest": only file larger than <size> will be inspected', 'int', 0))
        elif mode == 'list':
            base.DirTraverser.addOptions(mode, self._usageInfo)
        elif mode == 'adjust':
            add(mode, base.UsageInfo.Option('pattern', 'p',
                                            'specifies the filenames to change, with shell wildcards: "*": any string "?": one char...', 'string', '*'))
            add(mode, base.UsageInfo.Option('recursive', 'r',
                                            'files will be processed in subdirectories', 'bool'))

    def extrema(self):
        '''Searches the "extremest" (youngest, oldest, ...) files.
        '''
        what = self.shiftProgramArgument('o,y,l,s')
        if what == 'all':
            what = 'o,y,l,s'
        directory = self.shiftProgramArgument('.')
        what1 = ''
        for item in what.split(','):
            if item in ('o', 'y', 'l', 's', 'oldest', 'youngest', 'largest', 'smallest'):
                what1 += item[0]
            else:
                self.argumentError(
                    'unknown item in <what>: {} use oldest, youngest, largest or smallest'.format(item))
        if self.handleOptions():
            self._traverser = base.DirTraverser.buildFromOptions(
                directory, self._usageInfo, 'extrema')
            count = self._optionProcessor.valueOf('count')
            oldest = ExtremaList(count, 't', True) if what1.find(
                'o') >= 0 else None
            youngest = ExtremaList(
                count, 't', False) if what1.find('y') >= 0 else None
            largest = ExtremaList(count, 's', False) if what1.find(
                'l') >= 0 else None
            smallest = ExtremaList(count, 's', True)
            smallest._minLength = self._optionProcessor.valueOf('min-length')
            for filename in self._traverser.next(self._traverser._directory, 0):
                if oldest is not None:
                    oldest.merge(filename, self._traverser._statInfo)
                if youngest is not None:
                    youngest.merge(filename, self._traverser._statInfo)
                if not self._traverser._isDir:
                    if largest is not None:
                        largest.merge(filename, self._traverser._statInfo)
                    if smallest is not None and (
                            smallest._minLength is None
                            or self._traverser._statInfo.st_size >= smallest._minLength):
                        smallest.merge(filename, self._traverser._statInfo)
            summary = self._traverser.summary()
            self._logger.log(summary, base.Const.LEVEL_SUMMARY)
            self._resultLines = summary.split('\n')
            if oldest is not None:
                oldest.show('the oldest files:', self._resultLines)
            if smallest is not None:
                smallest.show('the smallest files:', self._resultLines)
            if youngest is not None:
                youngest.show('the youngest files:', self._resultLines)
            if largest is not None:
                largest.show('the largest files:', self._resultLines)
            print('\n'.join(self._resultLines))

    def list(self):
        '''Displays the meta data of the specified files/dirs.
        '''
        self._resultLines = []
        directory = self.shiftProgramArgument('.')
        if self.handleOptions():
            self._traverser = base.DirTraverser.buildFromOptions(
                directory, self._usageInfo, 'list')
            for filename in self._traverser.next(self._traverser._directory, 0):
                info = base.FileHelper.listFile(
                    self._traverser._statInfo, filename, orderDateSize=True, humanReadable=True)
                self._resultLines.append(info)
                print(info)
            summary = self._traverser.summary()
            self._logger.log(summary, base.Const.LEVEL_SUMMARY)
            self._resultLines += summary.split('\n')

    def run(self):
        '''Implements the tasks of the application.
        '''
        self._hostname = self._configuration.getString('hostname', '<host>')
        if self._mainMode == 'adjust':
            self.adjust()
        elif self._mainMode == 'extrema':
            self.extrema()
        elif self._mainMode == 'list':
            self.list()
        else:
            self.abort('unknown mode: ' + self._mainMode)


def main(args):
    '''Main function.
    @param args: the program arguments
    '''
    snakeboxx.startApplication()
    application = DirApp(args)
    application.main()


if __name__ == '__main__':
    main(sys.argv[1:])
