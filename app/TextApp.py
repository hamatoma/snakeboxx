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
import base.FileHelper
import app.BaseApp


class OptionsExecuteRules:
    '''Options for the mode execute-rules.
    '''
    def __init__(self):
        self.maxLoop = 1
        self.aboveFilename = False
        self.inPlace = None
        self.outPattern = None

class OptionsGrep:
    '''Options for the mode grep
    '''
    def __init__(self):
        self.wordOnly = False
        self.group = None
        self.lineNumber = False
        self.ignoreCase = False
        self.invertMatch = False
        self.formatFile = None
        self.formatLine = None
        self.afterContext = None
        self.beforeContext = None
        self.formatFile = None
        self.formatLine = None
        self.afterChars = None
        self.beforeChars = None

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
 <opt>:
  all options of the DirTraverser are allowed.
 ''', '''APP-NAME csv-info "address.csv" --sorted --unique --index=3,4 --cols=*name*,*city*
''')
        self._usageInfo.addMode('grep', '''grep <reg-expr> <file-pattern> <opts>
 Searches the regular expression in files.
 <file-pattern>: specifies the file(s) to process.
 <opt>:
  all options of the DirTraverser are allowed.
  -a<count> or --after-chars=<count>
   displays <count> characters after the pattern. Sets implicitly --only-matching
  -A<count> or --after-context=<count>
   the <count> lines after the hit will be displayed
  -b<count> or --before-chars=<count>
   displays <count> characters before the pattern. Sets implicitly --only-matching
  -B<count> or --before-context=<count>
   the <count> lines after the hit will be displayed
  -C<count> or --context=<count>
   the <count> lines before and after the hit will be displayed
  -f<format> or --format-line=<format>
   defines the display format of a hit line.
   Placeholders: %f: full filename %p: path %n: node %# line number %t: line text %<N>: group N (N in [0..9] %%: '%' %L: newline %T: tabulator
  -F<format> or --format-file=<format>
   defines the display format of the prefix of a file with hits.
   Placeholders: %f: full filename %p: path %n: node %%: '%' %L: newline %T: tabulator
  -i or --ignore-case
   the search is case insensitive
  -g<N> or --group=<N>
   displays only the N-th group of the regular expression
  -n or --line-number
   the line number will be displayed
  -o or --only-matching
   only the matching part of the line will be displayed (not the whole line)
  -v or --invert-match
   all lines not containing the search expression is listed
  -w or --word-regexpr
   only whole words will be found
