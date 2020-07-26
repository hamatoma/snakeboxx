'''
Created: 2020.06.24
@license: CC0 https://creativecommons.org/publicdomain/zero/1.0
@author: hm
'''

# coding=utf8
import json
import urllib3

import base.Logger


class HttpClient:
    '''Implements a HTTP or HTTPS client.
    '''

    def __init__(self, logger, timeout=10):
        '''Constructor.
        @param logger: the logger, type Logger
        @param timeout: the request is aborted after this amount of seconds
        '''
        self._logger = logger
        self._data = None
        self._response = None
        self._pool = urllib3.PoolManager()
        self._timeout = timeout

    def close(self):
        '''Frees the resources.
        '''

    def _headers(self):
        '''Returns the headers of the last response.
        @return: None: nothing available otherwise: a dictionay with the headers, e.g. '{ 'Content-Type': 'text/plain' }
        '''
        map1 = {}
        if self._response is not None:
            for key in self._response.headers:
                map1[key] = self._response.headers[key]
        return map1

    def _handleSingleRequest(self, url, method, content=None, contentType=None, timeout=None, retries=False):
        '''Handles a single HTTP(S) request (not following relocations).
        @param url: the URL of the website
        @param method: the request method, e.g. 'HEAD'
        @param content: only for 'PUT'/'POST': body of the request. If a dict: will be encoded as JSON
        @param contentType: None: automatic selection
        @param timeout: None: use _timeout otherwise: the request is aborted after this amount of seconds
        @param retries: configure the number of retries to allow before raising a
            @class:`~urllib3.exceptions.MaxRetryError` exception.
            Pass ``None`` to retry until you receive a response. Pass a
            @class:`~urllib3.util.retry.Retry` object for fine-grained control
            over different types of retries.
            Pass an integer number to retry connection errors that many times,
            but no other types of errors. Pass zero to never retry.
            If ``False``, then retries are disabled and any exception is raised
            immediately. Also, instead of raising a MaxRetryError on redirects,
            the redirect response will be returned.
       '''
        self._data = None
        self._response = None
        try:
            if method in ('POST', 'PUT'):
                if isinstance(content, dict):
                    content2 = json.dumps(
                        content, ensure_ascii=False)
                    content = content.encode(
                        'UTF-8') if isinstance(content2, bytes) else content2
                if contentType is None:
                    contentType = 'application/json; charset=UTF-8' if content.startswith(
                        '{') else 'text/plain; charset=utf-8'
                #self._logger.log('340: ' + content[340:], 4)
                self._logger.log(
                    'sending: ' + '<none>' if content is None else content, 4)
                self._response = self._pool.request(method, url, body=content.encode('UTF-8'),
                                                    headers={'Content-Type': contentType}, timeout=timeout, retries=retries)
            else:
                self._response = self._pool.request(
                    method, url, timeout=timeout, retries=retries)
                if method == 'GET':
                    self._data = self._response.read()
                    if self._data == b'' and self._response.data is not None:
                        self._data = self._response.data
        except Exception as exc:
            self._logger.error('error on processing [{}] {}: {} [{}]'.format(
                method, url, str(exc), str(type(exc))))
        if self._response is None:
            self._logger.error('url: {}: no response'.format(url))
        elif self._response.status >= 400:
            self._logger.error('status {} [{}] for {}'.format(
                self._response.status, self._response.reason, url))
        else:
            self._logger.log('url: {} status: {} reason: {}'.format(
                url, self._response.status, self._response.reason), 4)

    def getContent(self, url, relocationCount=0):
        '''Returns the header of a website.
        @param url: the URL of the website
        @param relocationCount: number of relocations to follow
        @return: '' or the html content
        '''
        self.handleRequest(url, 'GET', relocationCount)
        data = self._data
        return data

    def getHead(self, url, relocationCount=5):
        '''Returns the header of a website.
        @param url: the URL of the website
        @param relocationCount: number of relocations to follow
        @return: the dictionary with the headers
        '''
        self.handleRequest(url, 'HEAD', relocationCount)
        rc = self._headers()
        return rc

    def getHeaderField(self, field, defaultValue=None):
        '''Gets the value of a header field.
        @param field: name of the header field, e.g. 'content-length'
        @return defaultValue: the field is unknown
            otherwise: the value of the field
        '''
        rc = defaultValue
        field = field.lower()
        if self._response is not None:
            for key in self._response.headers:
                if key.lower() == field:
                    rc = self._response.headers[key]
                    break
        return rc

    def getRealUrl(self, url):
        '''Returns the first not relocated URL of a given URL.
        @param url: URL to inspect
        @return: <url>: url is not relocated otherwise: the first not relocated URL of a chain
        '''
        self._handleSingleRequest(url, 'HEAD')
        while self._response is not None and self._response.status > 300 and self._response.status < 400:
            url = self.getHeaderField('location', '')
            self._handleSingleRequest(url, 'HEAD')
        return url

    def handleRequest(self, url, method, relocationCount, content=None, contentType=None, timeout=None, convertToText=True):
        '''Handles a HTTP request.
        @param url: the URL of the website
        @param method: the request method, e.g. 'HEAD'
        @param relocationCount: number of relocations to follow
        @param content: only for 'PUT'/'POST': body of the request. If a dict: will be encoded as JSON
        @param contentType: None: automatic selection
        @param timeout: None: use _timeout otherwise: the request is aborted after this amount of seconds
        @return: url of the end of the relocation chain
        '''
        self._handleSingleRequest(url, method, content, contentType, timeout)
        status = 499 if self._response is None else self._response.status
        while relocationCount > 0 and (301 <= status < 400):
            relocationCount -= 1
            url = self.getHeaderField('location', '')
            self._handleSingleRequest(
                url, method, content, contentType, timeout)
            status = 499 if self._response is None else self._response.status
        if convertToText and isinstance(self._data, bytes):
            self._data = self._data.decode()
        return url

    def putSimpleRest(self, url, task, resource, data, timeout=None):
        '''Puts a REST request with the Simple-REST standard.
        @param url: the request target
        @param task: the task name, e.g. 'send'
        @param resource: a further specification of the request, e.g. 'db'
        @param data: the data to put: a string or a dictionary
        @param timeout: None: use _timeout otherwise: the request is aborted after this amount of seconds
        '''
        self._handleSingleRequest(
            url + '/' + task + '/' + resource, 'PUT', data, None, timeout)


def main():
    '''Main function.
    '''
    logger = base.Logger.Logger('/tmp/httpclient.log', True)
    client = HttpClient(logger, 1)
    url = 'https://wiki.hamatoma.de'
    data = client.getHead(url)
    print('header of {}:\n{}'.format(url, str(data).replace(', ', ',\n')))
    client.close()


if __name__ == '__main__':
    main()
