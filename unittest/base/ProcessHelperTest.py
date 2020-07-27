'''
Created on 12.04.2018

@author: hm
'''
from unittest.UnitTestCase import UnitTestCase

import os

import base.ProcessHelper
import base.StringUtils
import base.Logger

DEBUG = False


def usage(msg=None):
    base.StringUtils.avoidWarning(msg)
    return 'test usage'


class ProcessHelperTest(UnitTestCase):
    def __init__(self):
        UnitTestCase.__init__(self)
        self._dir = self.tempDir('processhelper', 'unittest')
        self._testFile = self._dir + os.sep + 'simple.file.txt'
        base.StringUtils.toFile(self._testFile, 'line 1\nline 2\nline 3\n')
        self._helper = base.ProcessHelper.ProcessHelper(
            base.Logger.Logger('/tmp/processhelpertest.log', 3))

    def debugFlag(self):
        base.StringUtils.avoidWarning(self)
        return DEBUG

    def testExecute(self):
        self._helper.execute(['tail', '-n2', self._testFile], True, True)
        if self.assertTrue(len(self._helper._output) == 2):
            self.assertIsEqual('line 2', self._helper._output[0])
            self.assertIsEqual('line 3', self._helper._output[1])

    def testExecuteError(self):
        self._helper._logger.log('expecting an error:')
        self._helper.execute(['tail', '-n2', '/etc/shadow'], True, True)
        self.assertIsEqual(0, len(self._helper._output))
        self.assertTrue(self._helper._error[0].startswith(
            "tail: '/etc/shadow'"))

    def testExecuteInput(self):
        self._helper.executeInput(
            ['grep', '-o', '[0-9][0-9]*'], True, 'line1\n\line222')
        self.assertIsEqual('1', self._helper._output[0])
        self.assertIsEqual('222', self._helper._output[1])

    def testExecuteInputError(self):
        self._helper._logger.log('expecting an error:')
        self._helper.executeInput(
            ['veryUnknownCommand!', '[0-9]+'], True, 'line1\n\nline222')
        self.assertIsEqual(0, len(self._helper._output))
        self.assertIsEqual(
            "[Errno 2] No such file or directory: 'veryUnknownCommand!': 'veryUnknownCommand!'", self._helper._error[0])

    def testExecuteScript(self):
        self._helper.executeScript(
            '#! /bin/bash\n/bin/echo $1', 'getArg1', True, ['Hi world', 'Bye world'])

    def testExecuteInChain(self):
        fn = self.tempFile('gzip.input', 'unittest')
        base.StringUtils.toFile(fn, 'Hi')
        self._helper.executeInChain(
            ['gzip', '-c', fn], None, ['zcat'], '!shell')


if __name__ == '__main__':
    # import sys;sys.argv = ['', 'Test.testName']
    tester = ProcessHelperTest()
    tester.run()
