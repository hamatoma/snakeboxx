'''
Created on 12.04.2018

@author: hm
'''
from unittest.UnitTestCase import UnitTestCase
import base.CryptoEngine
import base.MemoryLogger
import os.path
import base64

DEBUG = False

class CryptoEngineTest(UnitTestCase):

    def debugFlag(self):
        base.StringUtils.avoidWarning(self)
        return DEBUG

    def testBasic(self):
        logger = base.MemoryLogger.MemoryLogger()
        engine = base.CryptoEngine.CryptoEngine(logger)
        #self.log('random: ' + engine.nextString(60, 'ascii95'))

    def testEncode(self):
        logger = base.MemoryLogger.MemoryLogger()
        engine = base.CryptoEngine.CryptoEngine(logger)
        text = 'Hi_World'
        encoded = engine.encode(text, 'word')
        self.log('=' + encoded)
        decoded = engine.decode(encoded, 'word')
        self.assertIsEqual(text, decoded)
        self.assertIsEqual(0, len(logger.getMessages()))

    def testDecode(self):
        logger = base.MemoryLogger.MemoryLogger()
        engine = base.CryptoEngine.CryptoEngine(logger)
        for aSet in engine.getCharSetNames():
            text = engine.nextString(20, aSet)
            encoded = engine.encode(text, aSet)
            decoded = engine.decode(encoded, aSet)
            self.assertIsEqual(text, decoded)
            self.assertIsEqual(0, len(logger.getMessages()))
        for aSet in engine.getCharSetNames():
            text = engine.getCharSet(aSet)
            encoded = engine.encode(text, aSet)
            decoded = engine.decode(encoded, aSet)
            self.assertIsEqual(text, decoded)
            self.assertIsEqual(0, len(logger.getMessages()))

    def buildBinary(self, length):
        logger = base.MemoryLogger.MemoryLogger()
        engine = base.CryptoEngine.CryptoEngine(logger)
        engine.setSeedRandomly()
        rc = ''
        for ix in range(length):
            rc += chr(engine.nextInt(127, 1))
        return rc

    def testEncodeBinaryBase(self):
        if DEBUG:
            return
        logger = base.MemoryLogger.MemoryLogger()
        engine = base.CryptoEngine.CryptoEngine(logger)
        text = '12'
        encoded = engine.encodeBinary(text)
        decoded = engine.decodeBinary(encoded)
        self.assertIsEqual(text, decoded)
        text = '123'
        encoded = engine.encodeBinary(text)
        decoded = engine.decodeBinary(encoded)
        self.assertIsEqual(text, decoded)
        text = '1235'
        encoded = engine.encodeBinary(text)
        decoded = engine.decodeBinary(encoded)
        self.assertIsEqual(text, decoded)

    def testEncodeBinary(self):
        if DEBUG:
            return
        if self.assertTrue(False):
            logger = base.MemoryLogger.MemoryLogger()
            engine = base.CryptoEngine.CryptoEngine(logger)
            for length in range(20, 256):
                text = self.buildBinary(length)
                print(length)
                encoded = engine.encodeBinary(text)
                try:
                    decoded = engine.decodeBinary(encoded)
                except Exception as exc:
                    self.assertIsEqual('', str(exc))
                    break
                self.assertIsEqual(text, decoded)
                self.assertIsEqual(0, len(logger.getMessages()))

    def testTestCharSet(self):
        logger = base.MemoryLogger.MemoryLogger()
        engine = base.CryptoEngine.CryptoEngine(logger)
        for name in engine.getCharSetNames():
            aSet = engine.getCharSet(name)
            self.assertIsEqual(-1, engine.testCharSet(aSet, name))
            aSet += "\t"
            self.assertIsEqual(len(aSet) - 1, engine.testCharSet(aSet, name))

    def testOneTimePad(self):
        logger = base.MemoryLogger.MemoryLogger()
        engine = base.CryptoEngine.CryptoEngine(logger)
        fn = '/tmp/otp_request.txt'
        with open(fn, 'w') as fp:
            for user in range(1, 100):
                data = 'X{:04x}y'.format(user)
                pad = engine.oneTimePad(user, data)
                padData = engine.unpackOneTimePad(pad)
                self.assertIsEqual(user, padData[1])
                self.assertIsEqual(data, padData[2])
                fp.write('{:d}\t{:s}\t{:s}'.format(user, data, pad))

    def testExternOneTimePad(self):
        if "x"+"y" == "xy":
            return
        logger = base.MemoryLogger.MemoryLogger()
        engine = base.CryptoEngine.CryptoEngine(logger)
        fn = '/tmp/otp.txt'
        if self.assertTrue(os.path.exists(fn)):
            with open(fn, 'r') as fp:
                for line in fp:
                    [user, data, pad] = line.rstrip().split("\t")
                    padData = engine.unpackOneTimePad(pad, 3600)
                    self.assertIsEqual(int(user), padData[1])
                    self.assertIsEqual(data, padData[2])

    def testSetSeedFromString(self):
        if DEBUG:
            return
        logger = base.MemoryLogger.MemoryLogger()
        engine = base.CryptoEngine.CryptoEngine(logger)
        engine.setSeedFromString('')
        self.assertIsEqual(231702727, engine.nextInt())
        engine.setSeedFromString('x')
        self.assertIsEqual(1157398379, engine.nextInt())
        engine.setSeedFromString('blubber')
        self.assertIsEqual(604275342, engine.nextInt())

    def testSaveRestore(self):
        if DEBUG:
            return
        logger = base.MemoryLogger.MemoryLogger()
        engine = base.CryptoEngine.CryptoEngine(logger)
        engine.setSeedFromString('')
        seed1 = engine.saveSeed()
        value1 = engine.nextString(10, 'ascii94')
        engine.restoreSeed(seed1)
        value2 = engine.nextString(10, 'ascii94')
        self.assertIsEqual(value1, value2)

    def testBase64(self):
        if False and DEBUG:
            return
        buffer = b'x'
        '''
        for ix in range(256):
            buffer = buffer[0:-1]
            print("ix: " + str(ix))
            encoded = base64.encodebytes(buffer)
            decoded = base64.decodebytes(encoded)
            if decoded != buffer:
                print("Different: {:02x}".format(ix))
            for ix2 in range(32, 128):
                buffer += bytes(ix2)
                encoded = base64.encodebytes(buffer)
                decoded = base64.decodebytes(encoded)
                if decoded != buffer:
                    print("Different: {:02x}, {:02x}".format(ix, ix2))
        '''
if __name__ == '__main__':
    #import sys;sys.argv = ['', 'Test.testName']
    tester = CryptoEngineTest()
    tester.run()
