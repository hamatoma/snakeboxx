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

import base.DirTraverser
import base.StringUtils
import base.FileHelper
import base.MemoryLogger

debug = False

class DirTraverserTest(UnitTestCase):
    def __init__(self):
        UnitTestCase.__init__(self)
        self._base = self.tempDir('unittest.dtrav')
        self._logger = base.MemoryLogger.MemoryLogger(3)
        self._finish()
        base.FileHelper.ensureDirectory(self._base)
        base.FileHelper.createFileTree('''data1.txt|123
data2.conf
tree1/
tree1/file1.conf|blaBla|660|2020-04-05 11:22:33
tree2/
tree2/file2.txt|Jonny
tree2/file3.txt|charly7890|700
tree1/file4.conf|Judith
tree.txt/
tree.txt/x.conf/
tree.txt/x.conf/depth2.txt
tree2/link.txt|->file3.txt
link.x.conf|->tree2/x.conf
''', self._base)

    def _finish(self):
        shutil.rmtree(self.tempDir('unittest.dtrav'))

    def testAsListAll(self):
        if debug: return
        traverser = base.DirTraverser.DirTraverser(self._base)
        files = ' ' + ' '.join(traverser.asList()).replace(os.sep, '/') + ' '
        self.assertEquals(files.count(' '), 13+1)
        self.assertTrue(files.find('data1.txt') >= 0)
        self.assertTrue(files.find('data2.conf') >= 0)
        self.assertTrue(files.find(' tree1 ') >= 0)
        self.assertTrue(files.find('tree1/file1.conf') >= 0)
        self.assertTrue(files.find(' tree2 ') >= 0)
        self.assertTrue(files.find('tree2/file2.txt') >= 0)
        self.assertTrue(files.find('tree2/file3.txt') >= 0)
        self.assertTrue(files.find('tree1/file4.conf') >= 0)
        self.assertTrue(files.find(' tree.txt ') >= 0)
        self.assertTrue(files.find(' tree.txt/x.conf ') >= 0)
        self.assertTrue(files.find('tree.txt/x.conf/depth2.txt') >= 0)
        self.assertTrue(files.find('tree2/link.txt') >= 0)
        self.assertTrue(files.find('link.x.conf ') >= 0)

    def testAsListFilePattern(self):
        if debug: return
        traverser = base.DirTraverser.DirTraverser(self._base, filePattern="*.txt", dirPattern="*.txt")
        files = ' ' + ' '.join(traverser.asList()).replace(os.sep, '/') + ' '
        self.assertEquals(files.count(' '), 6+1)
        self.assertTrue(files.find('data1.txt') >= 0)
        self.assertFalse(files.find('data2.conf') >= 0)
        self.assertFalse(files.find(' tree1 ') >= 0)
        self.assertFalse(files.find('tree1/file1.conf') >= 0)
        self.assertFalse(files.find(' tree2 ') >= 0)
        self.assertTrue(files.find('tree2/file2.txt') >= 0)
        self.assertTrue(files.find('tree2/file3.txt') >= 0)
        self.assertFalse(files.find('tree1/file4.conf') >= 0)
        self.assertTrue(files.find(' tree.txt ') >= 0)
        self.assertFalse(files.find('tree.txt/x.conf ') >= 0)
        self.assertTrue(files.find('tree2/link.txt') >= 0)
        self.assertTrue(files.find('tree.txt/x.conf/depth2.txt') >= 0)

    def testAsListExclude(self):
        if debug: return
        traverser = base.DirTraverser.DirTraverser(self._base, reDirExcludes='.txt|2', reFileExcludes='.txt|2')
        files = ' ' +  ' '.join(traverser.asList()).replace(os.sep, '/') + ' '
        self.assertEquals(files.count(' '), 4+1)
        self.assertTrue(files.find(' tree1 ') >= 0)
        self.assertTrue(files.find('tree1/file1.conf') >= 0)
        self.assertTrue(files.find('tree1/file4.conf') >= 0)
        self.assertTrue(files.find('link.x.conf ') >= 0)

    def testAsListFileFileTypeDir(self):
        if debug: return
        traverser = base.DirTraverser.DirTraverser(self._base, fileType='d')
        files = ' ' + ' '.join(traverser.asList()).replace(os.sep, '/') + ' '
        self.assertEquals(files.count(' '), 4+1)
        self.assertTrue(files.find(' tree1 ') >= 0)
        self.assertTrue(files.find(' tree2 ') >= 0)
        self.assertTrue(files.find(' tree.txt ') >= 0)
        self.assertTrue(files.find('tree.txt/x.conf ') >= 0)

    def testAsListFileTypeFile(self):
        if debug: return
        traverser = base.DirTraverser.DirTraverser(self._base, fileType='f')
        files = ' ' + ' '.join(traverser.asList()).replace(os.sep, '/') + ' '
        self.assertEquals(files.count(' '), 7+1)
        self.assertTrue(files.find('data1.txt') >= 0)
        self.assertTrue(files.find('data2.conf') >= 0)
        self.assertTrue(files.find('tree1/file1.conf') >= 0)
        self.assertTrue(files.find('tree2/file2.txt') >= 0)
        self.assertTrue(files.find('tree2/file3.txt') >= 0)
        self.assertTrue(files.find('tree1/file4.conf') >= 0)
        self.assertTrue(files.find('tree.txt/x.conf/depth2.txt') >= 0)

    def testAsListFileTypeLink(self):
        if debug: return
        traverser = base.DirTraverser.DirTraverser(self._base, fileType='l')
        files = ' ' + ' '.join(traverser.asList()).replace(os.sep, '/') + ' '
        self.assertEquals(files.count(' '), 2+1)
        self.assertTrue(files.find('tree2/link.txt') >= 0)
        self.assertTrue(files.find('link.x.conf ') >= 0)

    def testAsListDepth(self):
        if debug: return
        traverser = base.DirTraverser.DirTraverser(self._base, minDepth=1, maxDepth=1)
        files = ' ' + ' '.join(traverser.asList()).replace(os.sep, '/') + ' '
        self.assertEquals(files.count(' '), 6+1)
        self.assertTrue(files.find('tree1/file1.conf') >= 0)
        self.assertTrue(files.find('tree2/file2.txt') >= 0)
        self.assertTrue(files.find('tree2/file3.txt') >= 0)
        self.assertTrue(files.find('tree1/file4.conf') >= 0)
        self.assertTrue(files.find('tree2/link.txt') >= 0)
        self.assertTrue(files.find(' tree.txt/x.conf ') >= 0)

    def testAsListMaxYields(self):
        if debug: return
        traverser = base.DirTraverser.DirTraverser(self._base, maxYields=4)
        files = ' ' +  ' '.join(traverser.asList()).replace(os.sep, '/') + ' '
        self.assertEquals(files.count(' '), 4+1)
        self.assertTrue(files.find('data1.txt') >= 0)
        self.assertTrue(files.find('data2.conf') >= 0)
        self.assertTrue(files.find(' tree1 ') >= 0)
        self.assertTrue(files.find(' tree2 ') >= 0)

    def testAsListYoungerThan(self):
        #if debug: return
        date = datetime.datetime.strptime('2020-04-05 11:22:34', '%Y-%m-%d %H:%M:%S')
        traverser = base.DirTraverser.DirTraverser(self._base, youngerThan=date)
        files = ' ' +  ' '.join(traverser.asList()).replace(os.sep, '/') + ' '
        self.assertEquals(files.count(' '), 12+1)
        self.assertTrue(files.find('data1.txt') >= 0)
        self.assertTrue(files.find('data2.conf') >= 0)
        self.assertTrue(files.find(' tree1 ') >= 0)
        self.assertFalse(files.find('tree1/file1.conf') >= 0)
        self.assertTrue(files.find(' tree2 ') >= 0)
        self.assertTrue(files.find('tree2/file2.txt') >= 0)
        self.assertTrue(files.find('tree2/file3.txt') >= 0)
        self.assertTrue(files.find('tree1/file4.conf') >= 0)
        self.assertTrue(files.find(' tree.txt ') >= 0)
        self.assertTrue(files.find(' tree.txt/x.conf ') >= 0)
        self.assertTrue(files.find('tree.txt/x.conf/depth2.txt') >= 0)
        self.assertTrue(files.find('tree2/link.txt') >= 0)
        self.assertTrue(files.find('link.x.conf ') >= 0)

    def testAsListOlderThan(self):
        if debug: return
        date = datetime.datetime.strptime('2020-04-05 11:22:34', '%Y-%m-%d %H:%M:%S')
        traverser = base.DirTraverser.DirTraverser(self._base)
        files = ' ' +  ' '.join(traverser.asList()).replace(os.sep, '/') + ' '
        self.assertTrue(files.find('tree1/file1.conf') >= 0)

    def testAsListMinSize(self):
        if debug: return
        traverser = base.DirTraverser.DirTraverser(self._base, minSize=6, fileType='f')
        files = ' ' +  ' '.join(traverser.asList()).replace(os.sep, '/')
        self.assertEquals(files.count(' '), 2+1)
        self.assertTrue(files.find('tree2/file3.txt') >= 0)
        self.assertTrue(files.find('tree1/file4.conf') >= 0)

    def testAsListMaxSize(self):
        if debug: return
        traverser = base.DirTraverser.DirTraverser(self._base, maxSize=5, fileType='f')
        files = ' ' +  ' '.join(traverser.asList()).replace(os.sep, '/') + ' '
        self.assertEquals(files.count(' '), 4+1)
        self.assertTrue(files.find('data1.txt') >= 0)
        self.assertTrue(files.find('data2.conf') >= 0)
        self.assertTrue(files.find('tree2/file2.txt') >= 0)
        self.assertFalse(files.find('tree2/file3.txt') >= 0)
        self.assertFalse(files.find('tree1/file4.conf') >= 0)
        self.assertTrue(files.find('tree.txt/x.conf/depth2.txt') >= 0)


if __name__ == '__main__':
    # import sys;sys.argv = ['', 'Test.testName']
    tester = DirTraverserTest()
    tester.run()
