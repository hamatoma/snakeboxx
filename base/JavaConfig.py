'''
Created: 2020.06.24
@license: CC0 https://creativecommons.org/publicdomain/zero/1.0
@author: hm
'''
import re
import os.path


class JavaConfig:
    '''
    Handles a java style configuration file.
    Format:
    <variable> = <value>
    # comment
    '''

    def __init__(self, filename, logger, ignoreIniHeader=False):
        '''
        Constructor.
        @param filename: None: the instance remain "empty" otherwise: the filename with path
        @param logger: the logger
        @param ignoreIniHeader: True: '[<section>]' will be ignored
        '''
        self._ignoreIniHeader = ignoreIniHeader
        self._vars = dict()
        self._logger = logger
        if filename is not None:
            self.readConfig(filename)

    def readConfig(self, filename):
        '''Reads the configuration file and put the data into the instance.
        @param filename: the name of the configuration file
        '''
        self._filename = filename
        self._vars = dict()
        regExpr = re.compile(r'([\w.]+)\s*=\s*(.*)$')
        if not os.path.exists(filename):
            self._logger.error('missing ' + filename)
        else:
            with open(filename, "r") as fp:
                lineNo = 0
                for line in fp:
                    lineNo += 1
                    line = line.strip()
                    if line.startswith('#') or line == '':
                        continue
                    matcher = regExpr.match(line)
                    if matcher is not None:
                        self._vars[matcher.group(1)] = matcher.group(2)
                    elif self._ignoreIniHeader and line.startswith('['):
                        continue
                    else:
                        self._logger.error('{:s} line {:d}: unexpected syntax [expected: <var>=<value>]: {:s}'.format(
                            filename, lineNo, line))

    def getBool(self, variable, defaultValue=None):
        '''Returns the value of a given variable.
        @param variable: name of the Variable
        @param defaultValue: if variable does not exist this value is returned
        @return: None: Variable not found or not a bool value
            otherwise: the bool value
        '''
        rc = defaultValue
        if variable in self._vars:
            value = self._vars[variable].lower()
            if value in ('t', 'true', 'yes'):
                rc = True
            elif value in ('f', 'false', 'no'):
                rc = False
            else:
                self._logger.error("{}: variable {} is not a boolean: {}".format(
                    self._filename, variable, value))
                rc = defaultValue
        return rc

    def getInt(self, variable, defaultValue=None):
        '''Returns the value of a given variable.
        @param variable: name of the Variable
        @param defaultValue: if variable does not exist this value is returned
        @return: None: Variable not found or not an integer
            otherwise: the int value
        '''
        rc = defaultValue
        if variable in self._vars:
            value = self._vars[variable]
            try:
                rc = int(value)
            except ValueError:
                self._logger.error("{}: variable {} is not an integer: {}".format(
                    self._filename, variable, value))
                rc = defaultValue
        return rc

    def getString(self, variable, defaultValue=None):
        '''Returns the value of a given variable.
        @param variable: name of the Variable
        @param defaultValue: if variable does not exist this value is returned
        @return: None: Variable not found otherwise: the value
        '''
        rc = defaultValue if variable not in self._vars else self._vars[variable]
        return rc

    def getKeys(self, regExpr=None):
        r'''Returns an array of (filtered) keys.
        @param regExpr: None or a regular expression to filter keys. regExpr can be an object or a text
            example: re.compile(r'^\s*pattern.\d+$', re.I)
        @return: the array of sorted keys matching the regExpr
        '''
        if isinstance(regExpr, str):
            regExpr = re.compile(regExpr)
        keys = self._vars.keys()
        rc = []
        for key in keys:
            if regExpr is None or regExpr.search(key):
                rc.append(key)
        rc.sort()
        return rc
