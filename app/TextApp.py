#! /usr/bin/python3
'''
Created: 2020.06.24
@license: CC0 https://creativecommons.org/publicdomain/zero/1.0
@author: hm
'''
import sys
import os
import re
import snakeboxx

import base.CsvProcessor
import base.TextProcessor
import base.DirTraverser
import app.BaseApp


class OptionsExecuteRules:
    '''Options for the mode execute-rules.
    '''

    def __init__(self):
        '''Constructor.
        '''
        self.maxLoop = 1
        self.backup = None


class OptionsGrep:
    '''Options for the mode grep
    '''

    def __init__(self):
        '''Constructor.
        '''
        self.wordOnly = False
        self.group = None
        self.lineNumber = False
        self.ignoreCase = False
        self.invertMatch = False
        self.formatFile = None
        self.formatLine = None
        self.belowContext = None
        self.aboveContext = None
        self.belowChars = None
        self.aboveChars = None


class OptionsInsertOrReplace:
    '''Options for the mode insert-or-replace
    '''

    def __init__(self):
        '''Constructor.
        '''
        self.ignoreCase = False
        self.anchor = None
        self.above = False
        self.backup = None


class OptionsReplace:
    '''Options for the mode replace
    '''

    def __init__(self):
        '''Constructor.
        '''
        self.ignoreCase = False
        self.backupExtensions = None
        self.prefixBackref = None
        self.wordOnly = None
        self.rawString = False
        self.escActive = False


