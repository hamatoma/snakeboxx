'''
Created: 2020.06.24
@license: CC0 https://creativecommons.org/publicdomain/zero/1.0
@author: hm
'''
import sys
import re
import base.MemoryLogger


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
            except re.error as exc:
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


class UsageInfo:
    '''Simplicates the building of large usage information.
    '''

    def __init__(self, logger, separatorMode='<mode>:', indentStep=2):
        '''Constructor.
        @param logger: the logger
        @param separatorMode: a text which will be put between global options and modes
        @param indentStep: the width of one indent level
        '''
        self._singleIndent = ' ' * indentStep
        self._logger = logger
        self._separatorMode = separatorMode
        self._description = ''
        self._descriptions = {}
        self._examples = {}
        self._nested = {}
        self._optionProcessors = {}

    def addMode(self, mode, description, example=None):
        '''Adds an entry to the usage info.
        @param mode: the mode
        @param description: description of the mode
        @param example: None or an example of the mode
        '''
        if mode in self._descriptions:
            self._logger.error('mode {} already exists'.format(mode))
        else:
            self._descriptions[mode] = description.rstrip()
            self._examples[mode] = '' if example is None else example.rstrip()
            self._optionProcessors[mode] = OptionProcessor(self._logger)

    def addModeOption(self, mode, option):
        '''Adds an option related to the mode.
        @param mode: the mode
        @param option: an Option instance
        '''
        self._optionProcessors[mode].add(option)

    def addSubMode(self, mode, subMode, description, example):
        '''Adds an submode entry to the usage info.
        @param mode: the mode
        @param subMode: the subMode beloging to the mode
        @param description: description of the sub mode
        @param example: None or an example of the sub mode
        '''
        if mode not in self._nested:
            self._logger.error(
                'missing UsageInfo for {}: Is it initialized?'.format(mode))
        elif subMode in self._descriptions:
            self._logger.error(
                'sub mode {} already exists in {}'.format(subMode, mode))
        else:
            subModeInfo = self._nested[mode]
            subModeInfo._descriptions[subMode] = description.rstrip()
            subModeInfo._examples[subMode] = '' if example is None else example

    def appendDescription(self, description):
        '''Appends a string to the description.
        @param description: the string to append
        '''
        if self._description == '':
            self._description = description.rstrip()
        else:
            self._description += "\n" + description.rstrip()

    def asString(self, pattern, indent, pattern2=''):
        '''Assembles the usage message depending on pattern and pattern2.
        @param pattern: only modes that matching this pattern will be assembled
        @param indent: the indentition level of the output
        @param pattern2: only sub modes that matching this pattern will be assembled
        '''
        rc = ''
        modes = []
        subModes = []
        rawPattern = pattern[1:] if pattern.startswith('=') else pattern
        mode = None
        if pattern == '' and pattern2 == '':
            modes = [x for x in self._descriptions] + [x for x in self._nested]
            #self._descriptions.keys() + self._nested.keys()
        elif pattern2 == '':
            # collect the modes:
            self.hasPattern(pattern, modes)
            for mode in self._nested:
                subModes2 = self._nested.keys()
                modes.append(mode)
                subModes2.sort()
                subModes[mode] = subModes2
        else:
            for mode in self._nested:
                modes2 = []
                if mode.find(rawPattern) >= 0 or self._nested[mode].hasPattern(pattern2, modes2):
                    modes2.sort()
                    subModes[mode] = modes2
                    modes.append(mode)
        if mode == '':
            modes = self._descriptions.keys() + self._nested.keys()
        modes.sort()
        rc += self.indent(0, self._description)
        separatedFound = False
        for mode in modes:
            if not separatedFound and not mode.startswith('<'):
                separatedFound = True
                rc += self.indent(0, self._separatorMode)
            if mode in self._descriptions:
                rc += self.indent(indent + 1, self._descriptions[mode])
            else:
                usage2 = self._nested[mode]
                rc += self.indent(indent + 1, usage2._description)
                array1 = self._nested[mode]._descriptions.keys(
                ) if pattern == '' else subModes[mode]
                rc += self.indent(indent + 2, usage2._separatorMode)
                for subMode in array1:
                    rc += self.indent(indent + 2,
                                      usage2._descriptions[subMode])
        rc += 'Examples:\n'
        for mode in modes:
            if mode in self._examples:
                rc += self.indent(0, self._examples[mode])
            else:
                usage2 = self._nested[mode]
                array1 = array1 = self._nested[mode]._descriptions.keys(
                ) if pattern == '' else subModes[mode]
                for subMode in array1:
                    rc += self.indent(0, usage2._examples[subMode])
        return rc

    def hasPattern(self, pattern, modes):
        '''Returns whether a mode or its description matches the [pattern].
        Side effect: modes
        @param pattern: the pattern to search
        @param modes: OUT: the list of the modes matching the pattern
        '''
        rc = False
        testModeOnly = False
        if pattern.startswith('='):
            pattern = pattern[1:]
            testModeOnly = True
        for mode in self._descriptions:
            if pattern == '' or not testModeOnly and (self._descriptions[mode].find(pattern) > 0
                                                      or self._examples[mode].find(pattern) > 0):
                modes.append(mode)
                rc = True
        for mode in self._nested:
            if pattern == '' or not testModeOnly and self._nested[mode].find(pattern) > 0:
                modes.append(mode)
                rc = True
        return rc

    def indent(self, indent, lines):
        '''Formats a list of lines (given as one string) to a given indent.
        @param indent: the indention level
        @param lines: None or the text to process, e.g. 'doit\n does the thing'
        @return the lines with the given indention level as a string, e.g. ' doit\n  does the thing'
        '''
        rc = ''
        prefix = self._singleIndent * indent
        if lines is not None:
            for line in lines.rstrip().split('\n'):
                line2 = line.lstrip()
                level = len(line) - len(line2)
                rc += prefix + self._singleIndent * level + line2 + '\n'
        return rc

    def initializeSubModes(self, mode, description=None):
        '''Prepares the instance for sub modes for a given mode.
        @param mode: the mode associated to the submode
        @param description: None or the description of the mode
        '''
        if mode in self._nested:
            self._logger.error(
                'mode {} already initialized (submodes)'.format(mode))
        else:
            self._nested[mode] = UsageInfo(self._logger, '<what>:')
            self._nested[mode]._description = '' if description is None else description

    def replaceInDescription(self, placeholder, replacement):
        '''Replaces a placeholder with a replacement in the description.
        @param placeholder: the string to replace
        @param replacement: the replacement
        '''
        self._description = self._description.replace(placeholder, replacement)

    def replaceMacro(self, placeholder, replacement):
        '''Replaces a placeholder with a replacement in descriptions and examples.
        @param placeholder: the string to replace
        @param replacement: the replacement
        '''
        self.replaceInDescription(placeholder, replacement)
        for mode in self._descriptions:
            self._descriptions[mode] = self._descriptions[mode].replace(
                placeholder, replacement)
            if self._examples[mode] is not None:
                self._examples[mode] = self._examples[mode].replace(
                    placeholder, replacement)


def main(argv):
    '''Main function.
    '''
    base.StringUtils.avoidWarning(argv)
    logger = base.MemoryLogger.MemoryLogger()
    info = UsageInfo(logger)
    info.addMode('help', '''help <pattern>
 display a help message
  <pattern>: only matching modes will be displayed
 ''', 'APP-NAME help')
    print(info.asString('help', 1))


if __name__ == '__main__':
    main(sys.argv)
