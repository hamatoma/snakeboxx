#! /usr/bin/python3
'''
processhelper: starting external scripts/programs

Created: 2020.06.24
@license: CC0 https://creativecommons.org/publicdomain/zero/1.0
@author: hm
'''
import subprocess
import tempfile
import os
import time
#import sys

import base.StringUtils


class ProcessHelper:
    '''Executes external processes.
    '''

    def __init__(self, logger):
        '''Constructor:
        @param logger: display output
        '''
        self._logger = logger
        self._output = None
        self._rawOutput = None
        self._error = None

    def execute(self, argv, logOutput, storeOutput=False, mode='!shell', timeout=None, currentDirectory=None):
        '''Executes an external program with input from stdin.
        @param argv: a list of arguments, starting with the program name
        @param logOutput: True: the result of stdout is written to stdout via logger.
        @param storeOutput: True: the raw output is available as self._output[]
        @param timeout: None or the timeout of the external program
        @return: None (logOutput==False) or array of strings
        '''
        curDir = self.pushd(currentDirectory)
        if argv is None:
            self._logger.error('execute(): missing argv (is None)')
        elif curDir != '':
            self._logger.log('executing: ' + ' '.join(argv),
                             base.Const.LEVEL_LOOP)
            shell = mode == 'shell'
            proc = subprocess.Popen(
                argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=shell)
            (out, err) = proc.communicate(None, timeout)
            self._output = []
            self._error = []
            if logOutput or storeOutput:
                for line in out.decode().split('\n'):
                    line2 = line.rstrip()
                    if len(line) > 1:
                        if storeOutput:
                            self._output.append(line2)
                        if logOutput:
                            self._logger.log(line2, base.Const.LEVEL_SUMMARY)
            for line in err.decode().split('\n'):
                msg = line.rstrip()
                if msg != '':
                    self._error.append(msg)
                    self._logger.error(msg)
        self.popd(curDir)
        return None if not logOutput else self._output

    def executeCommunicate(self, process, inputString, logOutput, timeout):
        '''Handles the output of subprocess calls.
        @param process: the process to inspect
        @param inputString: None or an input string
        @param logOutput: True: output should be returned
        @param timeout: the longest time a process should use
        '''
        if inputString is None:
            (out, err) = process.communicate(timeout=timeout)
        else:
            (out, err) = process.communicate(inputString.encode(), timeout)
        self._rawOutput = out
        if logOutput:
            for line in out.decode().split('\n'):
                if line != '':
                    self._output.append(line)
                    self._logger.log(line, base.Const.LEVEL_SUMMARY)
        for line in err.decode().split('\n'):
            if line != '':
                self._error.append(line)
                self._logger.error(line)

    def executeInput(self, argv, logOutput, inputString=None, mode='!shell', timeout=None):
        '''Executes an external program with input from stdin.
        @param argv: a list of arguments, starting with the program name
        @param logOutput: True: the result of stdout is written to stdout via logger.
            Note: the raw output is available as self._output[]
        @param inputString: None or the input for the program as string
        @param timeout: None or the timeout of the external program
        '''
        self._output = []
        self._error = []
        if inputString is None:
            inputString = ''
        self._logger.log('executing: ' + ' '.join(argv), base.Const.LEVEL_LOOP)
        if mode == 'not used and shell':
            fn = tempfile.gettempdir() + '/dbtool.' + str(time.time())
            base.StringUtils.toFile(fn, inputString)
            command = argv[0] + " '" + "' '".join(argv[1:]) + "' < " + fn
            subprocess.run([command], check=True, shell=True)
            os.unlink(fn)
        else:
            try:
                proc = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE, shell=mode == 'shell')
                self.executeCommunicate(proc, inputString, logOutput, timeout)
            except OSError as exc:
                msg = str(exc)
                self._logger.error(msg)
                self._error = msg.split('\n')
            except Exception as exc2:
                msg = str(exc2)
                self._logger.error(msg)
                self._error = msg.split('\n')

    def executeInputOutput(self, argv, inputString=None, logOutput=False, mode='!shell', timeout=None):
        '''Executes an external program with input from stdin and returns the output.
        @param argv: a list of arguments, starting with the program name
        @param inputString: None or the input for the program as string
        @param timeout: None or the timeout of the external program
        @return: a list of lines (program output to stdout)
        '''
        self.executeInput(argv, logOutput, inputString, mode, timeout)
        rc = self._output
        if (rc is None or not rc) and self._rawOutput is not None and self._rawOutput != '':
            try:
                rc = self._rawOutput.decode('utf-8').split('\n')
            except UnicodeDecodeError as exc:
                self._logger.error('executeInputOutput(): {}\n[{}]\n"{}"'.format(
                    str(exc), ','.join(argv), '' if inputString is None else inputString[0:80]))
                rc = base.StringUtils.minimizeArrayUtfError(self._rawOutput.split(b'\n'),
                                                            self._logger if self._logger._verboseLevel >= 2 else None)
        return rc

    def executeInChain(self, argv1, inputString, argv2, mode='shell', timeout=None):
        '''Executes 2 programs with input from stdin as chain and returns the output.
        @param argv1: a list of arguments for the first program, starting with the program name
        @param inputString: None or the input for the first program as string
        @param argv2: a list of arguments for the second program, starting with the program name
        @param timeout: None or the timeout of the external program
        @return: a list of lines (program output to stdout)
        '''
        self._output = []
        self._error = []
        self._logger.log('executing: ' + ' '.join(argv1) +
                         '|' + ' '.join(argv2), base.Const.LEVEL_LOOP)
        rc = []
        if mode == 'shell':
            fnOut = tempfile.gettempdir() + '/dbtool.out.' + str(time.time())
            if inputString is None:
                inputPart = ''
            else:
                fnIn = tempfile.gettempdir() + '/dbtool.in.' + str(time.time())
                inputPart = "< '" + fnIn + "' "
                base.StringUtils.toFile(fnIn, inputString)
            command = (argv1[0] + " '" + "' '".join(argv1[1:]) + "' " + inputPart + "| "
                       + argv2[0] + " '" + "' '".join(argv2[1:]) + "' > " + fnOut)
            try:
                subprocess.run([command], check=True, shell=True)
                data = base.StringUtils.fromFile(fnOut)
                rc = self._output = data.split('\n')
            except Exception as exc:
                self._logger.error(str(exc))
            if inputString is not None:
                os.unlink(fnIn)
            os.unlink(fnOut)
        else:
            try:
                p1 = subprocess.Popen(argv1, stdout=subprocess.PIPE)
                p2 = subprocess.Popen(
                    argv2, stdin=p1.stdout, stdout=subprocess.PIPE)
                # Allow p1 to receive a SIGPIPE if p2 exits.
                p1.stdout.close()
                self.executeCommunicate(p2, None, True, timeout)
                rc = self._output
            except Exception as exc:
                self._logger.error(str(exc))
        return rc

    def executeScript(self, script, node=None, logOutput=True, args=None, timeout=None):
        '''Executes an external program with input from stdin.
        @param script: content of the script
        @param node: script name without path (optional)
        @param logOutput: True: the result of stdout is written to stdout via logger.
            Note: the raw output is available as self._output[]
        @param args: None or an array of additional arguments, e.g. ['-v', '--dump']
        @param timeout: None or the timeout of the external program
        @return: None (logOutput==False) or array of strings
        '''
        self._logger.log('executing {}...'.format(
            'script' if node is None else node), base.Const.LEVEL_LOOP)
        if node is None:
            node = 'processtool.script'
        fn = tempfile.gettempdir() + os.sep + node + str(time.time())
        base.StringUtils.toFile(fn, script)
        os.chmod(fn, 0o777)
        argv = [fn]
        if args is not None:
            argv += args
        rc = self.execute(argv, logOutput, 'shell', timeout)
        os.unlink(fn)
        return rc

    def popd(self, directory):
        '''Changes the current direcory (if needed and possible).
        @param directory: None or the new current directory
        @return None: directory = None
            '': changing directory failed
            otherwise: the current directory (before changing)
        '''
        if directory is not None and directory != '':
            os.chdir(directory)
            if os.path.realpath(os.curdir) != os.path.realpath(directory):
                self._logger.error('cannot change to directory ' + directory)

    def pushd(self, directory):
        '''Changes the current direcory (if needed and possible).
        @param directory: None or the new current directory
        @return None: directory = None
            '': changing directory failed
            otherwise: the current directory (before changing)
        '''
        if directory is None:
            rc = None
        else:
            rc = os.curdir
            os.chdir(directory)
            if os.path.realpath(os.curdir) != os.path.realpath(directory):
                os.chdir(rc)
                self._logger.error('cannot change to directory ' + directory)
                rc = ''
        return rc
