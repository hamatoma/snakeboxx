'''
Created: 2020.06.24
@license: CC0 https://creativecommons.org/publicdomain/zero/1.0
@author: hm
'''
import random
import base64
import math
import time


class CryptoEngine:
    '''Implements a Pseudo Random Generator with the KISS algorithm.
    We want an algorithm which can be implemented in any programming language, e.g. in JavaScript or Java.
    JavaScript (at this moment) only contains floating point calculation.
    Java knows only signed integers or floating point numbers.
    Therefore we use IEEE 754 (64 bit floating point).
    '''

    def __init__(self, logger):
        '''Constructor.
        @param logger: the logger
        '''
        self._counter = 0
        self._base64Trailer = '!#$%&()*'
        self._uBoundBase64Tail = '*'
        self._x = 372194.0
        # @cond _y != 0
        self._y = 339219.0
        # @cond z | c != 0
        self._z = 470811222.0
        self._c = 1.0
        self._logger = logger

    def bytesToString(self, aBytes):
        '''Converts a string into a byte array without encoding.
        @param aBytes: byte array to convert
        @return a string
        '''
        try:
            rc = aBytes.decode('ascii')
        except UnicodeDecodeError as exc:
            rc = -1
            raise exc
        return rc

    def decode(self, string, charSet):
        '''Decodes a string encoded by encode().
        Format of the string: version salt encrypted
        '0' (version string)
        4 characters salt
        rest: the encrypted string
        @param string: string to encode
        @param charSet: the character set of the string and the result, e.g. 'word'
        @return: the decoded string (clear text)
        '''
        self._counter += 1
        aSet = self.getCharSet(charSet)
        aSize = len(aSet)
        rc = ''
        if string.startswith('0'):
            prefix = string[1:5]
            string = string[5:]
            aHash = self.hash(prefix)
            self.setSeed(aHash, 0x20111958, 0x4711, 1)
            length = len(string)
            for ix in range(length):
                ix3 = aSet.find(string[ix])
                ix2 = (aSize + ix3 - self.nextInt(aSize - 1)) % aSize
                rc += aSet[ix2]
        return rc

    def decodeBinary(self, string):
        '''Decodes a string encrypted by encryptBinary().
        @param string: string to decode
        @return: the decoded string (clear text)
        '''
        aSet = self.getCharSet('base64')
        aSize = len(aSet)
        rc = ''
        if string.startswith('0'):
            prefix = string[1:5]
            string = string[5:]
            aHash = self.hash(prefix)
            self.setSeed(aHash, 0x20111958, 0x4711, 1)
            aLen = len(string)
            buffer = ''
            # replace the trailing '=' "randomly" with a char outside the
            # character set:
            if aLen > 0 and string[aLen - 1] == '=':
                string[aLen - 1] = self._base64Trailer[self._counter * 7 %
                                                       len(self._base64Trailer)]
            if aLen > 1 and string[aLen - 2] == '=':
                string[aLen - 2] = self._base64Trailer[self._counter * 13 %
                                                       len(self._base64Trailer)]
            for ix in range(aLen):
                ix3 = aSet.find(string[ix])
                ix2 = (aSize + ix3 - self.nextInt(aSize - 1)) % aSize
                buffer += aSet[ix2]
            binBuffer = self.stringToBytes(buffer + '\n')
            try:
                binBuffer2 = base64.decodebytes(binBuffer)
            except Exception as exc:
                if str(exc) == 'Incorrect padding':
                    try:
                        binBuffer = binBuffer[0:-1]
                        binBuffer2 = base64.decodebytes(binBuffer)
                    except Exception:
                        binBuffer = binBuffer[0:-1]
                        binBuffer2 = base64.decodebytes(binBuffer)
            ix = binBuffer2.find(b'\n')
            if ix >= 0:
                binBuffer2 = binBuffer2[0:ix]
            rc = self.bytesToString(binBuffer2)
        return rc

    def encode(self, string, charSet):
        '''Encodes a string with a randomly generated salt.
        Format of the string: version salt encoded
        '0' (version string)
        4 characters salt
        rest: the encoded string
        @param string: string to encode
        @param charSet: the character set of the string and the result, e.g. 'word'
        @return: the encrypted string
        '''
        self._counter += 1
        self.setSeedRandomly()
        rc = self.nextString(4, charSet)
        aSet = self.getCharSet(charSet)
        aSize = len(aSet)
        aHash = self.hash(rc)
        self.setSeed(aHash, 0x20111958, 0x4711, 1)
        length = len(string)
        for ix in range(length):
            ix3 = aSet.find(string[ix])
            ix2 = (ix3 + self.nextInt(aSize - 1)) % aSize
            rc += aSet[ix2]
        return '0' + rc

    def encodeBinary(self, string):
        '''Encrypts a string with a randomly generated salt.
        The string can be based on any char set. It will be base64 encoded before encryption.
        Format of the result: version salt encrypted
        '0' (version string)
        4 characters salt
        rest: the encrypted string
        @param string: the string or bytes to encrypt
        @return: the encoded string
        '''
        self.setSeedRandomly()
        if isinstance(string, str):
            string = self.stringToBytes(string)
        # convert it to a ascii usable string
        string += b'\n'
        buffer = base64.encodebytes(string)
        string = self.bytesToString(buffer).rstrip()
        rc = self.nextString(4, 'base64')
        aSet = self.getCharSet('base64')
        aSize = len(aSet)
        aHash = self.hash(rc)
        self.setSeed(aHash, 0x20111958, 0x4711, 1)
        length = len(string)
        for ix in range(length):
            ix3 = aSet.find(string[ix])
            ix2 = (ix3 + self.nextInt(aSize - 1)) % aSize
            rc += aSet[ix2]
        return '0' + rc

    def getCharSet(self, name):
        '''Returns a string with all characters of the charset given by name.
        @param name: the name of the charset
        @return: None: unknown charset
            otherwise: the charset as string
        '''
        if name == 'dec':
            rc = '0123456789'
        elif name == 'hex':
            rc = '0123456789abcdef'
        elif name == 'upper':
            rc = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        elif name == 'lower':
            rc = 'abcdefghijklmnopqrstuvwxyz'
        elif name == 'alfa':
            rc = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
        elif name == 'word':
            rc = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_'
        elif name == 'ascii94':
            rc = r'''!"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~'''
        elif name == 'ascii95':
            rc = r''' !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~'''
        elif name == 'ascii':
            rc = r''' !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~''' + chr(
                127)
        elif name == 'base64':
            rc = r'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
        else:
            self._logger.error('unknown character set: ' + name)
            rc = ''

        return rc

    def getCharSetNames(self):
        '''Returns the list of the known charset names.
        @return the list of the known charset names
        '''
        rc = [
            'dec',
            'hex',
            'upper',
            'lower',
            'alfa',
            'word',
            'ascii94',
            'ascii95',
            'ascii',
            'base64']
        return rc

    def hash(self, string):
        '''Converts a string into an integer.
        @param string: the string to convert
        @return: the hash value
        '''
        rc = len(string)
        count = rc
        for ix in range(count):
            rc = (rc * (ix + 1) +
                  (ord(string[ix]) << (ix % 4 * 7))) & 0x7fffffff
        return rc

    def nextChar(self, charSet='ascii'):
        '''Returns a pseudo random character.
        @param charSet: the result is a character from this string
        @return: a pseudo random character
        '''
        aSet = self.getCharSet(charSet)
        ix = self.nextInt(0, len(aSet) - 1)
        rc = aSet[ix]
        return rc

    def nextInt(self, maxValue=0x7fffffff, minValue=0):
        '''Returns a pseudo random 31 bit integer.
        @param maxValue: the maximal return value (inclusive)
        @param minValue: the minimal return value (inclusive)
        @return: a number from [minValue..maxValue]
        '''
        if maxValue == minValue:
            rc = minValue
        else:
            if minValue > maxValue:
                maxValue, minValue = minValue, maxValue
            rc = self.nextSeed()
            rc = rc % (maxValue - minValue) + minValue
        return rc

    def nextString(self, length, charSet):
        '''Returns a pseudo random string.
        @param length: the length of the result
        @param charSet: all characters of the result are from this string
        @return: a pseudo random string with the given charset and length
        '''
        aSet = self.getCharSet(charSet)
        aSize = len(aSet)
        rc = ''
        aRandom = None
        for ix in range(length):
            if ix % 4 == 0:
                aRandom = self.nextSeed()
            else:
                aRandom >>= 8
            rc += aSet[aRandom % aSize]
        return rc

    def nextSeed(self):
        '''Sets the next seed and returns a 32 bit random value.
        @return: a pseudo random number with 0 <= rc <= 0xffffffff
        '''
        # linear congruential generator (LCG):
        self._x = math.fmod(69069.0 * self._x + 473219.0, 4294967296)
        # Xorshift
        #self._y ^= int(self._y) << 13
        self._y = math.fmod(int(self._y) ^ int(self._y) << 13, 4294967296)
        #self._y ^= self._y >> 17
        self._y = math.fmod(int(self._y) ^ int(self._y) >> 17, 4294967296)
        #self._y ^= self._y << 5
        self._y = math.fmod(int(self._y) ^ int(self._y) << 5, 4294967296)
        # multiply with carry:
        t = 698769069.0 * self._z + self._c
        #self._c = math.fmod(t >> 32, 2)
        self._c = math.fmod(int(t) >> 32, 2)
        self._z = math.fmod(t, 4294967296)
        return int(math.fmod(self._x + self._y + self._z, 4294967296))

    def oneTimePad(self, user, data):
        '''Builds a one time pad.
        @param user:    the user id
        @param data: None or additional data: allowed char set: word
        @return: char set: word
        '''
        if data is not None and self.testCharSet(data, 'word') >= 0:
            rc = ''
        else:
            padData = '{:08x}{:04x}'.format(
                int(round(time.time())), user) + data
            rc = self.encode(padData, 'word')
        return rc

    def restoreSeed(self, seed):
        '''Returns the current seed as string.
        @return the seed as string
        '''
        parts = seed.split(':')
        self.setSeed(float(parts[0]), float(parts[1]),
                     float(parts[2]), float(parts[3]))

    def saveSeed(self):
        '''Returns the current seed as string.
        @return the seed as string
        '''
        rc = '{}:{}:{}:{}'.format(repr(self._x), repr(
            self._y), repr(self._z), repr(self._c))
        return rc

    def setSeed(self, x, y, z, c):
        '''Sets the parameter of the KISS algorithm.
        @param x:
        @param y:
        @param z:
        @param c:
        '''
        self._x = math.fmod(x, 4294967296)
        self._y = 1234321.0 if y == 0 else math.fmod(y, 4294967296)
        if z == 0 and c == 0:
            c = 1.0
        self._c = math.fmod(c, 2)
        self._z = math.fmod(z, 4294967296)

    def setSeedFromString(self, seedString):
        '''Converts a string, e.g. a password, into a seed.
        @param seedString: the string value to convert
        '''
        if seedString == '':
            seedString = 'Big-Brother2.0IsWatching!You'
        while len(seedString) < 8:
            seedString += seedString
        x = self.hash(seedString[0:len(seedString) - 3])
        y = self.hash(seedString[1:8])
        z = self.hash(seedString[3:5])
        c = self.hash(seedString[1:])
        self.setSeed(x, y, z, c)

    def setSeedRandomly(self):
        '''Brings "true" random to the seed
        '''
        utime = time.time()
        rand1 = int(math.fmod(1000 * 1000 * utime, 1000000000.0))
        rand2 = int(math.fmod(utime * 1000, 1000000000.0))
        self.setSeed(rand1, rand2, int(random.random() * 0x7fffffff), 1)

    def stringToBytes(self, string):
        '''Converts a string into a byte array without encoding.
        @param string: string to convert
        @return a bytes array
        '''
        rc = string.encode('ascii')
        return rc

    def testCharSet(self, string, charSet):
        '''Tests whether all char of a string belong to a given charSet.
        @param string: string to test
        @param charSet: the char set to test
        @return: -1: success
            otherwise: the index of the first invalid char
        '''
        aSet = self.getCharSet(charSet)
        rc = -1
        for ix, item in enumerate(string):
            if aSet.find(item) < 0:
                rc = ix
                break
        return rc

    def unpackOneTimePad(self, pad, maxDiff=60):
        '''Decodes a one time pad.
        @param pad: the encoded one time pad
        @param maxDiff: maximal difference (in seconds) between time of the pad and now
        @return: None: invalid pad
            otherwise: a tuple (time, user, data)
        '''
        padData = self.decode(pad, 'word')
        length = len(padData)
        if length < 12 or self.testCharSet(padData[0:12], 'hex') >= 0 or self.testCharSet(padData[12:], 'word') >= 0:
            rc = None
        else:
            padTime = int(padData[0:8], 16)
            now = time.time()
            if abs(now - padTime) >= maxDiff:
                rc = None
            else:
                user = int(padData[8:12], 16)
                data = None if len(padData) == 12 else padData[12:]
                rc = (padTime, user, data)
        return rc


if __name__ == '__main__':
    pass
