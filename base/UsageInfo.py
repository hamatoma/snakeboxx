'''
Created: 2020.06.24
@license: CC0 https://creativecommons.org/publicdomain/zero/1.0
@author: hm
'''
import sys
import base.MemoryLogger


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
