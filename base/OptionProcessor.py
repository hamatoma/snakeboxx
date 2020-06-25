'''
Created: 2020.06.24
@license: CC0 https://creativecommons.org/publicdomain/zero/1.0
@author: hm
'''
import re

import base.Const
import base.StringUtils


class Option:
    '''Stores a single option.
    '''

    def __init__(self, name, longName, shortName, description, example,
                 dataType='string', mode=None, subMode=None, defaultValue=None):
        '''Constructor.
        @param name: the name of the option, used for accessing, e.g. 'dirPattern'
        @param longName: the long option name, e.g. 'dir-pattern'. Usage: --dir-pattern=abc
        @param shortName: the short option name, e.g. 'p'. Usage: "-pabc" or "-p abc"
        @param description: the description of the option,  e.g. 'a regular expr describing the dirs to process'
        @param example: None or one or more examples of usage, 'PROG --dir-pattern=(home|opt)'
        @param dataType: 'string', 'int', 'bool', 'date', 'datetime', 'regexpr'
        @param mode: None or the mode @see UsageInfo
        @param subMode: None or the sub mode for @see UsageInfo
        @param defaultValue: if option is not given that value will be taken
        '''
        self._name = name
        self._longName = longName
        self._shortName = shortName
        self._description = description
        self._example = example
        self._dataType = dataType
        self._mode = mode
        self._subMode = subMode
        self._defaultValue = defaultValue
        self._value = defaultValue
        # an OptionProcessor instance:
        self._parent = None
        self._caseSensitive = True

    def check(self, value, isShort):
        '''Checks a current option.
        @param value: the current option value, e.g. '123'
        @param isShort: True: the option is called as short option
        @return: True: success False: error detected
        '''
        rc = True
        if self._dataType == 'int':
            self._value = base.StringUtils.asInt(value)
            if self._value is None:
                if value in (None, ''):
                    rc = self.error('missing int value', isShort)
                else:
                    rc = self.error('not an integer: ' + value, isShort)
        elif self._dataType == 'bool':
            value = value.lower() if value is not None else None
            if value in (None, ''):
                self._value = True
            elif value in ('true', 't'):
                self._value = True
            elif value in ('false', 'f'):
                self._value = False
            else:
                rc = self.error('not a bool value: ' + value, isShort)
        elif self._dataType == 'regexpr':
            rc = None
            try:
                self._value = re.compile(
                    value, base.Const.IGNORE_CASE if self._caseSensitive else 0)
            except Exception as exc:
                rc = self.error(str(exc), isShort)
        elif self._dataType == 'date':
            pass
        return rc

    def error(self, message, isShort):
        '''Logs an error.
        @param message: the error message
        @param isShort: True: the option is called as short option
        @return False
        '''
        msg = 'error on option {} [-{}{}]:\n{}\n{}+++ {}'.format(
            self._name,
            '' if isShort else '-',
            self._shortName if isShort else self._longName,
            base.StringUtils.indentLines(self._description, 1),
            '' if self._example is None else self._example + '\n',
            message)
        self._parent._logger.error(msg)
        return False


class OptionProcessor:
    '''Stores program options for automatic evaluation and usage building.
    '''

    def __init__(self, logger):
        '''Constructor.
        @param logger: the logger
        '''
        self._logger = logger
        self._list = []
        self._names = {}

    def add(self, option):
        '''Adds a single option to the list.
        '''
        if option._dataType not in ['bool', 'date', 'datetime', 'int', 'regexpr', 'string']:
            self._logger.error('unknown data type {} in option {}'.format(
                option._dataType, option._name))
        option._parent = self
        if option._name in self._names:
            self._logger.error(
                'option {} already defined'.format(option._name))
        else:
            for opt in self._list:
                if option._shortName is not None:
                    # a later defined shortname overwrites the previous
                    # definition:
                    if opt._shortName == option._shortName:
                        opt._shortName = None
                if option._longName == opt._longName:
                    self._logger.error('--{} in option {} is already defined in {}'.format(
                        option._longName, option._name, opt._name))
            self._names[option._name] = option
            self._list.append(option)
            if option._dataType == 'bool' and option._defaultValue is None:
                option._defaultValue = option._value = False
            elif option._dataType == 'int' and option._defaultValue is not None:
                option._defaultValue = option._value = base.StringUtils.asInt(
                    option._defaultValue)

    def checkLong(self, current):
        '''Checks a long name option.
        @param current: the option to check, e.g. 'dir-pattern=abc'
        @return True: success False: error recognized
        '''
        rc = False
        [name, sep, value] = current.partition('=')
        base.StringUtils.avoidWarning(sep)
        found = False
        for opt in self._list:
            if opt._longName == name:
                found = True
                rc = opt.check(value, False)
                break
        if not found:
            rc = self._logger.error('unknown option --' + current)
        return rc

    def checkShort(self, current):
        '''Checks a short name option.
        @param current: the option to check, e.g. 'd/home'
        @return True: success False: error recognized
        '''
        rc = False
        name = current[0]
        value = current[1:]
        found = False
        for opt in self._list:
            if opt._shortName == name:
                found = True
                rc = opt.check(value, True)
                break
        if not found:
            rc = self._logger.error('unknown option -' + current)
        return rc

    def optionByName(self, name):
        '''Returns the option given by name.
        @param name: the option name
        @return: None: not found otherwise: the option with the given name
        '''
        rc = self._names[name] if name in self._names else None
        return rc

    def scan(self, programOptions):
        '''Validates the current program options using the internal stored data.
        @param programOptions: a list of the current program options, e.g. ['-i', '--mode=full']
        @return True: success False: error occurred
        '''
        rc = True
        for option in programOptions:
            if option.startswith('--'):
                rc = rc and self.checkLong(option[2:])
            else:
                rc = rc and self.checkShort(option[1:])
        return rc


if __name__ == '__main__':
    pass