''', r'''APP-NAME grep -n -g1 'Date:\s+(\d{4}\.\d\d\.\d\d)' "*.txt" --exclude-dirs=.git
''')

    def csvExecute(self):
        '''Executes a sequence of commands on CSV files.
        '''
        commands = self.shiftProgramArgument()
        pattern = self.shiftProgramArgument()
        wrong = self.shiftProgramArgument()
        if wrong is not None:
            self.abort('too many arguments: ' + wrong)
        elif pattern is None:
            self.abort('missing <file-pattern>')
        else:
            self._processor = base.CsvProcessor.CsvProcessor(self._logger)
            errors = []
            self._traverser = base.DirTraverser.fromOptions(
                pattern, self._programOptions, errors)
            if errors:
                for error in errors:
                    self._logger.error(error)
            else:
                self._traverser._findFiles = self._traverser._findLinks = True
                self._traverser._findDirs = False
                for filename in self._traverser.next(self._traverser._directory, 0):
                    self._processor.readFile(filename)
                    self._processor.execute(commands)

    def describeRules(self):
        '''Displays the description of the rules.
        '''
        item = base.TextProcessor.RuleList(self._logger)
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
        else:
            self._processor = base.TextProcessor.TextProcessor(self._logger)
            options = self.execRulesOptions()
            errors = []
            self._traverser = base.DirTraverser.fromOptions(
                pattern, self._programOptions, errors)
            if errors:
                for error in errors:
                    self._logger.error(error)
            else:
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
        self._processor.executeRules(rules)
        if self._processor._hasChanged:
            if options.inPlace is not None:
                if options.inPlace != '':
                    src = self._traverser._fileFullName
                    parts = base.FileHelper.splitFilename(src)
                    parts['ext'] = options.inPlace
                    trg = ''.join(parts)
                    if os.path.exists(trg):
                        os.unlink(trg)
                    os.rename(src, trg)
                self._processor.writeFile()

    def execRulesOptions(self):
        '''Analyses the options of the mode exec-rules.
        @return: an instance of OptionsExecuteRules
        '''
        options = OptionsExecuteRules()
        toDelete = []
        for ix, option in enumerate(self._programOptions):
            boolValue = base.StringUtils.boolOption(
                'above-filename', 'a', option)
            if boolValue is not None:
                toDelete.append(ix)
                options.aboveFilename = boolValue
                continue
            strValue = base.StringUtils.stringOption('in-place', 'i', option)
            if strValue is not None:
                toDelete.append(ix)
                options.inPlace = strValue
                continue
            intValue = base.StringUtils.intOption('max-loop', 'l', option)
            if intValue is not None:
                toDelete.append(ix)
                options.maxLoop = intValue
                continue
        toDelete.reverse()
        for ix in toDelete:
            del self._programOptions[ix]
        return options

    def grep(self):
        '''Searches regular expressions in files.
        '''
        self._resultLines = []
        what = self.shiftProgramArgument()
        pattern = self.shiftProgramArgument()
        if pattern is None:
            self.abort('missing <file-pattern>')
        else:
            options = self.grepOptions()
            if options.wordOnly:
                what = r'\b' + what + r'\b'
            regExpr = re.compile(what, base.Const.IGNORE_CASE if options.ignoreCase else 0)
            errors = []
            self._traverser = base.DirTraverser.fromOptions(
                pattern, self._programOptions, errors)
            if errors:
                for error in errors:
                    self._logger.error(error)
            else:
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
                line2 = TextApp.grepFormat(theFormat, fileNames, lines[start], start+1, None)
                output(line2)
                start += 1
            return end - 1
        lines = base.StringUtils.fromFile(filename, '\n')
        nameList = [filename, os.path.dirname(filename), os.path.basename(filename)]
        first = True
        lastIx = -1
        missingInterval = None
        for ix, line in enumerate(lines):
            matcher = regExpr.search(line)
            if matcher and first and options.formatFile is not None:
                lastIx = output(TextApp.grepFormat(options.formatFile, nameList, None, None, None))
                first = False
            if matcher and not options.invertMatch or matcher is None and options.invertMatch:
                if missingInterval is not None:
                    ix2 = min(ix, missingInterval[1])
                    lastIx = outputContext(options.formatLine, nameList, missingInterval[0], ix2, lines)
                    missingInterval = None
                if options.beforeContext is not None:
                    start = max(0, lastIx + 1, ix - options.beforeContext)
                    if start < ix:
                        lastIx = outputContext(options.formatLine, nameList, start, ix, lines)
                if options.group is None:
                    output(TextApp.grepFormat(options.formatLine, nameList, line, ix+1, matcher))
                else:
                    self.grepOneLine(options, nameList, line, ix+1, regExpr)
                lastIx = ix
                if options.afterContext is not None:
                    missingInterval = [ix + 1, ix + 1 + options.afterContext]
        if missingInterval is not None:
            lastIx = min(len(lines), missingInterval[1])
            outputContext(options.formatLine, nameList, missingInterval[0], lastIx, lines)

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
            if options.beforeChars is not None:
                start = max(0, start - options.beforeChars)
            if options.afterChars is not None:
                end = min(lineLength, end + options.afterChars)
            info = line[start:end]
            info2 = TextApp.grepFormat(options.formatLine, nameList, info, lineNo, matcher)
            if self._logger._verboseLevel > 0:
                self._resultLines.append(info2)
            print(info2)

    def grepOptions(self):
        '''Evaluates the grep options.
        @return: the options stored in a OptionsGrep instance
        '''
        options = OptionsGrep()
        toDelete = []
        for ix, option in enumerate(self._programOptions):
            boolValue = base.StringUtils.boolOption(
                'ignore-case', 'i', option)
            if boolValue is not None:
                toDelete.append(ix)
                options.ignoreCase = boolValue
                continue
            boolValue = base.StringUtils.boolOption(
                'word-regexpr', 'w', option)
            if boolValue is not None:
                toDelete.append(ix)
                options.wordOnly = boolValue
                continue
            boolValue = base.StringUtils.boolOption(
                'line-number', 'n', option)
            if boolValue is not None:
                toDelete.append(ix)
                options.lineNumber = boolValue
                continue
            boolValue = base.StringUtils.boolOption(
                'invert-match', 'v', option)
            if boolValue is not None:
                toDelete.append(ix)
                options.invertMatch = boolValue
                continue
            boolValue = base.StringUtils.boolOption(
                'only-matching', 'o', option)
            if boolValue is not None:
                toDelete.append(ix)
                options.group = 0
                continue
            intValue = base.StringUtils.intOption('group', 'g', option)
            if intValue is not None:
                toDelete.append(ix)
                options.group = intValue
                continue
            intValue = base.StringUtils.intOption('after-context', 'A', option)
            if intValue is not None:
                toDelete.append(ix)
                options.afterContext = intValue
                continue
            intValue = base.StringUtils.intOption('before-context', 'B', option)
            if intValue is not None:
                toDelete.append(ix)
                options.beforeContext = intValue
                continue
            intValue = base.StringUtils.intOption('after-chars', 'a', option)
            if intValue is not None:
                toDelete.append(ix)
                options.afterChars = intValue
                if options.group is None:
                    options.group = 0
                continue
            intValue = base.StringUtils.intOption('before-chars', 'b', option)
            if intValue is not None:
                toDelete.append(ix)
                options.beforeChars = intValue
                if options.group is None:
                    options.group = 0
                continue
            intValue = base.StringUtils.intOption('context', 'C', option)
            if intValue is not None:
                toDelete.append(ix)
                options.beforeContext = options.afterContext = intValue
                continue
            strValue = base.StringUtils.stringOption('format-line', 'f', option)
            if strValue is not None:
                toDelete.append(ix)
                options.formatLine = strValue
                continue
            strValue = base.StringUtils.stringOption('format-file', 'F', option)
            if strValue is not None:
                toDelete.append(ix)
                options.formatFile = strValue
                continue
        toDelete.reverse()
        for ix in toDelete:
            del self._programOptions[ix]
        if options.formatLine is None:
            info = '%t' if options.group is None else '%{}'.format(options.group)
            options.formatLine = ('%f-%#:' if options.lineNumber else '%f:') + info
        return options

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
