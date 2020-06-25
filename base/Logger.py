'''
Created: 2020.06.24
@license: CC0 https://creativecommons.org/publicdomain/zero/1.0
@author: hm
'''
import os
import datetime
import base.BaseLogger


class Logger(base.BaseLogger.BaseLogger):
    '''A feature reach class for logging messages of different levels.
    '''

    def __init__(self, logfile, verboseLevel):
        '''Constructor.
        @param logfile: the file for logging
        @param verboseLevel: > 0: logging to stdout too
        '''
        base.BaseLogger.BaseLogger.__init__(self, verboseLevel)
        self._logfile = logfile
        # Test accessability:
        try:
            with open(self._logfile, 'a'):
                pass
            os.chmod(self._logfile, 0o666)
        except OSError as exc:
            msg = '+++ cannot open logfile {}: {}'.format(
                self._logfile, str(exc))
            print(msg)
            self.error(msg)

    def log(self, message, minLevel=0):
        '''Logs a message.
        @param message: the message to log
        @param minLevel: the logging is done only if _verboseLevel >= minLevel
        @return: true: OK false: error on log file writing
        '''
        rc = False
        try:
            if not self._inUse and self._mirrorLogger is not None:
                self._mirrorLogger.log(message)
            now = datetime.datetime.now()
            message = now.strftime('%Y.%m.%d %H:%M:%S ') + message
            if self._verboseLevel >= minLevel:
                print(message)
            with open(self._logfile, 'a') as fp:
                rc = True
                fp.write(message + '\n')
        except:
            pass
        return rc


if __name__ == '__main__':
    pass
