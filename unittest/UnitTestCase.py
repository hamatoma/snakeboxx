'''
Created on 12.04.2018

@author: hm
'''

import re
import traceback
import os.path
import tempfile
import posix
import fnmatch

import base.FileHelper
import base.MemoryLogger

class UnitTestAppInfo:
    def __init__(self, usage):
        self._usage = usage

class UnitTestCase:
    def __init__(self):
        self._userId = posix.getuid()
        self._isRoot = self._userId == 0
        self._inTestSuite = False
        self._errors = 0
        self._summary = None
        self._name = type(self).__name__
        self._asserts = 0
        self._application = UnitTestAppInfo(self.usage)
        self._logger = base.MemoryLogger.MemoryLogger(True)
        self._silentLogger = base.MemoryLogger.MemoryLogger(False)
        base.FileHelper.setLogger(self._logger)

    def _finish(self):
        '''The last action of a test case.
        Should be overwritten by sub classes
        '''
 
    def _describeDifference(self, str1, str2, prefix = ''):
        '''Logs the difference of two strings.
        @param str1: first string to compare
        @param str2: second string to compare
        @param prefix: '' or a prefix
        @return: a string describing the difference
        '''
        count1 = len(str1)
        count2 = len(str2)
        ixDiff = -1
        for ix in range(min(count1, count2)):
            if str1[ix] != str2[ix]:
                ixDiff = ix
                break
        if ixDiff != -1:
            rc = '+++ {:s}different at pos {:d}: {:s}/{:s}\n'.format(prefix, ixDiff + 1, str1[ixDiff:ixDiff+5], str2[ixDiff:ixDiff+5])
        elif count1 > count2:
            rc = '+++ expected is longer:\n'
        else:
            rc = '+++ expected is shorter:\n'
        rc += str1 + '\n' + str2
        if ixDiff != -1:
            rc += '\n' + ('=' * ixDiff) + '^'
        return rc

    def assertDirExists(self, current):
        '''Tests whether a given directory exists.
        @param current: the directory to inspect
        @returns: True: the directory exists
        '''
        self._asserts += 1
        rc = True
        if not os.path.exists(current):
            rc = self.error('directory does not exist: ' + current)
        elif not os.path.isdir(current):
            rc = self.error('file {} exists but it is not a directory'.format(current))
        return rc

    def assertEquals(self, expected, current):
        '''Tests whether two values are equal.
        @param expected: the expected value
        @param current: the value to test
        @return: True: values are equal
        '''
        rc = False
        self._asserts += 1
        if type(expected) != type(current):
            self.error('different types: ' + str(type(expected)) + ' / ' + str(type(current)))
        else:
            rc = expected == current
            if not rc:
                if type(expected) is str:
                    if expected.find('\n') < 0:
                        self.error(self._describeDifference(expected, current))
                    else:
                        listExpected = expected.splitlines()
                        listCurrent = current.splitlines()
                        ixDiff = -1
                        for ix in range(min(len(listExpected), len(listCurrent))):
                            if listExpected[ix] != listCurrent[ix]:
                                self.error(self._describeDifference(listExpected[ix], listCurrent[ix], 'in line {:d}: '.format(ix + 1)))
                                ixDiff = ix
                                break
                        if ixDiff == -1 and len(listExpected) != len(listCurrent):
                            if len(listExpected) < len(listCurrent):
                                msg = 'expected has fewer lines: {:d}/{:d}\n'.format(len(listExpected), len(listCurrent)) + listCurrent[len(listExpected)]
                            else:
                                msg = 'expected has more lines: {:d}/{:d}\n'.format(len(listExpected), len(listCurrent)) + listExpected[len(listCurrent)]
                            self.error(msg)
                elif type(expected) is int:
                    self.error('different: {:d}/{:d} [0x{:x}/0x{:x}]'.format(expected, current, expected, current))
                else:
                    self.error('different: {:s} / {:s}'.format(str(expected), str(current)))
        return rc

    def assertFalse(self, current):
        '''Tests whether a value is False.
        @param current: value to test
        @returns: True: the value is False
        '''
        rc = True
        self._asserts += 1
        if current != False:
            rc = self.error('+++ False expected, found: ' + str(current))
        return rc

    def assertFileContent(self, expectedContent, currentFile):
        '''Compares a given string with an expected file content.
        @param currentFile: the name of the file with the expected content, e.g. 'data/abc.xyz'
        @param expectedContent: the content to compare
        @returns: True: file content is the expected
        '''
        rc = True
        self._asserts += 1
        full = currentFile if currentFile.startswith(os.sep) else os.path.dirname(__file__) + os.sep + currentFile
        if not os.path.exists(full):
            rc =self.error('missing file: ' + currentFile)
        else:
            with open(full, 'r') as fp:
                current = fp.read()
            rc = self.assertEquals(expectedContent, current)
            if not rc:
                tempFile = self.tempFile(os.path.basename(currentFile))
                with open(tempFile, "w") as fp:
                    fp.write(expectedContent)
                self.log('meld {} {}'.format(tempFile, full))
        return rc

    def assertFileContains(self, expected, currentFile):
        '''Tests whether a given file contains a given content.
        @param expected: content to search. May be a string or a re.RegExpr instance
        @param currentFile: file to inspect
        @returns: True: the file contains the expected string
        '''
        rc = True
        self._asserts += 1
        if not os.path.isfile(currentFile):
            rc = self.error('missing file ' + currentFile)
        else:
            found = False
            with open(currentFile) as fp:
                # lineNo = 0
                for line in fp:
                    #lineNo += 1
                    #if lineNo == 126:
                    #    lineNo = 126
                    if type(expected) == str:
                        if line.find(expected) >= 0:
                            found = True
                            break
                    else:
                        if expected.search(line) is not None:
                            found = True
                            break
            if not found:
                text = expected if type(expected) == str else expected.pattern
                rc = self.error('missing content {:s} in {:s}'.format(text[0:20], currentFile))
        return rc

    def assertFileExists(self, filename):
        '''Tests whether a given file exists.
        @param filename: the name of the file to test
        @returns: True: the file exists
        '''
        rc = True
        self._asserts += 1
        if not os.path.exists(filename):
            rc = self.error('file does not exist: ' + filename)
        return rc

    def assertFileNotContains(self, unexpectedContent, currentFile):
        '''Tests whether a given file contains not a given content.
        @param unexpectedContent: content to search
        @param currentFile: file to inspect
        '''
        rc = True
        self._asserts += 1
        if not os.path.isfile(currentFile):
            rc = self.error('missing file ' + currentFile)
        else:
            found = False
            with open(currentFile) as fp:
                for line in fp:
                    if line.find(unexpectedContent) >= 0:
                        found = True
                        break
            if found:
                rc = self.error('unexpected content {:s} in {:s}'.format(unexpectedContent[0:20], currentFile))
        return rc

    def assertFileNotExists(self, filename):
        '''Tests whether a given file does not exist.
        @param filename: the name of the file to test
        @returns: True: the file does not exist
        '''
        rc = True
        self._asserts += 1
        if os.path.exists(filename):
            rc = self.error('file exists: ' + filename)
        return rc

    def assertMatches(self, expectedRegExpr, current, flags=0):
        '''Tests whether a string matches a given regular expression.
        @param expectedRegExpr: regular expression
        @param current: string to test
        @param flags: flags for re.match, e.g. re.IGNORECASE or re.MULTILINE
        @returns: True: the value matches the expected
        '''
        rc = True
        self._asserts += 1
        if not re.search(expectedRegExpr, current, flags):
            rc = self.error('+++ does not match\n' + expectedRegExpr + '\n' + current)
        return rc

    def assertNodeExists(self, path, nodePattern):
        '''Tests whether at least one file exists in a given path with a given node pattern.
        @param path: the directory to inspect
        @param nodePattern: a pattern with unix wildcards to inspect
        @return True: node found
        '''
        nodes = os.listdir(path)
        found = False
        for node in nodes:
            if fnmatch.fnmatch(node, nodePattern):
                found = True
                break
        if not found:
            self.error('node {} not found in {}'.format(nodePattern, path))
        return found

    def assertNone(self, current):
        '''Tests whether a value is None.
        @param current: value to test
        @returns: True: the value is None
        '''
        rc = True
        self._asserts += 1
        if current is not None:
            rc = self.error('+++ None expected, found: ' + str(current))
        return rc

    def assertNotNone(self, current):
        '''Tests whether a value is not None.
        @param current: value to test
        @returns: True: the value is not None
        '''
        self._asserts += 1
        if current is None:
            self.error('+++ unexpected None found')

    def assertTrue(self, current):
        '''Tests whether a value is True.
        @param current: value to test
        @returns: True: the value is True
        '''
        rc = True
        self._asserts += 1
        if current != True:
            rc = self.error('+++ True expected, found: ' + str(current))
        return rc

    def clearDirectory(self, path):
        '''Removes all files and subdirs in a given directory.
        @param path: name of the directory
        '''
        base.FileHelper.clearDirectory(path)

    def ensureDirectory(self, directory):
        '''Ensures that the given directory exists.
        @param directory: the complete name
        @return: None: could not create the directory
            otherwise: the directory's name
        '''
        rc = base.FileHelper.ensureDirectory(directory)
        return rc

    def ensureFileDoesNotExist(self, filename):
        '''Ensures that a file does not exist.
        @param filename: the file to delete if it exists.
        '''
        base.FileHelper.ensureFileDoesNotExist(filename)

    def error(self, message):
        '''Displays an error with backtrace.
        @param message: error message
        @returns: False
        '''
        self._errors += 1
        print(message)
        info = traceback.extract_stack()
        # ignore runtime methods:
        while len(info) > 1 and (info[0].filename.find('/pysrc/') > 0 or info[0]._line.startswith('tester.run()')
                or info[0].filename.find('UnitTestCase.py') > 0 and info[0]._line.startswith('method()')):
            del info[0]
        # ignore UnitTest internals:
        length = len(info)
        while length > 1 and info[length - 1].filename.find('UnitTestCase.py') > 0:
            del info[length - 1]
            length -= 1
        for entry in info:
            print('{:s}:{:d} {:s}'.format(entry.filename, entry.lineno, entry.line))
        return False

    def getSummary(self):
        '''Return the summary message.
        @return the summary message
        '''
        return self._summary

    def log(self, message):
        '''Displays a message
        @param message: message
        '''
        print(message)

    def run(self):
        '''Searches the methods starting with 'test' and call them.
        '''
        for item in self.__dir__():
            if item.startswith('test'):
                method = getattr(self, item)
                print('= ' + item)
                method()
        self._summary = '=== unit {:s}: {:d} assert(s) with {:d} error(s)'.format(self._name, self._asserts, self._errors)
        print(self._summary)
        self._finish()

    def setInTestSuite(self, value):
        '''Sets the attribute.
        @param value: the new value of _inTestSuite
        '''
        self._inTestSuite = value

    def tempDir(self, node, subdir = None):
        '''Builds the name of a directory and ensures that the directory exists.
        @param node: the directory's name (without path)
        @param subdir: None or the name of a directory inside the temp dir
        @return: None: cannot create directory
                otherwise: the name of an existing temporary directory (with path)
        '''
        rc = tempfile.gettempdir()
        if subdir is not None:
            rc += os.sep + subdir
        if node is not None:
            if rc[-1] != os.sep:
                rc += os.sep
            rc += node
        rc = self.ensureDirectory(rc)
        return rc

    def tempFile(self, node, subdir = None, subdir2 = None):
        '''Builds the name of a temporary file and ensures that the parent directories exist.
        @param node: the file's name (without path)
        @param subdir: None or the name of a directory inside the temp dir
        @param subdir2: None or the name of a directory inside subdir
        @return: the name of a temporary file (with path), e.g. /tmp/subdir/subdir2/node
        '''
        rc = tempfile.gettempdir() + os.sep
        if subdir is not None:
            rc += subdir
            rc = self.ensureDirectory(rc)
            if subdir[-1] != os.sep:
                rc += os.sep
            if subdir2 is not None:
                rc += subdir2
                self.ensureDirectory(rc)
                if subdir2[-1] != os.sep:
                    rc += os.sep
        rc += node
        return rc

    def usage(self, message):
        print(message)
        self.assertFalse(True)

    def xtestMyself(self):
        self.assertEquals(3, 4)
        self.assertEquals('Hello', 'Hallo')
        self.assertEquals('abc\nhallo', 'abc\nhello')
        self.assertNone('not none')
        self.assertNotNone(None)

if __name__ == '__main__':
    tester = UnitTestCase()
    tester.run()
