#! /usr/bin/python3
'''
Created: 2020.06.24
@license: CC0 https://creativecommons.org/publicdomain/zero/1.0
@author: hm
'''
import sys
import os

sys.path.insert(0, '/usr/share/snakeboxx')
import base.CsvProcessor
import base.TextProcessor
import base.DirTraverser
import base.FileHelper
import app.BaseApp


class OptionsExecuteRules:
    '''Options for the mode execute-rules.
    '''

    def __init__(self):
        self._maxLoop = 1
        self._aboveFilename = False
        self._inPlace = None
        self._outPattern = None


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

    def execRulesOptions(self):
        '''Analyses the options of the mode exec-rules.
        @return: an instance of OptionsExecuteRules
        '''
        options = OptionsExecuteRules()
        toDelete = []
        ix = -1
        for option in self._programOptions:
            ix += 1
            boolValue = base.StringUtils.boolOption(
                'above-filename', 'a', option)
            if boolValue is not None:
                toDelete.append(ix)
                options._aboveFilename = boolValue
                continue
            strValue = base.StringUtils.stringOption('in-place', 'i', option)
            if strValue is not None:
                toDelete.append(ix)
                options._inPlace = strValue
                continue
            intValue = base.StringUtils.intOption('max-loop', 'l', option)
            if intValue is not None:
                toDelete.append(ix)
                options._maxLoop = intValue
                continue
        for ix in range(len(toDelete)):
            del self._programOptions[ix]
        return options

    def execRulesOneFile(self, rules, options):
        '''Executes rules for one file.
        @param filename: file to process
        @param rules: the rules to execute
        @param options: the program options (instance of OptionsExecuteRules)
        '''
        self._processor.readFile(self._traverser._fileFullName)
        self._processor.executeRules(rules)
        if self._processor._hasChanged:
            if options._inPlace is not None:
                if options._inPlace != '':
                    src = self._traverser._fileFullName
                    parts = base.FileHelper.splitFilename(src)
                    parts['ext'] = options._inPlace
                    trg = ''.join(parts)
                    if os.path.exists(trg):
                        os.unlink(trg)
                    os.rename(src, trg)
                self._processor.writeFile()

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
            csv = base.CsvProcessor.CsvProcessor(self._logger)
            csv.describe()
        else:
            self.abort('unknown mode: ' + self._mainMode)


def main(args):
    '''Main function.
    @param args: the program arguments
    '''
    application = TextApp(args)
    application.main()


if __name__ == '__main__':
    main(sys.argv[1:])
