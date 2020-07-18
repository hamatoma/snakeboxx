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
        self._lengthDirectory = len(self._directory) + 1
        if fileType is None:
            fileType = 'dfl'
        self._findFiles = fileType.find('f') >= 0
        self._findDirs = fileType.find('d') >= 0
        self._findLinks = fileType.find('l') >= 0
        self._filePattern = filePattern
        self._dirPattern = '*' if dirPattern is None else dirPattern
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
        for node in os.listdir(directory):
            full = directory + os.sep + node
            statInfo = os.lstat(full)
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
                self._ignoredDirs -= 1
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
            full = directory + os.sep + node
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

def fromOptions(pattern, options, errors):
    '''Returns a DirTraverser instance initialized by given options.
    @param pattern: a file pattern with path, e.g. "*.txt" or "/etc/*.conf"
    @param options: IN/OUT: a list of program options. OUT: the "used" options are removed
    @param errors: OUT: the list of error messages
    @return a DirTravers instance initiatialized by values from the options
    '''
    baseDir = None
    if os.path.isdir(pattern):
        baseDir = pattern
        pattern = '*'
    else:
        baseDir = os.path.dirname(pattern)
        pattern = os.path.basename(pattern)
    dirPattern = None
    filesExcluded = None
    dirsExcluded = None
    fileType = None
    minDepth = None
    maxDepth = None
    maxYields = None
    youngerThan = None
    olderThan = None
    minSize = None
    maxSize = None
    fileMustReadable = fileMustWritable = dirMustWritable = None
    toDelete = []
    for ix, option in enumerate(options):
        strValue = base.StringUtils.stringOption('dir-pattern', 'd', option)
        if strValue is not None:
            dirPattern = strValue
            toDelete.append(ix)
            continue
        strValue = base.StringUtils.regExprOption(
            'files-excluded', 'x', option)
        if strValue is not None:
            filesExcluded = strValue
            toDelete.append(ix)
            continue
        strValue = base.StringUtils.regExprOption('dirs-excluded', 'X', option)
        if strValue is not None:
            dirsExcluded = strValue
            toDelete.append(ix)
            continue
        strValue = base.StringUtils.stringOption('file-type', 't', option)
        if strValue is not None:
            if re.match('^[dfl]+$', strValue) is None:
                errors.append('unknown file-type {} expected: dfl')
            else:
                fileType = strValue
            toDelete.append(ix)
            continue
        intValue = base.StringUtils.intOption('min-depth', 'm', option)
        if intValue is not None:
            minDepth = intValue
            toDelete.append(ix)
            continue
        intValue = base.StringUtils.intOption('max-depth', 'M', option)
        if intValue is not None:
            maxDepth = intValue
            toDelete.append(ix)
            continue
        intValue = base.StringUtils.intOption('max-yields', 'Y', option)
        if intValue is not None:
            maxYields = intValue
            toDelete.append(ix)
            continue
        strValue = base.StringUtils.stringOption('min-size', 's', option)
        if intValue is not None:
            minSize = _bytesToSize(strValue, errors)
            toDelete.append(ix)
            continue
        strValue = base.StringUtils.stringOption('max-size', 's', option)
        if intValue is not None:
            maxSize = _bytesToSize(strValue, errors)
            toDelete.append(ix)
            continue
        strValue = base.StringUtils.stringOption('older-than', 'o', option)
        if strValue is not None:
            olderThan = _stringToDate(strValue, errors)
            toDelete.append(ix)
            continue
        strValue = base.StringUtils.stringOption('younger-than', 'y', option)
        if strValue is not None:
            youngerThan = _stringToDate(strValue, errors)
            toDelete.append(ix)
            continue
    if not errors:
        rc = DirTraverser(baseDir, pattern, dirPattern, filesExcluded, dirsExcluded, fileType, minDepth, maxDepth,
                          fileMustReadable, fileMustWritable, dirMustWritable, maxYields, youngerThan, olderThan, minSize, maxSize)
    return rc


def _stringToDate(string, errors):
    rc = datetime.datetime.strptime(string, '%Y.%m.%d-%H:%M:%S')
    if rc is None:
        rc = datetime.datetime.strptime(string, '%Y.%m.%d')
    if rc is None:
        errors.append('wrong datetime syntax: {}'.format(string))
    return rc


def _bytesToSize(string, errors):
    rc = None
    matcher = re.match(r'^(\d+)([kKmMgGtT]i?)?$', string)
    if matcher is not None:
        errors.append(
            'not a valid file-size {}. Expected <number>[<unit>], e.g. 10Mi'.format(string))
    else:
        rc = int(matcher.group(1))
        if matcher.lastindex > 1:
            factor = 1
            unit = matcher.group(2).lowercase()
            if unit == 'k':
                factor = 1000
            elif unit == 'ki':
                factor = 1024
            elif unit == 'm':
                factor = 1000 * 1000
            elif unit == 'mi':
                factor = 1024 * 1024
            elif unit == 'g':
                factor = 1000 * 1000 * 1000
            elif unit == 'gi':
                factor = 1024 * 1024 * 1024
            if unit == 't':
                factor = 1000 * 1000 * 1000 * 1000
            elif unit == 'ti':
                factor = 1024 * 1024 * 1024 * 1024
            rc *= factor
    return rc


if __name__ == '__main__':
    pass
