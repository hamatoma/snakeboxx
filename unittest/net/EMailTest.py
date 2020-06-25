'''
Created on 12.04.2018

@author: hm
'''
from unittest.UnitTestCase import UnitTestCase
import base.MemoryLogger
import base.StringUtils
import net.EMail

DEBUG = False

class EMailTest(UnitTestCase):

    def testBasics(self):
        if DEBUG: return
        logger = base.MemoryLogger.MemoryLogger()
        email = net.EMail.EMail('Testmail von Python', 'Hi!\nHat funktioniert', '''
<html>
<body>
<h1>Hi</h1>
<p>Hat funktioniert!</p
</body>
</html>
''')
        config = base.StringUtils.privateConfig()
        user = 'hm.neutral@gmx.de'
        code = config.getString('EMailTest.code.hm.neutral')
        email.setSmtpLogin('mail.gmx.net', 587, user, code, True, user)
        #code = config.getString('EMailTest.code.bigtoy.by')
        user = 'bigtoy-by@gmx.de'
        email.setSmtpLogin('smtp.gmx.de', 587, user, code, True, user)

        email.sendTo('wk64@gmx.de', None, None, logger)
        signature = email.lastSignature()
        self.assertEquals('smtp.gmx.de|587|bigtoy-by@gmx.de|{}|bigtoy-by@gmx.de|wk64@gmx.de'.format(code), signature)
        current = logger.getMessages()
        self.assertEquals(0, len(current))

    def testEmailWithCC(self):
        #if DEBUG: return
        logger = base.MemoryLogger.MemoryLogger()
        config = base.StringUtils.privateConfig()
        code = config.getString('EMailTest.code.bigtoy.by')
        user = 'bigtoy-by@gmx.de'
        email = net.EMail.EMail('Testmail+cc', 'Hi!\nHat funktioniert')
        email.setSmtpLogin('smtp.gmx.de', 587, user, code, True, user)
        email.sendTo('wk64@gmx.de', 'test1@hamatoma.de+test2@hamatoma.de', None, logger)
        signature = email.lastSignature()
        self.assertEquals('smtp.gmx.de|587|bigtoy-by@gmx.de|{}|bigtoy-by@gmx.de|wk64@gmx.de'.format(code), signature)
        current = logger.getMessages()
        self.assertEquals(0, len(current))

    def testEmailWithBCC(self):
        if DEBUG: return
        logger = base.MemoryLogger.MemoryLogger()
        config = base.StringUtils.privateConfig()
        code = config.getString('EMailTest.code.bigtoy.by')
        user = 'bigtoy-by@gmx.de'
        email = net.EMail.EMail('Testmail+bcc', 'Hi!\nHat funktioniert')
        email.setSmtpLogin('smtp.gmx.de', 587, user, code, True, user)
        email.sendTo('wk64@gmx.de', None, 'test1@hamatoma.de+test2@hamatoma.de', logger)
        signature = email.lastSignature()
        self.assertEquals('smtp.gmx.de|587|bigtoy-by@gmx.de|{}|bigtoy-by@gmx.de|wk64@gmx.de'.format(code), signature)
        current = logger.getMessages()
        self.assertEquals(0, len(current))

    def testSendSimpleEmail(self):
        if DEBUG: return
        logger = base.MemoryLogger.MemoryLogger(0, 0)
        config = base.StringUtils.privateConfig()
        code = config.getString('EMailTest.code.bigtoy.by')
        user = 'bigtoy-by@gmx.de'
        signature = net.EMail.sendSimpleEMail('wk64@gmx.de', 'test sendSimpleEMail', 'It works',
            user, 'smtp.gmx.de', 587, user, code, True, logger)
        # .................smtp.gmx.de|587|bigtoy-by@gmx.de|1G.e.h.t.H.e.i.m|bigtoy-by@gmx.de|wk64@gmx.de
        self.assertEquals('smtp.gmx.de|587|bigtoy-by@gmx.de|{}|bigtoy-by@gmx.de|wk64@gmx.de'.format(code), signature)
        current = logger.getMessages()
        self.assertEquals(0, len(current))

if __name__ == '__main__':
    #import sys;sys.argv = ['', 'Test.testName']
    tester = EMailTest()
    tester.run()
