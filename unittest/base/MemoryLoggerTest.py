'''
Created on 12.04.2018

@author: hm
'''
import re

from unittest.UnitTestCase import UnitTestCase
import base.MemoryLogger

class MemoryLoggerTest(UnitTestCase):

    def testBase(self):
        logger = base.MemoryLogger.MemoryLogger()
        logger.log('Hi world')
        logger.error('an expected error')
        logger.debug('debug message')
        self.assertTrue(logger.contains('Hi world'))
        self.assertTrue(logger.contains('an expected error', errorsToo=True))
        self.assertTrue(logger.contains('debug message'))
        self.assertFalse(logger.contains('Hi world!'))
        self.assertTrue(logger.matches(r'Hi\sworld'))
        self.assertTrue(logger.matches(r'an [a-z]+ error', errorsToo=True))
        self.assertTrue(logger.matches(r'^de.*sage$'))

    def testClear(self):
        logger = base.MemoryLogger.MemoryLogger()
        logger.log('Hi world')
        logger.error('dummy error')
        self.assertTrue(logger.contains('Hi world'))
        self.assertTrue(len(logger._firstErrors) > 0)
        logger.clear()
        self.assertFalse(logger.contains('Hi world'))
        self.assertFalse(len(logger._firstErrors) > 0)

    def testContains(self):
        logger = base.MemoryLogger.MemoryLogger()
        logger.log('Jones jumps')
        self.assertTrue(logger.contains('jumps'))
        self.assertFalse(logger.contains('Jonny'))

    def testDerive(self):
        logger = base.MemoryLogger.MemoryLogger()
        logger.log('Hi world')
        logger.error('dummy error')
        logger2 = base.MemoryLogger.MemoryLogger()
        logger2.derive(logger, messagesToo=True)
        logger2.contains('Hi world')
        logger2.contains('dummy error', errorsToo=True)

    def testGetMessages(self):
        logger = base.MemoryLogger.MemoryLogger()
        logger.log('Hi world')
        self.assertEquals('Hi world', logger.getMessages()[0])

    def testMatches(self):
        logger = base.MemoryLogger.MemoryLogger()
        logger.log('Jones jumps')
        self.assertTrue(logger.matches('[dj]umps'))
        self.assertFalse(logger.matches('Jonny'))
        self.assertFalse(logger.matches('jones'))
        self.assertTrue(logger.matches('jones', flags=re.I))
        logger.error('dummy error')
        self.assertTrue(logger.matches('[dj]um', errorsToo=True))
        self.assertFalse(logger.matches('er+or', errorsToo=False))
        self.assertTrue(logger.matches('er+or', errorsToo=True))
        self.assertFalse(logger.matches('fail', errorsToo=True))


if __name__ == '__main__':
    #import sys;sys.argv = ['', 'Test.testName']
    tester = MemoryLoggerTest()
    tester.run()
