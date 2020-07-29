'''
Created: 2020.06.24
@license: CC0 https://creativecommons.org/publicdomain/zero/1.0
@author: hm
'''
import fnmatch
import os.path
import stat
import re
import datetime

#import base.FileHelper
import base.Const
import base.StringUtils


class DirTraverser:
    '''Traverse a directory tree and return specified filenames.
    '''

    def __init__(self, directory, filePattern='*', dirPattern='*',
                 reFileExcludes=None, reDirExcludes=None, fileType=None,
                 minDepth=0, maxDepth=None, fileMustReadable=False, fileMustWritable=False,
                 dirMustWritable=False, maxYields=None, youngerThan=None, olderThan=None,
                 minSize=0, maxSize=None):
        '''Constructor.
        @param directory: the start directory
        @param filePattern: the shell pattern of the files to find
        @param dirPattern: the shell pattern of the dirs to find. Note: selects only the returned dirs, not the processed
        @param reFileExcludes: None or the regular expression for files to exclude
        @param reDirExcludes: None or the regular expression for directories to exclude
        @param nodeType: a string with the filetypes to find: d(irectory) f(ile) l(ink), e.g. 'dfl'
        @param minDepth: the minimum depth of the processed files: 1 means only files in subdirectories will be found
        @param maxDepth: the maximum depth of the processed files: 0 means only the base directory is scanned
        @param fileMustReadable: True: a file will only yielded if it is readable
        @param fileMustWritable: True: a file will only yielded if it is writable
        @param dirMustWritable: True: a directory will only processed if it is writable
        @param maxYields: None or after this amount of yields the iteration stops
        @param youngerThan: None or the modification file time must be greater or equal this
        @param olderThan: None or the modification file time must be lower or equal this
        @param minSize: None or only files larger than that will be found
        @param maxSize: None or only files smaller than that will be found
        '''
        self._directory = directory if directory != '' else '.'
        # +1: the preceeding slash
        self._lengthDirectory = 0 if directory == os.sep else len(
            self._directory) + 1
        if fileType is None:
            fileType = 'dfl'
        self._findFiles = fileType.find('f') >= 0
        self._findDirs = fileType.find('d') >= 0
        self._findLinks = fileType.find('l') >= 0
        self._filePattern = filePattern
        self._dirPattern = dirPattern
        self._reDirExcludes = reDirExcludes
        self._reDirExcludes = None if reDirExcludes is None else (
            re.compile(reDirExcludes, base.Const.IGNORE_CASE) if isinstance(reDirExcludes, str) else
            reDirExcludes)
        self._reFileExcludes = None if reFileExcludes is None else (
            re.compile(reFileExcludes, base.Const.IGNORE_CASE) if isinstance(reFileExcludes, str) else
            reFileExcludes)
        self._fileMustReadable = fileMustReadable
        self._fileMustWritable = fileMustWritable
        self._dirMustWritable = dirMustWritable
        self._minSize = minSize if minSize is not None else 0
        # 2**63-1:
        self._maxSize = maxSize
        # the stat info about the current file
        self._fileInfo = None
        self._fileFullName = None
        self._fileNode = None
        self._fileRelativeName = None
        # the stat info about the current directory
        self._dirInfo = None
        self._dirFullName = None
        self._dirRelativeName = None
        self._dirNode = None
        self._minDepth = minDepth if minDepth is not None else 0
        self._maxDepth = maxDepth if maxDepth is not None else 900
        self._youngerThan = None if youngerThan is None else youngerThan.timestamp()
        self._olderThan = None if olderThan is None else olderThan.timestamp()
        # 2.14*10E9
        self._maxYields = maxYields if maxYields is not None else 0x7fffffff
        self._yields = 0
        self._countFiles = 0
        self._bytesFiles = 0
        self._countDirs = 0
        self._ignoredDirs = 0
        self._ignoredFiles = 0
        self._euid = os.geteuid()
        self._egid = os.getegid()
        self._statInfo = None
        self._node = None
        self._isDir = False

    def asList(self):
        '''Returns a list of all found files (filenames with relative path).
        @return: []: nothing found otherwise: the list of all filenames
        '''
        rc = []
        for item in self.next(self._directory, 0):
            rc.append(item)
        return rc

    def next(self, directory, depth):
        '''Implements a generator which returns the next specified file.
        Note: this method is recursive (for each directory in depth)
        The traversal mode: yields all files and directories and than enters the recursivly the directories
        @param directory: the directory to process
        @param depth: the current file tree depth
        @return: the next specified file (the filename with path relative to _directory)
        '''
        self._countDirs += 1
        dirs = []
        directory2 = '' if directory == os.sep else directory
        for node in os.listdir(directory):
            full = directory2 + os.sep + node
            self._statInfo = statInfo = os.lstat(full)
            self._isDir = stat.S_ISDIR(statInfo.st_mode)
            if self._isDir:
                self._ignoredDirs += 1
                if (self._reDirExcludes is not None and self._reDirExcludes.search(node)):
                    continue
                if not base.LinuxUtils.isReadable(statInfo, self._euid, self._egid):
                    continue
                elif self._dirMustWritable and not base.LinuxUtils.isReadable(statInfo, self._euid, self._egid):
                    continue
                elif depth < self._maxDepth:
                    dirs.append(node)
                if depth < self._minDepth:
                    continue
                if depth < self._maxDepth:
                    self._ignoredDirs -= 1
                if self._dirPattern is None:
                    continue
                if not self._findDirs:
                    continue
                if self._dirPattern == '*' or fnmatch.fnmatch(node, self._dirPattern):
                    self._dirInfo = statInfo
                    self._dirNode = node
                    self._dirFullName = full
                    self._dirRelativeName = full[self._lengthDirectory:]
                    yield self._dirRelativeName
                    self._yields += 1
                    if self._yields >= self._maxYields:
                        return
            else:
                # tentative: because of "continue"
                self._ignoredFiles += 1
                if os.path.islink(full):
                    if not self._findLinks:
                        continue
                elif not self._findFiles:
                    continue
                if statInfo.st_size < self._minSize or (self._maxSize is not None and statInfo.st_size > self._maxSize):
                    continue
                if self._youngerThan is not None and statInfo.st_mtime < self._youngerThan:
                    continue
                if self._olderThan is not None and statInfo.st_mtime > self._olderThan:
                    continue
                if self._filePattern != '*' and not fnmatch.fnmatch(node, self._filePattern):
                    continue
                if self._reFileExcludes is not None and self._reFileExcludes.search(node):
                    continue
                if self._fileMustReadable and not base.LinuxUtils.isReadable(statInfo, self._euid, self._egid):
                    continue
                if self._fileMustWritable and not base.LinuxUtils.isWritable(statInfo, self._euid, self._egid):
                    continue
                if depth < self._minDepth:
                    continue
                self._ignoredFiles -= 1
                self._statInfo = statInfo
                self._countFiles += 1
                self._bytesFiles += self._statInfo.st_size
                self._fileFullName = full
                self._node = node
                self._fileRelativeName = full[self._lengthDirectory:]
                yield full
                self._yields += 1
                if self._yields >= self._maxYields:
                    return
        for node in dirs:
            full = directory2 + os.sep + node
            yield from self.next(full, depth + 1)

    def summary(self):
        '''Returns the info about the traverse process: count of files...
        @return: the infotext
        '''
        rc = 'dir(s): {} file(s): {} / {}\nignored: dir(s): {} file(s): {}'.format(
            self._countDirs, self._countFiles,
            base.StringUtils.formatSize(self._bytesFiles),
            self._ignoredDirs, self._ignoredFiles)
        return rc


