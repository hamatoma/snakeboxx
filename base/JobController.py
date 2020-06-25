'''
Wait for jobs written as files in a defined directory.

Created: 2020.06.24
@license: CC0 https://creativecommons.org/publicdomain/zero/1.0
@author: hm
'''
import time
import os.path
import random

import base.StringUtils


class JobController:
    '''Wait for jobs written as files in a defined directory.
    Needed: overriding process()
    Format of the job file:
    <separator><name><separator><argument1>...
    Example of a job file:
    |email|a@bc.de|Greetings|Greetings from your family
    '''

    def __init__(self, jobDirectory, cleanInterval, logger):
        '''Constructor.
        @param jobDirectory: the jobs will be expected in this directory
        @param cleanInterval: files older than this amount of seconds will be deleted
        @param logger: for messages
        '''
        self._jobDirectory = jobDirectory
        if not os.path.exists(jobDirectory):
            os.makedirs(jobDirectory, 0o777, True)
        self._cleanInterval = cleanInterval
        self._logger = logger

    def check(self):
        '''Checks whether a new job is requested.
        @return: True: a new job has been found and processed
        '''
        files = os.listdir(self._jobDirectory)
        now = time.time()
        found = False
        for file in files:
            full = self._jobDirectory + os.sep + file
            if not file.endswith('.job'):
                date = os.path.getmtime(full)
                if date < now - self._cleanInterval:
                    self._logger.log('cleaning too old file {}'.format(
                        file), base.Const.LEVEL_LOOP)
                    os.unlink(full)
                    if os.path.exists(full):
                        self._logger.error('cannot delete ' + full)
            else:
                content = base.StringUtils.fromFile(full)
                if len(content) < 2:
                    self._logger.error('cleaning empty job file: ' + file)
                    os.unlink(full)
                    continue
                separator = content[0]
                parts = content[1:].split(separator)
                self._logger.log(
                    'processing ' + parts[0], base.Const.LEVEL_SUMMARY)
                self.process(parts[0], parts[1:])
                self._logger.log('removing processed job file',
                                 base.Const.LEVEL_FINE)
                os.unlink(full)
                found = True
                break
        return found

    def jobDirectory(self):
        '''Returns the current job directory.
        @return: the job directory
        '''
        return self._jobDirectory

    def process(self, name, args):
        '''Dummy method for processing a job. Must be overridden.
        @param name: name of the job
        @param args: the arguments as list
        @return False: error
        '''
        base.StringUtils.avoidWarning(name)
        base.StringUtils.avoidWarning(args)
        self._logger('missing overriding method process()')
        return False

    @staticmethod
    def writeJob(name, args, directory, logger):
        '''Writes a job into a job file.
        @param name: name of the job
        @param args: arguments as a list
        @param directory: the name of the job directory
        @param logger: for messages
        @return: True: success
        '''
        rc = True
        chars = name + ''.join(args)
        separator = None
        for item in ['|', '\t', '^', '°', '#', '~', '/', '\\', '`', '?', '$', '%']:
            if chars.find(item) < 0:
                separator = item
                break
        if separator is None:
            logger.error('I am confused: no separator is possible')
            rc = False
        else:
            fn = '{}{}t{:05d}{:x}.xxx'.format(directory, os.sep, int(
                time.time()) % 86400, random.randint(0x1000, 0xffff))
            suffix = '' if args is None or not args else separator + \
                separator.join(args)
            content = separator + name + suffix
            base.StringUtils.toFile(fn, content)
            fn2 = fn.replace('.xxx', '.job')
            os.rename(fn, fn2)
        return rc


if __name__ == '__main__':
    pass
