'''
Created: 2020.06.24
@license: CC0 https://creativecommons.org/publicdomain/zero/1.0
@author: hm
'''
import datetime
import sys
import http.server

import base.MemoryLogger
import net.RestServer


class SimpleTaskHandler(net.RestServer.TaskHandler):
    '''Handles a task of the SimpleRestServer.
    '''

    def isRelevant(self, method):
        '''Tests whether the request can be serviced.
        Abstract method, should be overridden.
        @param method: the request method: 'DELETE', 'GET'
        @return True: the service can be handled
        '''
        return False

    def service(self, method):
        '''Abstract method for doing the real service.
        @param method: the request method: 'DELETE', 'GET'
        '''


class EchoTaskHandler(SimpleTaskHandler):
    '''Handles the echo command.
    '''

    def isRelevant(self, method):
        '''Tests whether the request can be serviced.
        Abstract method, should be overridden.
        @param method: the request method: 'DELETE', 'GET'
        @return True: the service can be handled
        '''
        rc = method in (
            'GET', 'POST', 'PUT') and self._requestHandler.task == 'echo'
        return rc

    def service(self, method):
        '''Abstract method for doing the real service.
        @param method: the request method: 'DELETE', 'GET'
        '''
        if method == 'GET':
            if self._requestHandler.resource == 'time':
                self._requestHandler.stringData = datetime.datetime.now(
                ).strftime('%Y.%m.%d %H:%M:%S\n')
            elif self._requestHandler.resource == 'ip':
                (host, port) = self._requestHandler.client_address
                self._requestHandler.stringData = '{:s}:{:d}\n'.format(
                    host, port)

            else:
                self._requestHandler.stringData = self._request.resource + "\n"
            if self._requestHandler.paramMap:
                self._requestHandler.stringData += repr(
                    self._requestHandler.paramMap) + "\n"
        else:
            self._requestHandler.stringData = self._requestHandler.inputString + "\n"
            if self._requestHandler.paramMap:
                self._requestHandler.stringData += repr(
                    self._requestHandler.paramMap) + "\n"


class SimpleRestHTTPRequestHandler(net.RestServer.RestHTTPRequestHandler):
    '''Request handler for the SimpleRestServer.
    '''

    def isValidPath(self, path):
        '''Inspects the path (part of the URL) whether the service can be handled.
        @param path: the path to inspect
        @return True: the service can be handled
        '''
        self.task = None
        self.resource = None
        if path.startswith('/'):
            path = path[1:]
        rc = False
        parts = path.split('?', 1)
        if parts[0].endswith('/'):
            parts[0] = parts[0][0:-1]
        self.params = []
        self.paramMap = {}
        if len(parts) == 1:
            self.params = []
            nodes = path.split('/')
            if len(nodes) == 2:
                self.task = nodes[0]
                self.resource = nodes[1]
                rc = True
        else:
            self.params = parts[1].split('&')
            for param in self.params:
                parts2 = param.split('=', 1)
                if len(parts2) == 2:
                    self.paramMap[parts2[0]] = parts2[1]
        self.pathNodes = parts[0].split('/')
        if len(self.pathNodes) >= 2:
            self.task = self.pathNodes[0]
            self.resource = self.pathNodes[1]
            rc = True
        return rc


class SimpleRestServer(net.RestServer.RestServer):
    '''A REST server which serves the URLS /<topic>/<resource>.
    Supports the methods PUT DELETE POST and GET.
    '''

    def getServerInstance(self):
        '''Returns the instance of HTTPServer.
        Note: must be overridden because of the last parameter: the request handler class
        @return the the instance of HTTPServer
        '''
        rc = http.server.HTTPServer(
            (self._address, self._port), SimpleRestHTTPRequestHandler)
        return rc


def main(argv):
    '''Main function.
    '''
    base.StringUtils.avoidWarning(argv)
    logger = base.MemoryLogger.MemoryLogger(4)
    taskHandler = EchoTaskHandler(logger)
    server = SimpleRestServer('localhost', 58133, logger)
    server.registerTaskHandler(taskHandler)
    server.listen(SimpleRestHTTPRequestHandler)


if __name__ == '__main__':
    main(sys.argv[1:])
