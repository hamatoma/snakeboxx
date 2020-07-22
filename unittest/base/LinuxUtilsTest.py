'''
Created on 12.04.2018

@author: hm
'''
from unittest.UnitTestCase import UnitTestCase
import base.LinuxUtils

class LinuxUtilsTest(UnitTestCase):

    def testDiskFree(self):
        infos = base.LinuxUtils.diskFree()
        self.assertTrue(len(infos) >= 1)
        for info in infos:
            if info[0] not in ['/', '/opt', '/work', '/home'] and not info[0].startswith('/media') and info[0].find('jail') < 0:
                self.assertIsEqual('valid path', info[0])
            self.assertTrue(type(info[1]) == int)
            self.assertTrue(type(info[2]) == int)
            self.assertTrue(type(info[3]) == int)
            self.assertTrue(info[1] >= info[2])
            self.assertTrue(info[1] >= info[3])

    def testUsers(self):
        infos = base.LinuxUtils.users()
        self.assertTrue(len(infos) >= 1)
        for info in infos:
            self.assertMatches(r'[\w]+', info[0])
            self.assertMatches(r'(:?\d+)(\.\d+)?|([\d.]+)', info[1])
            self.assertMatches(r'[0-2]?\d+:[0-5]\d', info[2])

    def testLoad(self):
        info = base.LinuxUtils.load()
        self.assertIsEqual(5, len(info))
        for ix in range(3):
            self.assertTrue(type(info[ix]) == float)
        self.assertTrue(type(info[3]) == int)
        self.assertTrue(type(info[4]) == int)
        self.assertTrue(int(info[3]) < int(info[4]))

    def testMemoryInfo(self):
        info = base.LinuxUtils.memoryInfo()
        self.assertIsEqual(5, len(info))
        # TOTAL_RAM, AVAILABLE_RAM, TOTAL_SWAP, FREE_SWAP, BUFFERS
        for ix in range(len(info)):
            self.assertTrue(type(info[ix]) == int)
        self.assertTrue(info[0] >= info[1])
        self.assertTrue(info[0] >= info[2])
        self.assertTrue(info[2] >= info[3])

    def checkMdadm(self, name, aType, members, blocks, status, info):
        self.assertIsEqual(name, info[0])
        self.assertIsEqual(aType, info[1])
        self.assertIsEqual(members, info[2])
        self.assertIsEqual(blocks, info[3])
        self.assertIsEqual(status, info[4])

    def testMdadmInfo(self):
        fn = self.tempFile('mdadm.info')
        with open(fn, "w") as fp:
            fp.write('''Personalities : [raid1]
md2 : active raid1 sdc1[0] sdd1[1]
      1953378368 blocks super 1.2 [2/2] [UU]
      bitmap: 0/15 pages [0KB], 65536KB chunk

md1 : active raid1 sda2[0] sdb2[1]
      508523520 blocks super 1.2 [2/2] [UU]
      bitmap: 2/4 pages [8KB], 65536KB chunk

md0 : active raid1 sda1[0] sdb1[1]
      242496 blocks super 1.2 [2/2] [UU]
''')
        infos = base.LinuxUtils.mdadmInfo(fn)
        self.assertIsEqual(3, len(infos))
        self.checkMdadm('md2', 'raid1', 'sdc1[0] sdd1[1]', 1953378368, 'OK', infos[0])
        self.checkMdadm('md1', 'raid1', 'sda2[0] sdb2[1]', 508523520, 'OK', infos[1])
        self.checkMdadm('md0', 'raid1', 'sda1[0] sdb1[1]', 242496, 'OK', infos[2])

    def testMdadmInfoBroken(self):
        fn = self.tempFile('mdadm.info')
        with open(fn, "w") as fp:
            fp.write('''Personalities : [raid1]
md1 : active raid1 hda14[0] sda11[2](F)
      2803200 blocks [2/1] [U_]''')
        infos = base.LinuxUtils.mdadmInfo(fn)
        self.assertIsEqual(1, len(infos))
        self.checkMdadm('md1', 'raid1', 'hda14[0] sda11[2](F)', 2803200, 'broken', infos[0])

    def testStress(self):
        info = base.LinuxUtils.stress(r'^(sda|nvme0n1)$', r'^(enp2s0|wlp4s0)$')
        self.assertIsEqual(7, len(info))

    def testUserId(self):
        self.assertIsEqual(base.LinuxUtils.userId('root'), 0)
        self.assertIsEqual(base.LinuxUtils.userId('www-data'), 33)
        self.assertIsEqual(base.LinuxUtils.userId(99), 99)
        self.assertIsEqual(base.LinuxUtils.userId('98'), 98)
        self.assertNone(base.LinuxUtils.userId('bluberablub'))
        self.assertIsEqual(base.LinuxUtils.userId('NobodyKnows', -1), -1)

    def testGroupId(self):
        self.assertIsEqual(base.LinuxUtils.groupId('root'), 0)
        self.assertIsEqual(base.LinuxUtils.groupId('www-data'), 33)
        self.assertIsEqual(base.LinuxUtils.groupId(99), 99)
        self.assertIsEqual(base.LinuxUtils.groupId('98'), 98)
        self.assertNone(base.LinuxUtils.groupId('bluberablub'))
        self.assertIsEqual(base.LinuxUtils.groupId('NobodyKnows', -1), -1)

if __name__ == '__main__':
    #import sys;sys.argv = ['', 'Test.testName']
    tester = LinuxUtilsTest()
    tester.run()
