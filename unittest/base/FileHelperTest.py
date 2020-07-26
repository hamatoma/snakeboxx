'''
Created on 12.04.2018

@author: hm
'''
import sys
print(sys.path)
from unittest.UnitTestCase import UnitTestCase

import shutil
import datetime
import time
import os.path

import base.MemoryLogger
import base.FileHelper
import base.StringUtils

DEBUG = False

class FileHelperTest(UnitTestCase):
    def __init__(self):
        UnitTestCase.__init__(self)
        self._logger = base.MemoryLogger.MemoryLogger(1)
        base.FileHelper.setLogger(self._logger)
        self._baseNode = 'unittest.fh'
        self._baseDir = self.tempDir('filetool', self._baseNode)
        self._fn = self.tempFile('first.txt', self._baseNode, 'filetool')
        base.StringUtils.toFile(self._fn, "line 1\nline 2\nThis file is in line 3")

    def _finish(self):
        shutil.rmtree(self.tempDir(self._baseNode))

    def debugFlag(self):
        base.StringUtils.avoidWarning(self)
        return DEBUG

    def checkPart(self, container, full, path, node, fn, ext):
        self.assertIsEqual(path, container['path'])
        self.assertIsEqual(full, container['full'])
        self.assertIsEqual(node, container['node'])
        self.assertIsEqual(fn, container['fn'])
        self.assertIsEqual(ext, container['ext'])
        self.assertIsEqual(full, base.FileHelper.joinFilename(container))

    def testSplitFilenameJoinFilename(self):
        if DEBUG: return
        container = base.FileHelper.splitFilename('/tmp/jonny.txt')
        self.checkPart(container, '/tmp/jonny.txt', '/tmp/', 'jonny.txt', 'jonny', '.txt')
        container = base.FileHelper.splitFilename('/home/authors/jonny.txt')
        self.checkPart(container, '/home/authors/jonny.txt', '/home/authors/', 'jonny.txt', 'jonny', '.txt')
        container = base.FileHelper.splitFilename('jonny.v2.txt')
        self.checkPart(container, 'jonny.v2.txt', '', 'jonny.v2.txt', 'jonny.v2', '.txt')
        container = base.FileHelper.splitFilename('.config')
        self.checkPart(container, '.config', '', '.config', '.config', '')

    def testTail(self):
        if DEBUG: return
        tail = base.FileHelper.tail(self._fn)
        self.assertIsEqual(1, len(tail))
        self.assertIsEqual('This file is in line 3', tail[0])

    def testTailNumbers(self):
        if DEBUG: return
        tail = base.FileHelper.tail(self._fn, 2, True)
        self.assertIsEqual(2, len(tail))
        asString = ''.join(tail)
        self.assertIsEqual('2: line 2\n3: This file is in line 3', asString)

    def testDirectoryInfo(self):
        if DEBUG: return
        info = base.FileHelper.directoryInfo('/etc', r'.*\.conf')
        self.assertTrue(info._fileCount > 0)
        self.assertTrue(info._fileSizes > 0)
        self.assertTrue(info._dirCount > 0)
        self.assertTrue(info._ignoredDirs > 0)
        # self.assertTrue(info._ignoredFiles > 0)
        self.assertIsEqual(5, len(info._youngest))
        self.assertIsEqual(5, len(info._largest))

    def testPathToNode(self):
        if DEBUG: return
        self.assertIsEqual('x__abc_def_x.txt', base.FileHelper.pathToNode('x:/abc/def/x.txt'))

    def testSetModified(self):
        if DEBUG: return
        fn = self.tempFile('test.txt', self._baseNode)
        base.StringUtils.toFile(fn, 'Hi')
        yesterday = int(time.time()) - 86400
        januar = datetime.datetime(2016, 1, 2, 10, 22, 55)
        januar2 = time.mktime(januar.timetuple())
        base.FileHelper.setModified(fn, yesterday)
        self.assertIsEqual(yesterday, int(os.path.getmtime(fn)))
        base.FileHelper.setModified(fn, None, januar)
        self.assertIsEqual(januar2, os.path.getmtime(fn))

    def testDistinctPaths(self):
        if DEBUG: return
        tempDir = self.tempDir('disticts', self._baseNode)
        self.clearDirectory(tempDir)
        dir1 = tempDir + os.sep + 'abc'
        dir2 = tempDir + os.sep + 'def'
        dirLink = tempDir + os.sep + 'link'
        dirChild = dir1 + os.sep + 'child'
        dirChildInLink = dirLink + os.sep + 'childInLink'
        dirLinkLink = dir1 + os.sep + 'linkLink'
        self.ensureDirectory(dir1)
        self.ensureDirectory(dir2)
        self.ensureDirectory(dirChild)
        os.symlink(dir2, dirLink)
        os.symlink(dirChildInLink, dirLinkLink)
        # base/abc
        # base/abc/child
        # base/abc/linkInLink -> def
        # base/def
        # base/link -> def
        # base/def/childInLink
        # base/def/linkLink -> def/childInLink
        self.assertTrue(base.FileHelper.distinctPaths(dir1, dir2))
        self.assertTrue(base.FileHelper.distinctPaths(dir2, dir1))
        self.assertTrue(base.FileHelper.distinctPaths(dirChild, dir2))
        self.assertTrue(base.FileHelper.distinctPaths(dir2, dirChild))
        self.assertTrue(base.FileHelper.distinctPaths(dir1, dirLink))
        self.assertTrue(base.FileHelper.distinctPaths(dirLink, dir1))

        self.assertFalse(base.FileHelper.distinctPaths(dirChild, dir1))
        self.assertFalse(base.FileHelper.distinctPaths(dir1, dirChild))
        self.assertFalse(base.FileHelper.distinctPaths(dir2, dirLink))
        self.assertFalse(base.FileHelper.distinctPaths(dirLink, dir2))
        self.assertFalse(base.FileHelper.distinctPaths(dir2, dirChildInLink))
        self.assertFalse(base.FileHelper.distinctPaths(dirChildInLink, dir2))
        self.assertFalse(base.FileHelper.distinctPaths(dir2, dirLinkLink))
        self.assertFalse(base.FileHelper.distinctPaths(dirLinkLink, dir2))
        self.assertFalse(base.FileHelper.distinctPaths(dirChildInLink, dirLinkLink))
        self.assertFalse(base.FileHelper.distinctPaths(dirLinkLink, dirChildInLink))
        self.assertFalse(base.FileHelper.distinctPaths(dirLinkLink, dir2))
        self.assertFalse(base.FileHelper.distinctPaths(dir2, dirLinkLink))

    def testFromBytes(self):
        if DEBUG: return
        self.assertIsEqual('ascii', base.FileHelper.fromBytes(b'ascii'))
        self.assertIsEqual('äöüÖÄÜß', base.FileHelper.fromBytes('äöüÖÄÜß'.encode('utf_8')))
        line = 'äöüÖÄÜß'.encode('latin-1')
        self.assertIsEqual('äöüÖÄÜß', base.FileHelper.fromBytes(line))
        line = 'äöüÖÄÜß'.encode('cp850')
        self.assertFalse('äöüÖÄÜß' == base.FileHelper.fromBytes(line))
        line = b''
        hexString = ''
        for ix in range(1, 255):
            hexString += "{:02x}".format(ix)
        line = bytes.fromhex(hexString)
        self.assertFalse('äöüÖÄÜß' == base.FileHelper.fromBytes(line))

    def testEnsureDir(self):
        if DEBUG: return
        temp = self.tempDir('dir1', self._baseNode)
        # already exists
        base.FileHelper.ensureDirectory(temp)
        self.assertTrue(os.path.isdir(temp))
        # does not exist with logger
        self.ensureFileDoesNotExist(temp)
        base.FileHelper.ensureDirectory(temp)
        self.assertTrue(os.path.isdir(temp))
        # does not exist without logger
        self.ensureFileDoesNotExist(temp)
        base.FileHelper.ensureDirectory(temp)
        self.assertTrue(os.path.isdir(temp))
        # file exists, with logger
        self.ensureFileDoesNotExist(temp)
        base.StringUtils.toFile(temp, 'anything')
        base.FileHelper.ensureDirectory(temp)
        self.assertTrue(os.path.isdir(temp))
        # file exists, with logger
        self.ensureFileDoesNotExist(temp)
        base.StringUtils.toFile(temp, 'anything')
        base.FileHelper.ensureDirectory(temp)
        self.assertTrue(os.path.isdir(temp))
        # invalid link, with logger
        self.ensureFileDoesNotExist(temp)
        os.symlink('../does-not-exist', temp)
        base.FileHelper.ensureDirectory(temp)
        self.assertTrue(os.path.isdir(temp))
        # invalid link, without logger
        self.ensureFileDoesNotExist(temp)
        os.symlink('../does-not-exist2', temp)
        base.FileHelper.ensureDirectory(temp)
        self.assertTrue(os.path.isdir(temp))

    def testEnsureFileDoesNotExist(self):
        if DEBUG: return
        temp = self.tempDir('file', self._baseNode)
        # directory exists
        base.FileHelper.ensureFileDoesNotExist(temp)
        self.assertFalse(os.path.exists(temp))
        # does not exists:
        base.FileHelper.ensureFileDoesNotExist(temp)
        self.assertFalse(os.path.exists(temp))
        base.FileHelper.ensureFileDoesNotExist(temp)
        self.assertFalse(os.path.exists(temp))
        # file exists
        base.StringUtils.toFile(temp, 'x')
        base.FileHelper.ensureFileDoesNotExist(temp)
        self.assertFalse(os.path.exists(temp))
        base.StringUtils.toFile(temp, 'x')
        base.FileHelper.ensureFileDoesNotExist(temp)
        self.assertFalse(os.path.exists(temp))
        # invalid link exists
        os.symlink('../invalid-link-source', temp)
        base.FileHelper.ensureFileDoesNotExist(temp)
        self.assertFalse(os.path.exists(temp))
        os.symlink('../invalid-link-source', temp)
        base.FileHelper.ensureFileDoesNotExist(temp)
        self.assertFalse(os.path.exists(temp))

    def testEnsureSymbolicLink(self):
        if DEBUG: return
        tempDir = self.tempDir('jail', self._baseNode)
        target = tempDir + os.sep + 'parent'
        # creating base dir and target:
        self.ensureFileDoesNotExist(tempDir)
        self.tempDir('sibling', self._baseNode)
        base.FileHelper.ensureSymbolicLink('../../sibling', target)
        self.assertTrue(os.path.islink(target))
        self.assertIsEqual('../../sibling', os.readlink(target))
        # changing link source:
        self.tempDir('sibling2', self._baseNode)
        base.FileHelper.ensureSymbolicLink('../../sibling2', target, True)
        self.assertTrue(os.path.islink(target))
        self.assertIsEqual('../../sibling2', os.readlink(target))
        # removing existing target:
        self.ensureFileDoesNotExist(target)
        base.StringUtils.toFile(target, 'anything')
        base.FileHelper.ensureSymbolicLink('../../sibling2', target, True)
        self.assertTrue(os.path.islink(target))
        self.assertIsEqual('../../sibling2', os.readlink(target))

    def testEnsureSymbolicLinkErrors(self):
        if DEBUG: return
        tempDir = self.tempDir('jail', self._baseNode)
        target = tempDir + os.sep + 'parent'
        self.ensureDirectory(target)
        # creating base dir and target:
        self.ensureFileDoesNotExist(tempDir)
        self.tempDir('sibling', self._baseNode)
        self._logger.log('= expecting error is directory')
        base.FileHelper.ensureSymbolicLink('../../sibling', target, True)
        self.assertFalse(os.path.exists(target))
        # must not create parent:
        self._logger.log('= expecting error missing parent')
        self.ensureFileDoesNotExist(os.path.dirname(target))
        base.FileHelper.ensureSymbolicLink('../../sibling', target, False)
        self.assertFalse(os.path.exists(target))

    def testFileClass(self):
        if DEBUG: return
        baseDir = '/usr/share/pyrshell/unittest/data/'
        aClass, subClass = base.FileHelper.fileClass(baseDir + 'example.zip')
        self.assertIsEqual('container', aClass)
        self.assertIsEqual('zip', subClass)
        aClass, subClass = base.FileHelper.fileClass(baseDir + 'example.tar')
        self.assertIsEqual('container', aClass)
        self.assertIsEqual('tar', subClass)
        aClass, subClass = base.FileHelper.fileClass(baseDir + 'example.tgz')
        self.assertIsEqual('container', aClass)
        self.assertIsEqual('tar', subClass)
        aClass, subClass = base.FileHelper.fileClass(baseDir + 'example.tbz')
        self.assertIsEqual('container', aClass)
        self.assertIsEqual('tar', subClass)
        aClass, subClass = base.FileHelper.fileClass(baseDir + 'example.html')
        self.assertIsEqual('text', aClass)
        self.assertIsEqual('xml', subClass)
        aClass, subClass = base.FileHelper.fileClass(baseDir + 'example.sh')
        self.assertIsEqual('text', aClass)
        self.assertIsEqual('shell', subClass)
        aClass, subClass = base.FileHelper.fileClass(baseDir + 'example.txt')
        self.assertIsEqual('text', aClass)
        self.assertIsEqual('text', subClass)

    def testEnsureFileExists(self):
        if DEBUG: return
        fn = self.tempFile('should.exist.txt', self._baseNode)
        base.FileHelper.ensureFileDoesNotExist(fn)
        base.FileHelper.ensureFileExists(fn, 'Hi world')
        self.assertFileContains('Hi world', fn)

    def testEnsureFileExistsError(self):
        if DEBUG: return
        fn = self.tempDir('blocking.dir', self._baseNode)
        self._logger.log('expectig error: blocking dir')
        base.FileHelper.ensureFileExists(fn, 'Hi')
        self.assertDirExists(fn)

    def testCopyDirectoryClear(self):
        if DEBUG: return
        source = self.tempDir('src', self._baseNode)
        target = self.tempDir('trg', self._baseNode)
        base.StringUtils.toFile(source + '/hi.txt', 'Hi')
        os.symlink('hi.txt', source + os.sep + 'hi.link.txt')
        source2 = self.tempDir('src/dir1', self._baseNode)
        base.StringUtils.toFile(source2 + '/wow.txt', 'Wow')
        if not os.path.exists(source2 + '/wow.symlink.txt'):
            os.symlink('wow.txt', source2 + '/wow.symlink.txt')
        base.FileHelper.copyDirectory(source, target, 'clear', 3)
        self.assertFileContains('Hi', target + '/hi.txt')
        self.assertDirExists(target + '/dir1')
        self.assertFileContains('Wow', target + '/dir1/wow.txt')
        trg2 = target + '/dir1/wow.symlink.txt'
        self.assertFileContains('Wow', trg2)
        self.assertTrue(os.path.islink(trg2))
        fn = target + os.sep + 'hi.link.txt'
        self.assertFileExists(fn)
        self.assertIsEqual('hi.txt', os.readlink(fn))

    def testCopyDirectoryUpdate(self):
        if DEBUG: return
        source = self.tempDir('src', self._baseNode)
        target = self.tempDir('trg', self._baseNode)
        base.StringUtils.toFile(source + '/hi.txt', 'Hi')
        source2 = self.tempDir('src/dir1', self._baseNode)
        base.StringUtils.toFile(source2 + '/wow.txt', 'Wow')
        base.FileHelper.copyDirectory(source, target, 'clear', 3)
        time.sleep(1)
        base.StringUtils.toFile(source + '/hi.txt', 'hi!')
        base.FileHelper.setModified(source + '/hi.txt', 365*24*3600)
        base.StringUtils.toFile(source + '/hi2.txt', 'hi!')
        base.StringUtils.toFile(source2 + '/wow2.txt', 'wow!')
        base.FileHelper.setModified(source2 + '/wow2.txt', 365*24*3600)
        base.FileHelper.copyDirectory(source, target, 'update')
        self.assertFileContains('Hi', target + '/hi.txt')
        self.assertFileContains('hi!', target + '/hi2.txt')
        self.assertDirExists(target + '/dir1')
        self.assertFileContains('Wow', target + '/dir1/wow.txt')
        self.assertFileContains('wow!', target + '/dir1/wow2.txt')

    def testUnpackTgz(self):
        if DEBUG: return
        target = self.tempDir(self._baseNode)
        fn = target + os.sep + 'dummy'
        base.StringUtils.toFile(fn, '')
        base.FileHelper.unpack('/usr/share/pyrshell/unittest/data/etc.work.tgz', target, True)
        self.assertFileNotExists(fn)
        self.assertFileExists(target + '/etc/passwd')
        self.assertFileExists(target + '/etc/nginx/sites-available/default')

    def testUnpackZip(self):
        if DEBUG: return
        target = self.tempDir('archive', self._baseNode)
        base.FileHelper.unpack('/usr/share/pyrshell/unittest/data/example.zip', target, True)
        self.assertFileExists(target + '/All.sh')

    def testTempFile(self):
        if DEBUG: return
        fn = base.FileHelper.tempFile('test.txt', 'unittest.2')
        parent = os.path.dirname(fn)
        self.assertIsEqual('test.txt', os.path.basename(fn))
        self.assertIsEqual('unittest.2', os.path.basename(parent))
        self.assertFileExists(parent)
        self.ensureFileDoesNotExist(parent)

    def testCreateTree(self):
        if DEBUG: return
        base.FileHelper.ensureDirectory(self._baseDir)
        base.FileHelper.createFileTree('''tree1/
tree1/file1|blaBla|660|2020-04-05 11:22:33
tree2/|744|2020-04-06 12:23:34
tree2/file2
tree2/file3|1234|700
tree1/file4
link|->tree1
''', self._baseDir)
        dirName = self._baseDir + os.sep + 'tree1'
        self.assertDirExists(dirName)
        fn = dirName + os.sep + 'file1'
        self.assertFileExists(fn)
        statInfo = os.stat(fn)
        self.assertNotNone(statInfo)
        self.assertIsEqual('blaBla', base.StringUtils.fromFile(fn))
        self.assertIsEqual(0o660, statInfo.st_mode % 0o1000)
        current = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(statInfo.st_mtime))
        self.assertIsEqual('2020-04-05 11:22:33', current)
        self.assertFileExists(dirName + os.sep + 'file4')
        dirName = self._baseDir + os.sep + 'tree2'
        self.assertDirExists(dirName)
        statInfo = os.lstat(dirName)
        self.assertIsEqual(0o744, statInfo.st_mode % 0o1000)
        current = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(statInfo.st_mtime))
        self._logger.log('== time test for dirs deactivated')
        #self.assertIsEqual('2020-04-06 12:23:34', current)
        self.assertFileExists(dirName + os.sep + 'file2')
        fn = dirName + os.sep + 'file3'
        self.assertFileExists(dirName + os.sep + 'file3')
        statInfo = os.stat(fn)
        self.assertNotNone(statInfo)
        self.assertIsEqual(0o700, statInfo.st_mode % 0o1000)
        self.assertIsEqual('1234', base.StringUtils.fromFile(fn))
        fn = self._baseDir + os.sep + 'link'
        self.assertFileExists(fn)
        self.assertTrue(os.path.islink(fn))
        self.assertIsEqual('tree1', os.readlink(fn))

    def testCopyByRules(self):
        if DEBUG: return
        base.FileHelper.ensureDirectory(self._baseDir)
        base.FileHelper.createFileTree('''skeleton/
skeleton/.list|app
skeleton/app/
skeleton/app/test/
skeleton/app/.gitignore|test/
skeleton/app/common/
skeleton/app/common/sql/
skeleton/app/common/sql/common.sql|select * from x;
skeleton/app/users/
skeleton/app/roles/
skeleton/public/
skeleton/public/index.php|<?php
skeleton/public/js/
skeleton/public/js/file1.js|.name { width:3 }
skeleton/public/js/file2.js|.name { width:4 }
skeleton/public/js/global.js|->file1.js
''', self._baseDir)
        rules = '''
# symlinks+except
app/*:*:symlink,dirsonly,except test
# single dir in base dir
.list:*
# single dir
public:*
# single file with replacement
public/index.php:*:replace /php/php>/
# dirtree
public/js:*:recursive
:tmp/down
'''.split('\n')
        baseSource = self._baseDir + os.sep + 'skeleton'
        baseTarget = self._baseDir + os.sep + 'project'
        self.ensureFileDoesNotExist(baseTarget)
        base.FileHelper.copyByRules(rules, baseSource, baseTarget)
        self.assertFileContent('app', baseTarget + '/.list')
        self.assertDirExists(baseTarget + '/app')
        self.assertFileNotExists(baseTarget + '/app/test')
        self.assertFileNotExists(baseTarget + '/app/.gitignore')
        self.assertFileExists(baseTarget + '/app/common/sql/common.sql')
        self.assertFileContent('select * from x;', baseTarget + '/app/common/sql/common.sql')
        self.assertFileExists(baseTarget + '/app/users')
        self.assertFileExists(baseTarget + '/app/roles')
        self.assertFileContent('<?php>', baseTarget + '/public/index.php')
        self.assertDirExists(baseTarget + '/public/js')
        self.assertFileContent('.name { width:3 }', baseTarget + '/public/js/file1.js')
        self.assertFileContent('.name { width:4 }', baseTarget + '/public/js/file2.js')
        self.assertFileContent('.name { width:3 }', baseTarget + '/public/js/global.js')
        self.assertDirExists(baseTarget + '/tmp/down')

    def testEndOfLinkChain(self):
        if DEBUG: return
        end = self._baseDir + os.sep + 'end.txt'
        base.StringUtils.toFile(end, 'endOfLink')
        link1 = self._baseDir + os.sep + 'link1'
        base.FileHelper.ensureFileDoesNotExist(link1)
        os.symlink('link2', link1)
        link2 = self._baseDir + os.sep + 'link2'
        base.FileHelper.ensureFileDoesNotExist(link2)
        os.symlink('end.txt', link2)
        self.assertIsEqual(end, base.FileHelper.endOfLinkChain(link1))
        base.FileHelper.ensureFileDoesNotExist(end)
        self.assertNone(base.FileHelper.endOfLinkChain(link1))

    def testDeepRename(self):
        if DEBUG: return
        first = self._baseDir + os.sep + 'first.txt'
        base.StringUtils.toFile(first, 'first')
        second = self._baseDir + os.sep + 'second.txt'
        base.FileHelper.ensureFileDoesNotExist(second)
        self.assertTrue(base.FileHelper.deepRename(first, 'second.txt'))
        self.assertFileNotExists(first)
        self.assertFileContent('first', second)

        third = self._baseDir + os.sep + 'third.txt'
        base.StringUtils.toFile(third, 'third')
        self.assertTrue(base.FileHelper.deepRename(second, third, deleteExisting=True))
        self.assertFileNotExists(second)
        self.assertFileContent('first', third)

    def testDeepRenameLink(self):
        if DEBUG: return
        first = self._baseDir + os.sep + 'first.txt'
        base.StringUtils.toFile(first, 'first')
        second = self._baseDir + os.sep + 'second.txt'
        base.StringUtils.toFile(second, '2nd')
        base.FileHelper.ensureFileDoesNotExist(second)
        link1 = self._baseDir + os.sep + 'link1'
        base.FileHelper.ensureFileDoesNotExist(link1)
        os.symlink('link2', link1)
        link2 = self._baseDir + os.sep + 'link2'
        base.FileHelper.ensureFileDoesNotExist(link2)
        os.symlink('first.txt', link2)
        self.assertTrue(base.FileHelper.deepRename(link2, 'second.txt', deleteExisting=True))
        self.assertFileNotExists(first)
        self.assertFileContent('first', second)

    def testDeepRenameLink2(self):
        if DEBUG: return
        first = self.tempFile('first.txt', 'renamedir')
        base.StringUtils.toFile(first, 'first')
        second = self.tempFile('second.txt', 'renamedir')
        base.StringUtils.toFile(second, '2nd')
        base.FileHelper.ensureFileDoesNotExist(second)
        link1 = self._baseDir + os.sep + 'link1'
        base.FileHelper.ensureFileDoesNotExist(link1)
        os.symlink('link2', link1)
        link2 = self._baseDir + os.sep + 'link2'
        base.FileHelper.ensureFileDoesNotExist(link2)
        os.symlink(first, link2)
        self.assertTrue(base.FileHelper.deepRename(link2, 'second.txt', deleteExisting=True))
        self.assertFileNotExists(first)
        self.assertFileContent('first', second)

    def testDeepRenameError(self):
        if DEBUG: return
        self._logger.clear()
        self.assertFalse(base.FileHelper.deepRename('not#existising#file', 'realy#not#existising#file'))
        self.assertTrue(self._logger.contains('old name does not exist', errorsToo=True))

        self._logger.clear()
        first = self.tempFile('first.txt', 'renamedir')
        base.StringUtils.toFile(first, '')
        link1 = self._baseDir + os.sep + 'link1'
        base.FileHelper.ensureFileDoesNotExist(link1)
        os.symlink(first, link1)
        self.assertFalse(base.FileHelper.deepRename(link1, 'first.txt', deleteExisting=True))
        self.assertTrue(self._logger.contains('link target has the same name', errorsToo=True))

        self._logger.clear()
        second = self.tempFile('second.txt', 'renamedir')
        base.StringUtils.toFile(second, '')
        self.assertFalse(base.FileHelper.deepRename(first, 'second.txt', deleteExisting=False))
        self.assertTrue(self._logger.contains('new name exists', errorsToo=True))

        self._logger.clear()
        base.FileHelper.setUnitTestMode('deepRename-no-unlink')
        self.assertFalse(base.FileHelper.deepRename(first, 'second.txt', deleteExisting=True))
        self.assertTrue(self._logger.contains('cannot remove new name', errorsToo=True))
        base.FileHelper.setUnitTestMode(None)

    def testMoveFileRename(self):
        if DEBUG: return
        first = self.tempFile('first.txt', 'move')
        second = self.tempFile('second.txt', 'move', 'trg')
        base.StringUtils.toFile(first, '')
        base.FileHelper.moveFile(first, second)
        self.assertFileExists(second)
        self.assertFileNotExists(first)
        
    def testMoveFileCopy(self):
        if DEBUG: return
        srcDir = '/opt/tmp'
        if not os.path.exists(srcDir):
            self._logger.log(f'>>> missing {srcDir}: cannot do the unit test')
        else:
            first = srcDir + os.sep + 'first'
            second = self.tempFile('second.txt', 'move', 'trg')
            base.StringUtils.toFile(first, '')
            base.FileHelper.moveFile(first, second)
            self.assertFileExists(second)
            self.assertFileNotExists(first)

    def testReplaceExtension(self):
        #if DEBUG: return
        self.assertIsEqual('/abc/def.abc', base.FileHelper.replaceExtension('/abc/def.txt', '.abc'))
        self.assertIsEqual('/abc/.def.abc', base.FileHelper.replaceExtension('/abc/.def', '.abc'))

if __name__ == '__main__':
    sys.argv = ['', 'Test.testName']
    tester = FileHelperTest()
    tester.run()
