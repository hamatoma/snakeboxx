'''
Created on 12.04.2018

@author: hm
'''
import os
from unittest.UnitTestCase import UnitTestCase
import base.JavaConfig
import base.StringUtils
import base.MemoryLogger

class JavaConfigTest(UnitTestCase):

    def testBasic(self):
        logger = base.MemoryLogger.MemoryLogger()
        fn = self.tempFile('javaconf.conf')
        base.StringUtils.toFile(fn, '# comment\nabc.def=/dev\n\t\n\tFile = /tmp/x')
        config = base.JavaConfig.JavaConfig(fn, logger)
        self.assertEquals('/dev', config.getString('abc.def'))
        self.assertEquals('/tmp/x', config.getString('File'))
        self.assertNone(config.getString('file'))
        self.assertNone(config.getString('unknown'))
        os.unlink(fn)

    def testSyntaxError(self):
        fn = self.tempFile('error.conf')
        base.StringUtils.toFile(fn, '# comment\nabc.def:=/dev\n\t\n\tFile')
        logger = base.MemoryLogger.MemoryLogger()
        base.JavaConfig.JavaConfig(fn, logger)
        self.assertTrue(logger.contains('error.conf line 2: unexpected syntax [expected: <var>=<value>]: abc.def:=/dev', True))
        self.assertTrue(logger.contains('error.conf line 4: unexpected syntax [expected: <var>=<value>]: File', True))

    def testIntVar(self):
        fn = self.tempFile('javaconf.conf')
        base.StringUtils.toFile(fn, '# comment\nnumber=123\nWrong = zwo')
        logger = base.MemoryLogger.MemoryLogger()
        config = base.JavaConfig.JavaConfig(fn, logger)
        self.assertEquals(123, config.getInt('number'))
        self.assertEquals(456, config.getInt('unknown', 456))
        self.assertEquals(111, config.getInt('Wrong', 111))
        self.assertTrue(logger.contains('javaconf.conf: variable Wrong is not an integer: zwo', True))
        os.unlink(fn)

    def testGetKeys(self):
        fn = self.tempFile('javaconf.conf')
        base.StringUtils.toFile(fn, '# comment\nnumber=123\nWrong = zwo')
        logger = base.MemoryLogger.MemoryLogger()
        config = base.JavaConfig.JavaConfig(fn, logger)
        keys = config.getKeys()
        self.assertEquals(2, len(keys))
        self.assertEquals('Wrong', keys[0])
        self.assertEquals('number', keys[1])
        os.unlink(fn)

    def testGetKeysRegExpr(self):
        fn = self.tempFile('javaconf.conf')
        base.StringUtils.toFile(fn, '# comment\nnumber=123\nWrong = zwo')
        logger = base.MemoryLogger.MemoryLogger()
        config = base.JavaConfig.JavaConfig(fn, logger)
        keys = config.getKeys(r'number|int')
        self.assertEquals(1, len(keys))
        self.assertEquals('number', keys[0])
        os.unlink(fn)

if __name__ == '__main__':
    #import sys;sys.argv = ['', 'Test.testName']
    tester = JavaConfigTest()
    tester.run()
