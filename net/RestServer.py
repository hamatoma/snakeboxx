'''
Created: 2020.06.24
@license: CC0 https://creativecommons.org/publicdomain/zero/1.0
@author: hm
'''
# coding=utf8
import json
import http.server

import base.Const

class TaskHandler:
    '''Does a specific service.
    '''

    def __init__(self, logger):
        '''Constructor.
        '''
        self._logger = logger
        self._requestHandler = None

    def setRequest(self, requestHandler):
        '''Setter.
        @param requestHandler: an instance of RestHTTPRequestHandler
        '''
        self._requestHandler = requestHandler

    def isRelevant(self, method):
        '''Tests whether the request can be serviced.
        Abstract method, should be overridden.
        @param method: the request method: 'DELETE', 'GET'
        @return True: the service can be handled
        '''
        base.StringUtils.avoidWarning(method)
        return False

    def service(self, method):
        '''Abstract method for doing the real service.
        Should be overridden.
        @param method: the request method: 'DELETE', 'GET'
        @return True: OK False: break chain handling
        '''
        base.StringUtils.avoidWarning(method)
        return False


class RestHTTPRequestHandler(http.server.BaseHTTPRequestHandler):
    '''Handles the requests for the REST service.
    There may be no constructor (invisible instantiation).
    '''

    def callHandler(self, method):
        '''Search for the matching TaskHandler and calls it.
        @param method: the request method
        '''
        self.server.logger.log('serving ' + method, base.Const.LEVEL_LOOP)
        if not self.isValidPath(self.path):
            self.server.logger.error('invalid path: ' + self.path)
            self.send_response(500)
            self.end_headers()
        else:
            self.stringData = ''
            self.byteData = b''
            self.jsonData = None
            self.httpStatus = 200
            self.mediaType = None
            self.inputBytes = b''
            if method in ('POST', 'PUT'):
                self.inputLength = int(self.headers['Content-Length'])
                if self.inputLength > 0:
                    self.inputBytes = self.rfile.read(self.inputLength)
                    self.inputString = self.inputBytes.decode('utf-8')
                if self.inputString.startswith('{') or self.inputString.startswith('['):
                    self.jsonData = json.loads(self.inputString)
            found = False
            for handler in self.server.restServer.taskHandlers:
                handler.setRequest(self)
                if handler.isRelevant(method):
                    found = True
                    if not handler.service(method):
                        break
            if not found:
                self.httpStatus = 404
            content = None
            if self.jsonData is not None:
                content = json.dumps(self.jsonData)
                if self.mediaType is None:
                    self.mediaType = 'text/json'
            if self.byteData:
                content = self.byteData
            elif self.stringData:
                content = self.stringData.encode('utf-8')
            if self.mediaType is None:
                self.mediaType = 'text/plain'
            self.send_header('Content-Type', self.mediaType)
            if content is not None:
                self.send_header('Length', str(len(content)))
            self.send_response(self.httpStatus)
            self.end_headers()
            if content is not None and content:
                # self.wfile.write(b"\n")
                self.wfile.write(content)

    def do_DELETE(self):
        '''Handles a request of the DELETE method.
        '''
        self.callHandler('DELETE')

    def do_GET(self):
        '''Handles a request of the GET method.
        '''
        self.callHandler('GET')

    def do_POST(self):
        '''Handles a request of the POST method.
        '''
        self.callHandler('POST')

    def do_PUT(self):
        '''Handles a request of the PUT method.
        '''
        self.callHandler('PUT')

    def isValidPath(self, path):
        '''Inspects the path (part of the URL) whether the service can be handled.
        Should be overridden.
        @param path: the path to inspect
        @return True: the service can be handled
        '''
        base.StringUtils.avoidWarning(path)
        rc = False
        return rc

class RestServer:
    '''A REST server which serves the URLS /<topic>/<resource>.
    Supports the methods PUT DELETE POST and GET.
    '''

    def __init__(self, address, port, logger):
        '''Constructor.
        @param addr: the address of the server, e.g. 'localhost'
        @param port: the port for listening
        @param logger: the logger
        '''
        self._address = address
        self._port = port
        self.logger = logger
        self.taskHandlers = []
        self.server = None

    def getServerInstance(self):
        '''Returns the instance of HTTPServer.
        Note: must be overridden because of the last parameter: the request handler class
        @return the the instance of HTTPServer
        '''
        rc = http.server.HTTPServer((self._address, self._port), RestHTTPRequestHandler)
        return rc

    def listen(self):
        '''Listens for connections and handles them.
        '''
        self.logger.log('listening on {:s}-{:d}'.format(self._address, self._port), base.Const.LEVEL_SUMMARY)
        self.server = self.getServerInstance()
        self.server.logger = self.logger
        self.server.restServer = self
        self.server.serve_forever()

    def registerTaskHandler(self, handler):
        '''Registers a task handler.
        @param handler: an instance of TaskHandler
        '''
        self.taskHandlers.append(handler)

    def stopListening(self):
        '''Stops the never ending loop.
        '''
        self.server.shutdown()

if __name__ == '__main__':
    pass
