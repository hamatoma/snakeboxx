'''
Created on 12.04.2018

@author: hm
'''
from unittest.UnitTestCase import UnitTestCase
import base.MemoryLogger
import base.UsageInfo

class UsageInfoTest(UnitTestCase):

    def testBasics(self):
        logger = base.MemoryLogger.MemoryLogger()
        info = base.UsageInfo.UsageInfo(logger)
        info.appendDescription('''example <mode>
 displays this example
''')
        info.addMode('help', '''help <pattern>
 display a help message
  <pattern>: only matching modes will be displayed
 ''', 'APP-NAME help')
        current = info.asString('help', 1)
        self.assertIsEqual('''example <mode>
  displays this example
<mode>:
    help <pattern>
      display a help message
        <pattern>: only matching modes will be displayed
Examples:
APP-NAME help''', current)

if __name__ == '__main__':
    #import sys;sys.argv = ['', 'Test.testName']
    tester = UsageInfoTest()
    tester.run()
