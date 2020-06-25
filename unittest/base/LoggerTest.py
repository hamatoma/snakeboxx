'''
Created on 12.04.2018

@author: hm
'''
from unittest.UnitTestCase import UnitTestCase
from base.Logger import Logger
import os
import re
# import from base.Logger Logger

class LoggerTest(UnitTestCase):

    def testLogger(self):
        logFile = '/tmp/logger.log'
        if os.path.isfile(logFile):
            os.remove(logFile)
        logger = Logger(logFile, True)
        logger.log('Hi world')
        logger.error('an expected error')
        logger.debug('debug message')
        self.assertFileContains('Hi world', logFile)
        self.assertFileContains('+++ an expected error', logFile)
        self.assertFileContains('debug message', logFile)
        self.assertEquals('an expected error', logger._firstErrors[0])
        self.assertEquals(1, logger._errors)

    def testTextFilter(self):
        logFile = '/tmp/logger.log'
        if os.path.isfile(logFile):
            os.remove(logFile)
        logger = Logger(logFile, True)
        logger.setErrorFilter('[second]')
        logger.log('Hi world')
        logger.error('an expected error')
        logger.error('a [second] expected error')
        logger.debug('debug message')
        self.assertFileContains('Hi world', logFile)
        self.assertFileContains('+++ an expected error', logFile)
        self.assertFileNotContains('a [second] expected error', logFile)
        self.assertFileContains('debug message', logFile)
        self.assertEquals('an expected error', logger._firstErrors[0])
        self.assertEquals(1, logger._errors)

    def testRegExprFilter(self):
        logFile = '/tmp/logger.log'
        if os.path.isfile(logFile):
            os.remove(logFile)
        logger = Logger(logFile, True)
        logger.setErrorFilter(re.compile('second|third'))
        logger.log('Hi world')
        logger.error('an expected error')
        logger.error('a [second] expected error')
        logger.debug('debug message')
        self.assertFileContains('Hi world', logFile)
        self.assertFileContains('+++ an expected error', logFile)
        self.assertFileNotContains('a [second] expected error', logFile)
        self.assertFileContains('debug message', logFile)
        self.assertEquals('an expected error', logger._firstErrors[0])
        self.assertEquals(1, logger._errors)

    def testMirror(self):
        logFile1 = '/tmp/logger1.log'
        if os.path.isfile(logFile1):
            os.remove(logFile1)
        logger = Logger(logFile1, True)

        logFile2 = '/tmp/logger2.log'
        if os.path.isfile(logFile2):
            os.remove(logFile2)
        loggerMirror = Logger(logFile2, True)
        logger.setMirror(loggerMirror)

        logger.log('Hi world')
        logger.error('an expected error')
        logger.debug('debug message')
        self.assertFileContains('Hi world', logFile1)
        self.assertFileContains('+++ an expected error', logFile1)
        self.assertFileContains('debug message', logFile1)
        self.assertEquals('an expected error', logger._firstErrors[0])
        self.assertEquals(1, logger._errors)

        self.assertFileContains('Hi world', logFile2)
        self.assertFileContains('+++ an expected error', logFile2)
        self.assertFileContains('debug message', logFile2)
        self.assertEquals('an expected error', loggerMirror._firstErrors[0])
        self.assertEquals(1, loggerMirror._errors)

if __name__ == '__main__':
    #import sys;sys.argv = ['', 'Test.testName']
    tester = LoggerTest()
    tester.run()
