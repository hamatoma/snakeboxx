'''
Created: 2020.06.24
@license: CC0 https://creativecommons.org/publicdomain/zero/1.0
@author: hm
'''
import re
import os.path
import csv
import datetime
import fnmatch

import base.Const
import base.StringUtils

class CsvProcessor:
    '''A processor for finding/modifying text.
    '''

    def __init__(self, logger):
        self._filename = None
        self._lines = None
        self._logger = logger
        self._colNames = None
        # data type of one row, e.g. [str, int, None]
        self._dataTypes = []
        # bool flags of one row: True: any row has null (empty value)
        self._hasEmpty = []
        self._rows = []
        self._indexes = None
        self._minCols = 0x7fffffff
        self._rowMinCols = None
        self._maxCols = 0
        self._rowMaxCols = None
        self._columnOrder = None
        self._dialect = None

    def addColumn(self, header, colIndex, value1, value2):
        '''Adds a CSV column to the internal structure.
        @param header: '' or the column header, e.g. 'name'
        @param colIndex: the index of the column after inserting. '0' means: the new column is the first
        @param value1: the column value in row[0]
        @param value2: None: all column values are set to value1
            Otherwise: the column value of the 2nd row. all other values will be interpolated
        '''
        index = base.StringUtils.asInt(colIndex)
        if index is None:
            self._logger.error('<index> is not an integer: ' + colIndex)
        else:
            index = index if index < len(self._rows[0]) else len(self._rows[0])
            value = value1
            step = None
            if value2 is not None:
                v1 = base.StringUtils.asInt(value1)
                v2 = base.StringUtils.asInt(value2)
                if v1 is None or v2 is None:
                    self._logger.error(
                        'cannot interpolate {}..{}'.format(value1, value2))
                    index = None
                else:
                    step = v2 - v1
                    value = v1
            if index is not None and header == '' and self._colNames is not None:
                self._logger.error(
                    'missing <header> in add-column command: may not be empty')
                index = None
            if index is not None:
                if self._colNames is not None:
                    self._colNames.insert(index, header)
                self._rows[0].insert(index, value)
                for ixRow in range(1, len(self._rows)):
                    if step is not None:
                        value += step
                    self._rows[ixRow].insert(index, value)
    @staticmethod
    def dataType(string):
        '''Returns the data type of the given string.
        @param string: string to inspect
        @return the data type: None, str int
        '''
        if string is None or string == '':
            rc = None
        elif base.StringUtils.asInt(string) is not None:
            rc = int
        else:
            rc = str
        return rc

    __description = '''= Commands of the CsvProcessor:
commands: <command1> [<command2>...]
add-column:<header>,<col-index>,<firstValue>[,<secondValue>]
    <header>: name of the column
    <col-index>: 0..N: 0 means the new column is the first column
    <first-value>: the value of the first row (below the header)
    <second-value>: if it does not exists: all other rows are set to <first-value>
        if it exists: the second row is set to this value and the next values are interpolated
info:<what1>[,<what2>...]
    Note: only filtered column will be respected
    <what>: summary | min | max | sorted | unique | multiple
set-filter:<index1>[,<index2...] or set-filter:<pattern1>[,<pattern2...]
set-order:<pattern1>[,<pattern2...]
    Sets the columns that are then written.
write:<filename>[,<delimiter>[,<backupExtension>]]
    If <filename> is empty, the current filename is taken.
    <delimiter>: the delimiter between two columns: comma | tab | semicolon
        If empty the current is taken.
    <backupExtension>: if given and a <filename> already exists: it is renamed
        with this extension. May contain placeholders %date%, %datetime% or %seconds%.
Example:
set-filter:name,prename info:summary,unique set-order:nam*,*pren* write:names.csv,tab,.%date%
'''
    @staticmethod
    def describe():
        '''Prints a description of the commands.
        '''
        print(CsvProcessor.__description)

    def execute(self, commands):
        '''Executes a sequence of commands.
        @see describe()
        @param commands: the command sequence as string
    '''
        for command in commands.split():
            name, delim, args = command.partition(':')
            if name == '' or name.startswith('#'):
                continue
            if delim != ':':
                self._logger.error('missing ":" in ' + command)
                break
            arguments = args.split(',')
            if name == 'add-column':
                if len(arguments) < 3:
                    self._logger.error(
                        'missing arguments for add-column: <header>,<col-index>,<first-value> expected')
                else:
                    self.addColumn(arguments[0], arguments[1], arguments[2], None if len(
                        arguments) < 4 else arguments[3])
            elif name == 'info':
                self.info(args)
            elif name == 'set-filter':
                if base.StringUtils.asInt(arguments[0]) is not None:
                    self.setFilterIndexes(arguments)
                else:
                    self.setFilterCols(arguments)
            elif name == 'set-order':
                self.setColumnOrder(arguments)
            elif name == 'write':
                ext = None if len(arguments) < 3 else arguments[2]
                delim = None if len(arguments) < 2 else arguments[1]
                if delim == 'comma':
                    delim = ','
                elif delim == 'semicolon':
                    delim = ';'
                elif delim == 'tab':
                    delim = '\t'
                fn = None if arguments[0] == '' else arguments[0]
                self.writeFile(fn, ext, delim)

    def info(self, what):
        '''Prints some infos about the CSV file.
        Note: only columns listed in self._indexes are inspected.
        @param what: a comma separated list of requests, e.g. 'unique,sorted,summary,min,max'
        '''
        def prefix(col):
            return '{}{}: '.format(col, (' "' + self._colNames[col] + '"') if col < len(self._colNames) else '')

        if re.search(r'unique|sorted|multiple|min|max|max-length', what) is not None:
            unique = what.find('unique') >= 0
            multiple = what.find('multiple') >= 0
            for index in self._indexes:
                cols = []
                for row in self._rows:
                    value = row[index]
                    if self._dataTypes == int:
                        cols.append(int(value))
                    else:
                        cols.append(value)
                cols.sort()
                self._logger.log('== {}'.format(prefix(index)))
                if what.find('min') >= 0:
                    self._logger.log('minimum: {}'.format(cols[0]))
                if re.search(r'(max[^-])|(max$)', what) is not None:
                    self._logger.log('maximum: {}'.format(cols[-1]))
                if what.find('max-length') >= 0:
                    maxLength = 0
                    maxString = None
                    for row in self._rows:
                        current = len(row[index])
                        if current > maxLength:
                            maxLength = current
                            maxString = row[index]
                    if maxString is not None:
                        self._logger.log(
                            'max-length: {} "{}"'.format(maxLength, maxString))
                if unique or what.find('sorted') >= 0:
                    lastValue = None
                    for col in cols:
                        if unique and col == lastValue:
                            continue
                        self._logger.log(col)
                        lastValue = col
                elif multiple:
                    lastValue = None
                    lastCount = 0
                    for col in cols:
                        if col == lastValue:
                            lastCount += 1
                        else:
                            if lastValue is not None and lastCount > 0:
                                self._logger.log('{}: {}'.format(
                                    lastValue, lastCount + 1))
                        lastValue = col
                    if lastCount > 0:
                        self._logger.log('{}: {}'.format(
                            lastValue, lastCount + 1))
        if what.find('summary') >= 0:
            info = '== summary:\nRows: {}\nCols: {}\nHeaders: {} line(s)'.format(
                len(self._rows), len(self._rows[0]), 1 if self._colNames else 0)
            info += (f'\ndelimiter: {self._dialect.delimiter}\ndoublequote: {self._dialect.doublequote}'
                     + f'\nescapechar: {self._dialect.escapechar}\nquotechar: {self._dialect.quotechar}')
            self._logger.log(info)
            for col in range(len(self._rows[0])):
                info = '{} {} {}'.format(prefix(col),
                                         str(self._dataTypes[col]), 'hasEmpty' if self._hasEmpty[col] else '')
                self._logger.log(info)

    def readFile(self, filename, mustExists=True):
        '''Reads a file into the internal buffer.
        @param filename: the file to read
        @param mustExists: True: errros will be logged
        @return True: success False: cannot read
        '''
        self._filename = filename
        rc = os.path.exists(filename)
        if not rc:
            if mustExists:
                self._logger.error('{} does not exists'.format(filename))
        else:
            with open(filename, newline='') as csvfile:
                sniffer = csv.Sniffer()
                buffer = csvfile.read(16000)
                self._dialect = sniffer.sniff(buffer)
                hasHeaders = sniffer.has_header(buffer)
                csvfile.seek(0)
                reader = csv.reader(csvfile, self._dialect)
                self._colNames = None
                ix = -1
                for row in reader:
                    ix += 1
                    if ix == 0 and hasHeaders:
                        self._colNames = row
                    else:
                        self._rows.append(row)
                        currentLength = len(row)
                        if currentLength < self._minCols:
                            self._minCols = currentLength
                            self._rowMinCols = reader.line_num
                        if currentLength > self._maxCols:
                            self._maxCols = currentLength
                            self._rowMaxCols = reader.line_num
                        if not self._dataTypes:
                            for col in row:
                                currentType = CsvProcessor.dataType(col)
                                self._dataTypes.append(currentType)
                                self._hasEmpty.append(currentType is None)
                        else:
                            for ix, col in enumerate(row):
                                currentType = self.dataType(col)
                                if ix >= len(self._dataTypes):
                                    self._dataTypes.append(currentType)
                                    self._hasEmpty.append(currentType is None)
                                else:
                                    if currentType is None:
                                        self._hasEmpty[ix] = True
                                    if self._dataTypes[ix] == int and currentType is not None and currentType != int:
                                        self._dataTypes[ix] = str
        return rc

    def setColumnOrder(self, patterns):
        '''Sets the filter indexes by column name patterns.
        @param patterns: a list of column name patterns, e.g. ['*name*', 'ag*']
        '''
        self._columnOrder = []
        for pattern in patterns:
            found = False
            ix = -1
            for name in self._colNames:
                ix += 1
                if fnmatch.fnmatch(name, pattern):
                    found = True
                    self._columnOrder.append(ix)
                    self._logger.log('pattern {} found as column {} at index {}'.format(
                        pattern, name, ix), base.Const.LEVEL_FINE)
                    break
            if not found:
                self._logger.error('pattern {} not found')

    def setFilterIndexes(self, indexes):
        '''Sets the filter indexes by indexes.
        @param indexes: a list of indexes. May be strings or integers like ['0', 2]
        '''
        self._indexes = []
        for ix in indexes:
            self._indexes.append(int(ix))
        self._indexes.sort()

    def setFilterCols(self, patterns):
        '''Sets the filter indexes by column name patterns.
        @param patterns: a list of column name patterns, e.g. ['*name*', 'ag*']
        '''
        self._indexes = []
        for pattern in patterns:
            found = False
            ix = -1
            for name in self._colNames:
                ix += 1
                if fnmatch.fnmatch(name, pattern):
                    found = True
                    self._indexes.append(ix)
                    self._logger.log('pattern {} found as column {} at index {}'.format(
                        pattern, name, ix), base.Const.LEVEL_FINE)
                    break
            if not found:
                self._logger.error('col name pattern {} not found in [{}]'.format(
                    pattern, ','.join(self._colNames)))
                break
        self._indexes.sort()

    def quoteString(self, string):
        '''Quotes the given string if necessary.
        @param string: the string to quote
        @return: string or the quoted string
        '''
        rc = string
        quote = self._dialect.quotechar
        delim = self._dialect.delimiter
        forceQuoting = self._dialect.quoting == csv.QUOTE_ALL or (
            self._dialect.quoting == csv.QUOTE_NONNUMERIC and base.StringUtils.asInt(string) is None)
        if forceQuoting or string.find(delim) >= 0:
            if self._dialect.doublequote:
                string = string.replace(delim, delim + delim)
            else:
                esc = self._dialect.escapechar
                string = string.replace(
                    esc, esc + esc).replace(quote, esc + quote)
            rc = quote + string + quote
        return rc

    def writeFile(self, filename=None, backupExtension=None, delimiter=None):
        '''Writes the internal buffer as a file.
        @param filename: the file to write: if None _filename is taken
        @param backupExtension: None or: if the file already exists it will be renamed with this extension
                macros: '%date%' replace with the  current date %datetime%: replace with the date and time
                '%seconds%' replace with the seconds from epoc
        '''
        filename = self._filename if filename is None else filename
        delimiter = self._dialect.delimiter if delimiter is None else delimiter
        if os.path.exists(filename) and backupExtension is not None:
            if backupExtension.find('%') >= 0:
                now = datetime.datetime.now()
                backupExtension = backupExtension.replace(
                    '%date%', now.strftime('%Y.%m.%d'))
                backupExtension = backupExtension.replace(
                    '%datetime%', now.strftime('%Y.%m.%d-%H_%M_%S'))
                backupExtension = backupExtension.replace(
                    '%seconds%', now.strftime('%a'))
            if not backupExtension.startswith('.'):
                backupExtension = '.' + backupExtension
            parts = base.FileHelper.splitFilename(filename)
            parts['ext'] = backupExtension
            newNode = parts['fn'] + backupExtension
            base.FileHelper.deepRename(filename, newNode, deleteExisting=True)
        with open(filename, "w") as fp:
            indexes = self._columnOrder if self._columnOrder is not None else [
                ix for ix in range(len(self._rows[0]))]
            if self._colNames is not None:
                line = ''
                for ix, item in enumerate(indexes):
                    if ix > 0:
                        line += delimiter
                    line += self.quoteString(self._colNames[item])
                fp.write(line + self._dialect.lineterminator)
            for row in self._rows:
                line = ''
                for ix, item in enumerate(indexes):
                    if ix > 0:
                        line += delimiter
                    value = base.StringUtils.toString(row[item])
                    line += self.quoteString(value)
                fp.write(line + self._dialect.lineterminator)


if __name__ == '__main__':
    pass