def addOptions(mode, usageInfo):
    '''Adds the options for controlling the DirTraverser instance to a UsageInfo instance.
    @param: the options will be assigned to this mode
    @param: usageInfo: the options will be added to that
    '''
    option = base.UsageInfo.Option('dirs-pattern', 'f', 'if a directory matches this regular expression it will be not processed',
                                   'regexpr')
    usageInfo.addModeOption(mode, option)
    option = base.UsageInfo.Option('dirs-excluded', 'X', 'if a directory matches this regular expression it will be not processed',
                                   'regexpr')
    usageInfo.addModeOption(mode, option)
    option = base.UsageInfo.Option(
        'file-type', 't', 'only files with this filetype will be found: d(irectory) f(ile) l(link)')
    usageInfo.addModeOption(mode, option)
    option = base.UsageInfo.Option(
        'min-depth', 'm', 'only subdirectories with that (or higher) depth will be processed', 'int', 0)
    usageInfo.addModeOption(mode, option)
    option = base.UsageInfo.Option(
        'min-depth', 'm', 'only subdirectories with that (or lower) depth will be processed', 'int')
    option = base.UsageInfo.Option(
        'max-yields', 'Y', 'only that number of matching files will be found', 'int')
    usageInfo.addModeOption(mode, option)
    option = base.UsageInfo.Option(
        'min-size', 's', 'only larger files than that will be found, e.g. --min-size=2Gi', 'size', 0)
    usageInfo.addModeOption(mode, option)
    option = base.UsageInfo.Option(
        'max-size', 'S', 'only smaller files than that will be found, e.g. --max-size=32kByte', 'size')
    usageInfo.addModeOption(mode, option)
    option = base.UsageInfo.Option(
        'older-than', 'o', 'only files older than that will be found, e.g. --older-than=2020.7.3-4:32', 'datetime')
    usageInfo.addModeOption(mode, option)
    option = base.UsageInfo.Option(
        'younger-than', 'y', 'only files younger than that will be found, e.g. --younger-than=2020.7.3-4:32', 'datetime')
    usageInfo.addModeOption(mode, option)


def buildFromOptions(pattern, usageInfo, mode):
    '''Returns a DirTraverser instance initialized by given options.
    @param pattern: a file pattern with path, e.g. "*.txt" or "/etc/*.conf"
    @param usageInfo: contains the options built by addOptions()
    @param mode: specifies the storage in usageInfo
    @return a DirTravers instance initiatialized by values from the options
    '''
    def v(name):
        return usageInfo._optionProcessors[mode].valueOf(name)
    baseDir = None
    if os.path.isdir(pattern):
        baseDir = pattern
        pattern = '*'
    else:
        baseDir = os.path.dirname(pattern)
        pattern = os.path.basename(pattern)
    fileMustReadable = fileMustWritable = dirMustWritable = None
    rc = DirTraverser(baseDir, pattern, v('dir-pattern'), v('files-excluded'), v('dirs-excluded'),
                      v('file-type'), v('min-depth'), v('max-depth'),
                      fileMustReadable, fileMustWritable, dirMustWritable,
                      v('max-yields'), v('younger-than'), v('older-than'), v('min-size'), v('max-size'))
    return rc


def _stringToDate(string, errors):
    rc = datetime.datetime.strptime(string, '%Y.%m.%d-%H:%M:%S')
    if rc is None:
        rc = datetime.datetime.strptime(string, '%Y.%m.%d')
    if rc is None:
        errors.append('wrong datetime syntax: {}'.format(string))
    return rc


if __name__ == '__main__':
    pass
