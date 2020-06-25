'''
Created on 12.04.2018

@author: hm
'''
import os
import time

from unittest.UnitTestCase import UnitTestCase
import base.MemoryLogger
import base.JobController
import base.StringUtils

class TestJobController (base.JobController.JobController):
    def __init__(self, logger):
        base.JobController.JobController.__init__(self, '/tmp/unittest/jobcontrol', 1, logger)
        self._done = {}

    def process(self, name, args):
        self._done[name] = ':' + '|'.join(args)
        return True

    def result(self, name):
        rc = self._done[name] if name in self._done else ''
        return rc

class JobControllerTest(UnitTestCase):
    def __init__(self):
        UnitTestCase.__init__(self)
        self._logger = base.MemoryLogger.MemoryLogger(3)
        self._controller = TestJobController(self._logger)
        self._dummyFile = self._controller.jobDirectory() + os.sep + 'dummy.file'

    def testBasics(self):
        base.JobController.JobController.writeJob('test2args', ['a1', 'a2'], self._controller.jobDirectory(), self._logger)
        base.JobController.JobController.writeJob('testNoArgs', [], self._controller.jobDirectory(), self._logger)
        self.assertTrue(self._controller.check())
        self.assertTrue(self._controller.check())
        self.assertEquals(':a1|a2', self._controller.result('test2args'))
        self.assertEquals(':', self._controller.result('testNoArgs'))

    def testClean(self):
        base.StringUtils.toFile(self._dummyFile, 'Hi')
        time.sleep(1)
        self.assertFalse(self._controller.check())
        self.assertFileNotExists(self._dummyFile)

if __name__ == '__main__':
    #import sys;sys.argv = ['', 'Test.testName']
    tester = JobControllerTest()
    tester.run()
