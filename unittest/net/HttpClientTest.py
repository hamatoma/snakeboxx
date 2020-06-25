'''
Created on 12.04.2018

@author: hm
'''
import re

from unittest.UnitTestCase import UnitTestCase
import base.MemoryLogger
import net.HttpClient

DEBUG = False

class HttpClientTest(UnitTestCase):

    def testGetContent(self):
        if DEBUG: return
        logger = base.MemoryLogger.MemoryLogger()
        client = net.HttpClient.HttpClient(logger, 2)
        content = client.getContent('http://ip.hamatoma.de', 1)
        self.assertMatches(r'(\d+\.){3}\d+', content)
        content = client.getContent('https://wiki.hamatoma.de', 3)
        self.assertTrue(content.startswith('<!DOCTYPE html>'))

    def testGetHeader(self):
        if DEBUG: return
        logger = base.MemoryLogger.MemoryLogger()
        client = net.HttpClient.HttpClient(logger, 2)
        headers = client.getHead('https://wiki.hamatoma.de', 3)
        self.assertTrue(headers is not None and 'Content-Type' in headers)

    def testGetHeaderField(self):
        if DEBUG: return
        logger = base.MemoryLogger.MemoryLogger()
        client = net.HttpClient.HttpClient(logger, 2)
        client.getHead('https://wiki.hamatoma.de', 3)
        item = client.getHeaderField('content-type')
        self.assertEquals('text/html; charset=UTF-8', item)

    def testPutSimpleRest(self):
        if DEBUG: return
        logger = base.MemoryLogger.MemoryLogger(1)
        client = net.HttpClient.HttpClient(logger, 2)
        client.putSimpleRest('https://wiki.hamatoma.de', 'test', 'data', { 'a': 'b'})
        self.assertEquals(client._response.status, 405)

if __name__ == '__main__':
    #import sys;sys.argv = ['', 'Test.testName']
    tester = HttpClientTest()
    tester.run()