class TextApp(app.BaseApp.BaseApp):
    '''Performs some tasks with text files: searching, modification...
    '''

    def __init__(self, args):
        '''Constructor.
        @param args: the program arguments, e.g. ['test', 'a@bc.de']
        '''
        app.BaseApp.BaseApp.__init__(self, 'TextApp', args, None, 'textboxx')
        self._processor = None
        self._traverser = None
        self._hostname = None

    def buildConfig(self):
        '''Creates an useful configuration example.
        '''
        content = '''# created by TextApp
logfile=/var/log/local/textboxx.log
'''
        self.buildStandardConfig(content)

    def buildUsage(self):
        '''Builds the usage message.
        '''
        self._usageInfo.appendDescription('''APP-NAME <global-opts> <mode> [<opts>]
 Searching and modifying in text files.
''')
        self._usageInfo.addMode('describe-rules', '''describe-rules
 Describes the syntax and the meaning of the rules
 ''', '''APP-NAME describe-rules
''')
        self._usageInfo.addMode('exec-rules', '''exec-rules <rules> <file-pattern> [<opts>]
 Executes the given <rules> which allows to show some parts of or modify the given the files.
 <rules>: a string describing the actions to do. call "APP-NAME describe-rules" for more info
 ''', '''APP-NAME exec-rules ">/hello/" "*.txt" --recursive --min-depth=1 --files-only
''')
        self._usageInfo.addMode('csv-execute', '''csv-execute <commands> <file-pattern>
 Does some operations on a Comma Separated File. More info with csv-describe.
 <file-pattern>: specifies the file(s) to process.
''', '''APP-NAME csv-info "address.csv" --sorted --unique --index=3,4 --cols=*name*,*city*
''')
        self._usageInfo.addMode('grep', '''grep <reg-expr> <file-pattern> <opts>
 Searches the regular expression in files.
 <file-pattern>: specifies the file(s) to process.
''', r'''APP-NAME grep -n -g1 'Date:\s+(\d{4}\.\d\d\.\d\d)' "*.txt" --exclude-dirs=.git --max-depth=2
APP-NAME grep "[\w.+-]+@[\w.+-]+" "*.addr" --format-file="=== EMail addresses in file %f:" --format-line=%l:%T%t *.addr
''')

        self._usageInfo.addMode('insert-or-replace', '''insert-or-replace <key> <line> <file-pattern> <opts>
 Searches <key>. If found this line is replaced by <line>.
 If not found and option --anchor is given: <line> is inserted at this position.
 <key>: the regular expression to identify the line to replace
 <line>: the line to replace or insert
 <file-pattern>: specifies the file(s) to process.
''', r'''APP-NAME insert-or-replace '^\s*memory_limit\s*=' "memory_limit=2048M" "/etc/php/7.3/fmt/php.ini" -aphp.net/memory-limit
''')

        self._usageInfo.addMode('replace', r'''replace <pattern> <replacement> <file-pattern> <opts>
 Searches the regular expression in files.
 <pattern>: the pattern to search, a regular expression only if --not-regexpr
 <replacement>: the <reg-expr> will be replaced by this string. Can contain backreferences: see --prefix-backref
 <file-pattern>:
  file name pattern, with wilcards *, ? [chars] and [!not chars].
''', r'''APP-NAME replace "version: ([\d+.]+)" "V%1" "*.py" --prefix-backref=% -B.bak
''')

        self._usageInfo.addMode('replace-many', r'''replace-many <data-file> <file-pattern> <opts>
 Searches the regular expression in <input> and print the processed (replaced) string.
 This is useful for complex scripts.
 <data-file>: a text file with lines "<string>TAB<replacement>"
 <file-pattern>:
  file name pattern, with wilcards *, ? [chars] and [!not chars].
''', r'''APP-NAME replace-many changes.txt *.html --file-type=fl --max-size=100ki
''')

        self._usageInfo.addMode('replace-string', r'''replace <pattern> <replacement> <input> <opts>
 Searches the regular expression in <input> and print the processed (replaced) string.
 This is useful for complex scripts.
 <pattern>: the pattern to search, a regular expression only if --not-regexpr
 <replacement>: the <reg-expr> will be replaced by this string. Can contain backreferences: see --prefix-backref
 <input>:
  this string will be processed
''', r'''APP-NAME replace-string "(files|dirs): (\d+)" "%2 %1" "files: 4 dirs: 9" --prefix-backref=%
''')

    def buildUsageOptions(self, mode=None):
        '''Adds the options for a given mode.
        @param mode: None or the mode for which the option is added
        '''
        def add(mode, opt):
            self._usageInfo.addModeOption(mode, opt)

        def addIgnore(mode):
            add(mode, base.UsageInfo.Option('ignore-case', 'i',
                                            'ignore case while searching', 'bool'))

        def addIgnoreAndWord(mode):
            addIgnore(mode)
            add(mode, base.UsageInfo.Option('word-regexpr', 'w',
                                            'only whole words will be found', 'bool'))

        def addBackup(mode):
            add(mode, base.UsageInfo.Option('backup', 'B',
                                            '''if <item> is starting with ".": the origin file will be renamed with this extension
if <item> is a directory: the original file is moved to this directory
if not given no backup is done: the original file is modified'''))

        def addEsc(mode):
            add(mode, base.UsageInfo.Option('esc-active', 'e',
                                            r"esc sequences '\n', '\r', \t', '\xXX', '\uXXXX' and '\Uxxxxxxxx' "
                                            + 'in replacement will be recognized', 'bool'))

        def addPrefixBackticks(mode):
            add(mode, base.UsageInfo.Option('prefix-backref', 'b',
                                            r'''if given <prefix><group> will be replaced by the group
example: opt: -b% reg-expr: "version: ([\d+.]+)" replacement: "V%1" string: "version: 4.7" result: "V4.7"'''))

        def addRawString(mode):
            add(mode, base.UsageInfo.Option('raw-string', 'R',
                                            '<pattern> is a string, not a regular expression', 'bool'))

        def addReplace(mode, changeFile):
            addIgnoreAndWord(mode)
            addEsc(mode)
            addPrefixBackticks(mode)
            addRawString(mode)
            if (changeFile):
                addBackup(mode)

        if mode is None:
            mode = self._mainMode
        if mode == 'describe-rules':
            pass
        elif mode == 'exec-rules':
            base.DirTraverser.addOptions(mode, self._usageInfo)
            addBackup(mode)
            add(mode, base.UsageInfo.Option('max-loops', 'l',
                                            'the process is stopped after <max-loop>*<source_lines> statements', 'int', 1))
        elif mode == 'csv-execute':
            base.DirTraverser.addOptions(mode, self._usageInfo)
        elif mode == 'grep':
            base.DirTraverser.addOptions(mode, self._usageInfo)
            addIgnoreAndWord(mode)
            add(mode, base.UsageInfo.Option('above-chars', 'a',
                                            'displays <int> characters above the hit. Sets implicitly --only-matching', 'int'))
            add(mode, base.UsageInfo.Option('below-chars', 'b',
                                            'displays <int> characters below the hit. Sets implicitly --only-matching', 'int'))
            add(mode, base.UsageInfo.Option('above-context', 'A',
                                            'displays <int> lines above the hit', 'int'))
            add(mode, base.UsageInfo.Option('below-context', 'B',
                                            'displays <int> lines below the hit', 'int'))
            add(mode, base.UsageInfo.Option('context', 'C',
                                            'displays <int> lines above and below the hit', 'int'))
            add(mode, base.UsageInfo.Option('format-line', 'f',
                                            '''defines the display format of a hit line.
Placeholders: %f: full filename %p: path %n: node %# line number
%t: line text %<N>: group N (N in [0..9] %%: '%' %L: newline %T: tabulator'''))
            add(mode, base.UsageInfo.Option('format-file', 'F',
                                            '''defines the display format of the prefix of a file with hits.
Placeholders: %f: full filename %p: path %n: node %%: '%' %L: newline %T: tabulator'''))
            add(mode, base.UsageInfo.Option('group', 'g',
                                            'displays only the <int>-th group of the regular expression', 'int'))
            add(mode, base.UsageInfo.Option('line-number', 'n',
                                            'the line number will be displayed for each hit', 'bool'))
            add(mode, base.UsageInfo.Option('only-matching', 'o',
                                            'only the matching part of the line will be displayed (not the whole line)', 'bool'))
            add(mode, base.UsageInfo.Option('invert-match', 'v',
                                            'all lines not containing the search expression is displayed', 'bool'))
        elif mode == 'insert-or-replace':
            base.DirTraverser.addOptions(mode, self._usageInfo)
            addIgnore(mode)
            add(mode, base.UsageInfo.Option('above', 'A',
                                            'the insertion point is above the anchor', 'bool'))
            add(mode, base.UsageInfo.Option('anchor', 'a',
                                            'defines the insertion position if <key> is not found'))
            addBackup(mode)
        elif mode == 'replace':
            base.DirTraverser.addOptions(mode, self._usageInfo)
            addReplace(mode, True)
        elif mode == 'replace-many':
            base.DirTraverser.addOptions(mode, self._usageInfo)
            addReplace(mode, True)
        elif mode == 'replace-string':
            addReplace(mode, False)

    def csvExecute(self):
        '''Executes a sequence of commands on CSV files.
        '''
        commands = self.shiftProgramArgument()
        pattern = self.shiftProgramArgument()
        wrong = self.shiftProgramArgument()
        if wrong is not None:
            self.abort('too many arguments: ' + wrong)
        elif pattern is None:
            self.abort('too few arguments')
        elif self.handleOptions():
            self._processor = base.CsvProcessor.CsvProcessor(self._logger)
            self._traverser = base.DirTraverser.buildFromOptions(
                pattern, self._usageInfo, 'csv-execute')
            self._traverser._findFiles = self._traverser._findLinks = True
            self._traverser._findDirs = False
            for filename in self._traverser.next(self._traverser._directory, 0):
                self._processor.readFile(filename)
                self._processor.execute(commands)

    def describeRules(self):
        '''Displays the description of the rules.
        '''
        item = base.SearchRuleList.SearchRuleList(self._logger)
        item.describe()

    def execRules(self):
        '''Executes a sequence of rules on specified files.
        '''
        rules = self.shiftProgramArgument()
        pattern = self.shiftProgramArgument()
        wrong = self.shiftProgramArgument()
        if wrong is not None:
            self.abort('too many arguments')
        elif pattern is None:
            self.abort('missing <file-pattern>')
        elif self.handleOptions():
            self._processor = base.TextProcessor.TextProcessor(self._logger)
            options = OptionsExecuteRules()
            options.backup = self._optionProcessor.valueOf('backup')
            options.maxLoop = self._optionProcessor.valueOf('max-loops')
            self._traverser = base.DirTraverser.buildFromOptions(
                pattern, self._usageInfo, 'exec-rules')
            self._traverser._findFiles = self._traverser._findLinks = True
            self._traverser._findDirs = False
            for filename in self._traverser.next(self._traverser._directory, 0):
                base.StringUtils.avoidWarning(filename)
                self.execRulesOneFile(rules, options)

    def execRulesOneFile(self, rules, options):
        '''Executes rules for one file.
        @param filename: file to process
        @param rules: the rules to execute
        @param options: the program options (instance of OptionsExecuteRules)
        '''
        self._processor.readFile(self._traverser._fileFullName)
        self._processor.executeRules(rules, options.maxLoop)
        if self._processor._hasChanged:
            self._processor.writeFile(None, options.backup)

    def grep(self):
        '''Searches regular expressions in files.
        '''
        self._resultLines = []
        what = self.shiftProgramArgument()
        pattern = self.shiftProgramArgument()
        if pattern is None:
            self.abort('too few arguments')
        elif self.handleOptions():
            options = self.grepOptions()
            if options.wordOnly:
                what = r'\b' + what + r'\b'
            regExpr = re.compile(
                what, base.Const.IGNORE_CASE if options.ignoreCase else 0)
            self._traverser = base.DirTraverser.buildFromOptions(
                pattern, self._usageInfo, 'grep')
            self._traverser._findFiles = self._traverser._findLinks = True
            self._traverser._findDirs = False
            for filename in self._traverser.next(self._traverser._directory, 0):
                if not self.grepOneFile(filename, regExpr, options):
                    break

    @staticmethod
    def grepFormat(theFormat, filename, text, lineNo, matcher):
        '''Returns a format with expanded placeholders.
        @param format: the format string with placeholders, e.g. '%f-%#: %t'
        @param filename: [full, path, node], e.g. ['/etc/password', '/etc/', 'password']
        @param text: None or the line text with the hit
        @param lineNo: None or the line number
        @param matcher: None or the match object of the hit
        @return: the format with expanded placeholders, e.g. '/etc/password-12:sync:x:4:65534:sync:/bin:/bin/sync'
        '''
        last = 0
        rc = ''
        lengthFormat = len(theFormat)
        while True:
            position = theFormat.find('%', last)
            if position > 0:
                rc += theFormat[last:position]
            if position < 0:
                rc += theFormat[last:]
                break
            if position == lengthFormat - 1:
                rc += '%'
                break
            variable = theFormat[position + 1]
            if variable == 'f':
                rc += filename[0]
            elif variable == 'p':
                rc += filename[1]
            elif variable == 'n':
                rc += filename[2]
            elif variable == 'T':
                rc += '\t'
            elif variable == 'L':
                rc += '\n'
            elif variable == '%':
                rc += '%'
            elif variable == 't':
                if text is not None:
                    rc += text
            elif variable == '#':
                rc += str(lineNo)
            elif '0' <= variable <= '9':
                group = ord(variable) - ord('0')
                if matcher is not None:
                    if matcher.lastindex is None:
                        rc += matcher.group(0)
                    elif matcher.lastindex <= group:
                        rc += matcher.group(group)
            last = position + 2
        return rc

    def grepOneFile(self, filename, regExpr, options):
        '''Searches the regular expression in one file.
        @param filename: the name of the file to inspect
        @param regExpr: the regular expression to search
        @param options: the program options a OptionsGrep instance
        '''
        def output(line):
            if self._logger._verboseLevel > 0:
                self._resultLines.append(line)
            print(line)

        def outputContext(theFormat, fileNames, start, end, lines):
            while start < end:
                line2 = TextApp.grepFormat(
                    theFormat, fileNames, lines[start], start + 1, None)
                output(line2)
                start += 1
            return end - 1
        lines = base.StringUtils.fromFile(filename, '\n')
        nameList = [filename, os.path.dirname(
            filename), os.path.basename(filename)]
        first = True
        lastIx = -1
        missingInterval = [None, None]
        for ix, line in enumerate(lines):
            matcher = regExpr.search(line)
            if matcher and first and options.formatFile is not None:
                output(TextApp.grepFormat(
                    options.formatFile, nameList, None, None, None))
                first = False
            if matcher and not options.invertMatch or matcher is None and options.invertMatch:
                if missingInterval[0] is not None:
                    ix2 = min(ix, missingInterval[1])
                    lastIx = outputContext(
                        options.formatLine, nameList, missingInterval[0], ix2, lines)
                    missingInterval[0] = None
                if options.aboveContext is not None:
                    start = max(0, lastIx + 1, ix - options.aboveContext)
                    if start < ix:
                        lastIx = outputContext(
                            options.formatLine, nameList, start, ix, lines)
                if options.group is None:
                    output(TextApp.grepFormat(options.formatLine,
                                              nameList, line, ix + 1, matcher))
                else:
                    self.grepOneLine(options, nameList, line, ix + 1, regExpr)
                lastIx = ix
                if options.belowContext is not None:
                    missingInterval = [ix + 1, ix + 1 + options.belowContext]
        if missingInterval[0] is not None:
            lastIx = min(len(lines), missingInterval[1])
            outputContext(options.formatLine, nameList,
                          missingInterval[0], lastIx, lines)

    def grepOneLine(self, options, nameList, line, lineNo, regExpr):
        '''Handles the multiple hits in one line.
        @precondition: only the matching pattern should be displayed (not the whole line).
        @param options: the program options
        @param namelist: variants of the filename: [<full>, <path>, <node>]
        @param line: the line to inspect
        @param lineNo: the line number of line
        @param regExpr: the regular expression to search
        '''
        lineLength = len(line)
        for matcher in regExpr.finditer(line):
            start, end = matcher.span(options.group)
            if options.aboveChars is not None:
                start = max(0, start - options.aboveChars)
            if options.belowChars is not None:
                end = min(lineLength, end + options.belowChars)
            info = line[start:end]
            info2 = TextApp.grepFormat(
                options.formatLine, nameList, info, lineNo, matcher)
            if self._logger._verboseLevel > 0:
                self._resultLines.append(info2)
            print(info2)

    def grepOptions(self):
        '''Evaluates the grep options.
        @return: the options stored in a OptionsGrep instance
        '''
        options = OptionsGrep()
        options.ignoreCase = self._optionProcessor.valueOf('ignore-case')
        options.wordOnly = self._optionProcessor.valueOf('word-regexpr')
        if self._optionProcessor.valueOf('group') is not None:
            options.group = self._optionProcessor.valueOf('group')
        elif self._optionProcessor.valueOf('only-matching'):
            options.group = 0
        options.lineNumber = self._optionProcessor.valueOf('line-number')
        options.invertMatch = self._optionProcessor.valueOf('invert-match')
        options.formatFile = self._optionProcessor.valueOf('format-file')
        options.formatLine = self._optionProcessor.valueOf('format-line')
        #if options.formatLine is None:
        #    info = '%t' if options.group is None else f'%{options.group}'
        #    options.formatLine = f'%f-%#:{info}' if options.lineNumber else f'%f:{info}'
        options.belowContext = self._optionProcessor.valueOf(
            'below-context')
        options.aboveContext = self._optionProcessor.valueOf(
            'above-context')
        if options.belowContext is None and options.aboveContext is None:
            options.belowContext = options.aboveContext = options.aboveContext = self._optionProcessor.valueOf(
                'context')
        options.belowChars = self._optionProcessor.valueOf('below-chars')
        options.aboveChars = self._optionProcessor.valueOf('above-chars')
        if (options.belowChars is not None or options.aboveChars is not None) and options.group is None:
            options.group = 0 
        if options.formatLine is None:
            info = '%t' if options.group is None else f'%{options.group}'
            options.formatLine = f'%f-%#:{info}' if options.lineNumber else f'%f:{info}'
        return options

    def insertOrReplace(self):
        '''Searches regular expressions in files.
        '''
        self._resultLines = []
        key = self.shiftProgramArgument()
        line = self.shiftProgramArgument()
        pattern = self.shiftProgramArgument()
        if pattern is None:
            self.abort('too few arguments')
        elif self.handleOptions():
            options = OptionsInsertOrReplace()
            options.ignoreCase = self._optionProcessor.valueOf('ignore-case')
            options.anchor = self._optionProcessor.valueOf('anchor')
            options.above = self._optionProcessor.valueOf('above')
            options.backup = self._optionProcessor.valueOf('backup')
            if options.ignoreCase and options.anchor is not None:
                options.anchor = re.compile(
                    options.anchor.pattern, base.Const.IGNORE_CASE)
            self._traverser = base.DirTraverser.buildFromOptions(
                pattern, self._usageInfo, 'insert-or-replace')
            self._processor = base.TextProcessor.TextProcessor(self._logger)
            self._traverser._findFiles = self._traverser._findLinks = True
            self._traverser._findDirs = False
            for filename in self._traverser.next(self._traverser._directory, 0):
                self._processor.readFile(filename)
                self._processor.insertOrReplace(
                    key, line, options.anchor, options.above)
                if self._processor._hasChanged:
                    self._processor.writeFile(filename, options.backup)

    def replace(self):
        '''Replaces a regular expression in files by a replacement.
        '''
        self._resultLines = []
        what = self.shiftProgramArgument()
        replacement = self.shiftProgramArgument()
        pattern = self.shiftProgramArgument()
        if pattern is None:
            self.abort('too few arguments')
        elif self.handleOptions():
            self._processor = base.TextProcessor.TextProcessor(self._logger)
            options = self.replaceOptions(True)
            if options is not None:
                self._traverser = base.DirTraverser.buildFromOptions(
                    pattern, self._usageInfo, 'replace')
                self._traverser._findFiles = self._traverser._findLinks = True
                self._traverser._findDirs = False
                for filename in self._traverser.next(self._traverser._directory, 0):
                    self._processor.readFile(filename)
                    hits = self._processor.replace(what, replacement, options.prefixBackref,
                                                   options.rawString, True, options.wordOnly, options.ignoreCase,
                                                   options.escActive)
                    if hits > 0:
                        self._processor.writeFile(
                            filename, options.backupExtensions)

    def replaceMany(self):
        '''Replaces strings by replacements given in a file in files.
        '''
        self._resultLines = []
        dataFile = self.shiftProgramArgument()
        pattern = self.shiftProgramArgument()
        if pattern is None:
            self.abort('too few arguments')
        elif not os.path.exists(dataFile):
            self.abort('data file does not exists: ' + dataFile)
        elif self.handleOptions():
            what = []
            replacements = []
            lines = base.StringUtils.fromFile(dataFile, '\n')
            for line in lines:
                parts = line.split('\t')
                if len(parts) == 2:
                    what.append(parts[0])
                    replacements.append(parts[1])
            self._processor = base.TextProcessor.TextProcessor(self._logger)
            options = self.replaceOptions(True)
            if options is not None:
                self._traverser = base.DirTraverser.buildFromOptions(
                    pattern, self._usageInfo, 'replace-many')
                self._traverser._findFiles = self._traverser._findLinks = True
                self._traverser._findDirs = False
                for filename in self._traverser.next(self._traverser._directory, 0):
                    self._processor.readFile(filename)
                    hits = self._processor.replaceMany(what, replacements)
                    if hits > 0:
                        self._processor.writeFile(
                            filename, options.backupExtensions)

    def replaceOptions(self, fileOptions):
        '''Evaluates the options for the mode "replace", "replace-string" and "replace-many".
        @param fileOptions: the mode is "replace" or "replace-many": operates on files
        @return: None: error occurred otherwise: the OptionsReplace instance
        '''
        options = OptionsReplace()
        options.ignoreCase = self._optionProcessor.valueOf('ignore-case')
        options.wordOnly = self._optionProcessor.valueOf('word-regexpr')
        options.prefixBackref = self._optionProcessor.valueOf('prefix-backref')
        options.rawString = self._optionProcessor.valueOf('raw-string')
        options.escActive = self._optionProcessor.valueOf('esc-active')
        if fileOptions:
            options.backupExtensions = self._optionProcessor.valueOf('backup')
        if options.prefixBackref is not None and len(options.prefixBackref) != 1:
            self.argumentError(
                'prefix-backref must have length 1, not ' + options.prefixBackref)
            options = None
        return options

    def replaceString(self):
        '''Replaces a regular expression in a given string by a replacement and display it.
        '''
        self._resultLines = []
        what = self.shiftProgramArgument()
        replacement = self.shiftProgramArgument()
        inputString = self.shiftProgramArgument()
        if inputString is None:
            self.abort('too few arguments')
        elif self.handleOptions():
            self._processor = base.TextProcessor.TextProcessor(self._logger)
            options = self.replaceOptions(False)
            if options is not None:
                self._processor.setContent(inputString)
                self._processor.replace(what, replacement, options.prefixBackref,
                                        options.rawString, True, options.wordOnly, options.ignoreCase, options.escActive)
                info = '\n'.join(self._processor._lines)
                self._resultText = info
                print(info)

    def run(self):
        '''Implements the tasks of the application
        '''
        self._hostname = self._configuration.getString('hostname', '<host>')
        if self._mainMode == 'exec-rules':
            self.execRules()
        elif self._mainMode == 'describe-rules':
            self.describeRules()
        elif self._mainMode == 'csv-execute':
            self.csvExecute()
        elif self._mainMode == 'csv-describe':
            base.CsvProcessor.CsvProcessor.describe()
        elif self._mainMode == 'grep':
            self.grep()
        elif self._mainMode == 'replace':
            self.replace()
        elif self._mainMode == 'replace-many':
            self.replaceMany()
        elif self._mainMode == 'replace-string':
            self.replaceString()
        elif self._mainMode == 'insert-or-replace':
            self.insertOrReplace()
        else:
            self.abort('unknown mode: ' + self._mainMode)


def main(args):
    '''Main function.
    @param args: the program arguments
    '''
    snakeboxx.startApplication()
    application = TextApp(args)
    application.main()


if __name__ == '__main__':
    main(sys.argv[1:])
