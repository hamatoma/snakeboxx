'''
Created: 2020.06.24
@license: CC0 https://creativecommons.org/publicdomain/zero/1.0
@author: hm
'''
import re
import os.path
import datetime

import base.Const
import base.StringUtils


class CommandData:
    '''Properties given for a command (action except search and reposition).
    @param register: None or the related register ('A'..'Z')
    @param marker: None or the related marker: 'a' .. 'z'
    @param text: None or the related text
    @param text2: None or the related 2nd text
    @param group: None or the related reg. expression group: 0..N
    @param escChar: None or a prefix character to address registers (@see parseRuleReplace())
    @param options: None or an command specific options
    '''

    def __init__(self, register=None, register2=None, marker=None, text=None, text2=None,
                 group=None, escChar=None, options=None):
        self._register = register
        self._register2 = register2
        self._marker = marker
        self._text = text
        self._text2 = text2
        self._group = group
        self._options = options
        self._escChar = escChar

    def getText(self, state, second=False):
        '''Replaces register placeholders with the register content.
        Note: register placeholders starts with self._escChar followed by the register name, e.g. '$A'
        @param state: the ProcessState instance with the registers
        @param second: True: _text2 is used False: _text is used
        @return text with replaced register placeholders
        '''
        text = self._text2 if second else self._text
        if self._escChar is None:
            rc = text
        else:
            startIx = 0
            rc = ''
            while startIx + 2 < len(text):
                ix = text.find(self._escChar, startIx)
                if ix < 0:
                    break
                rc += text[startIx:ix]
                name = text[ix + 1]
                if 'A' <= name <= 'Z':
                    rc += state.getRegister(name)
                else:
                    rc += self._escChar + name
                startIx = ix + 2
            rc += text[startIx:]
        return rc


class FlowControl:
    '''Flow control of a rule: continue, stop or jump on a condition
    '''
    # ..................................A.........A

    def __init__(self):
        '''Constructor.
        '''
        self._onSuccess = 'c'
        self._onError = 'e'

    def setControl(self, control):
        '''Translate the options given as string into the class variables.
        @param control: the control as string
        @param logger: only internal errors are possible
        @return: None: success otherwise: error message
        '''
        rc = None
        reaction = None
        if control[-1] == '%':
            reaction = control[control.find('%'):]
        elif control.endswith('continue'):
            reaction = 'c'
        elif control.endswith('stop'):
            reaction = 's'
        elif control.endswith('error'):
            reaction = 'e'  # error
        else:
            rc = 'unknown control: ' + control
        if control.startswith('success'):
            self._onSuccess = reaction
        elif control.startswith('error'):
            self._onError = reaction
        else:
            rc = 'unknown control statement: ' + control
        return rc


class Position:
    '''Constructor.
    @param line: the line number
    @param col: the column number
    '''

    def __init__(self, line, col):
        self._line = line
        self._col = col

    def toString(self):
        '''Returns the position as string.
        @return: <line>:<col>
        '''
        return '{}:{}'.format(self._line, self._col)

    def check(self, lines, behindLineIsAllowed=False):
        '''Checks, whether the instance is valid in lines.
        @param lines: the list of lines to inspect
        @param behindLineIsAllowed: True: the column may be equal the line length
        @return: True: the cursor is inside the lines
        '''
        rc = self._line < len(lines) and self._col <= len(
            lines[self._line]) - (1 if behindLineIsAllowed else 0)
        return rc

    def clone(self, source):
        '''Transfers the internal state from the source to the self.
        @param source: the Position instance to clone
        '''
        self._line = source._line
        self._col = source._col

    def compare(self, other):
        '''Compares the instance with an other instance
        @param other: the Position instance to compare
        @return: <0: self < other 0: self==other >0: self>other
        '''
        rc = self._line - other._line
        if rc == 0:
            rc = self._col - other._col
        return rc

    def endOfLine(self, lines):
        '''Tests whether the instance is one position behind the current line.
        @param lines: the list of lines to inspect
        @return: True: the instance points to the position one behind the current line or the beginning of the next line
        '''
        rc = self._line == len(
            lines) and self._col == 0 or self._col == len(lines[self._line])
        return rc


class ProcessState:
    '''Reflects the state while processing a rule list.
    '''

    def __init__(self, lines, startRange, endRange, start, logger, maxLoops=10):
        '''Constructor.
        @param lines: the list of lines to inspect
        @param startRange: the rule starts at this position
        @param endRange: the end of the rules must be below this position
        @param start: the rule starts from this position
        @param logger:
        @param maxLoops: the number of executed rules is limited to maxLoops*len(lines)
        '''
        self._logger = logger
        self._lines = lines
        self._maxLoops = maxLoops
        self._cursor = Position(start._line, start._col)
        self._startRange = startRange
        self._endRange = endRange
        self._logger = logger
        self._success = True
        self._lastMatch = None
        # replaces temporary _startRange or _endRange
        self._tempRange = Position(0, 0)
        self._safePosition = Position(0, 0)
        # <name>: Position
        self._markers = {}
        # <name>: string
        self._registers = {}
        self._hasChanged = False
        self._lastHits = 0

    def deleteToMarker(self, name):
        '''Deletes the text from the cursor to the marker.
        @param name: a bound of the region to delete, _position is the other
        '''

        marker = self.getMarker(name)
        self._success = marker is not None and self.inRange(
            marker) and self.inRange()
        if self._success:
            comp = self._cursor.compare(marker)
            start = marker if comp >= 0 else self._cursor
            end = self._cursor if comp >= 0 else marker
            ixStart = start._line
            deletedLines = 0
            self._hasChanged = True
            if start._line == end._line:
                self._lines[ixStart] = self._lines[ixStart][0:start._col] + \
                    self._lines[ixStart][end._col:]
            else:
                prefix = '' if start._col == 0 else self._lines[start._line][0:start._col]
                ixEnd = end._line if end._col > 0 else end._line + 1
                if end._col > 0:
                    self._lines[end._line] = prefix + \
                        self._lines[end._line][end._col:]
                for ix in range(ixStart, ixEnd):
                    del self._lines[ix]
                    deletedLines += 1
            # Adapt the existing markers:
            for name2 in self._markers:
                current = self.getMarker(name2)
                if current.compare(start) >= 0:
                    if current._line > end._line or current._line == end._line and end._col == 0:
                        current._line -= deletedLines
                    elif current._line == end._line:
                        if current._col > end._col:
                            current._col -= end.col
                        current.clone(start)
                    else:
                        current.clone(start)

    def insertAtCursor(self, text):
        '''Inserts a text at the cursor.
        @param text: the text to insert, may contain '\n'
        '''
        self._success = self.inRange()
        if self._success:
            newLines = text.split('\n')
            curLine = self._cursor._line
            self._hasChanged = True
            if len(newLines) == 1:
                insertedLines = 0
                colNew = self._cursor._col + len(text)
                self._lines[curLine] = (self._lines[curLine][0:self._cursor._col] + newLines[0]
                                        + self._lines[curLine][self._cursor._col:])
            else:
                insertedLines = len(newLines)
                tail = ''
                ixNew = 0
                if self._cursor._col > 0:
                    ixNew = 1
                    tail = self._lines[self._cursor._line][self._cursor._col:]
                    self._lines[curLine] = self._lines[curLine][0:self._cursor._col] + newLines[0]
                    curLine += 1
                    insertedLines -= 1
                ixLast = len(newLines)
                while ixNew < ixLast:
                    self._lines.insert(curLine, newLines[ixNew])
                    ixNew += 1
                    curLine += 1
                self._lines[curLine - 1] = self._lines[curLine - 1] + tail
                colNew = len(newLines[-1])
            for name in self._markers:
                marker = self._markers[name]
                if marker.compare(self._cursor) >= 0:
                    if marker._line == self._cursor._line and marker._col > self._cursor._col:
                        marker._line += insertedLines
                        marker._col += len(newLines[-1])
                    elif marker._line == self._cursor._line > 0:
                        marker._line += insertedLines
            self._cursor._line += insertedLines
            self._cursor._col = colNew

    def getMarker(self, name):
        '''Returns the marker given by the name ('a'..'z')
        @param name: the marker's name: 'a'..'z'
        @return: None: not found otherwise: the Position instance
        '''
        rc = None if not name in self._markers else self._markers[name]
        return rc

    def getRegister(self, name, maxLength=None):
        '''Returns the marker given by the name ('a'..'z')
        @param name: the marker's name: 'a'..'z'
        @return: '': not found otherwise: the register content
        '''
        rc = '' if not name in self._registers else self._registers[name]
        if maxLength is not None:
            rc = base.StringUtils.limitLength2(
                rc, maxLength).replace('\n', '\\n')
        return rc

    def inRange(self, position=None):
        '''Returns whether a position is in the current range.
        @param position: a Position instance to test
        @return: position is between _startRange and _endRange
        '''
        if position is None:
            position = self._cursor
        rc = (position._line > self._startRange._line
              or position._line == self._startRange._line and position._col >= self._startRange._col)
        rc = rc and (position._line < self._endRange._line or position._line == self._endRange._line
                     and position._col <= self._endRange._col)
        return rc

    def putToRegister(self, name, text, append=False):
        '''Sets the register <name> with a text.
        @param name: the register name: 'A'..'Z'
        @param text: the text to set
        @param append: True: the text will be appended False: the text will be set
        '''
        if not append or not name in self._registers:
            self._registers[name] = text
        else:
            self._registers[name] += text

    def setMarker(self, name):
        '''Sets the marker <name> from the current position.
        @param name: the marker name: 'a'..'z'
        '''
        if not name in self._markers:
            self._markers[name] = Position(0, 0)
        self._markers[name].clone(self._cursor)

    def textToMarker(self, name):
        '''Returns the text between the marker name and the cursor.
        @param name: the marker's name
        @return: the text between marker and cursor (current position)
        '''
        rc = ''
        marker = self.getMarker(name)
        if marker is not None and self.inRange(marker) and self.inRange():
            comp = self._cursor.compare(marker)
            start = marker if comp >= 0 else self._cursor
            end = self._cursor if comp >= 0 else marker
            ixStart = start._line
            if start._line == end._line:
                rc = self._lines[start._line][start._col:end._col]
            else:
                if start._col > 0:
                    prefix = self._lines[start._line][start._col:]
                    ixStart += 1
                rc = '\n'.join(self._lines[ixStart:end._line])
                if start._col > 0:
                    if rc == '':
                        rc = prefix
                    else:
                        rc = prefix + '\n' + rc
                if end._col > 0:
                    if rc != '':
                        rc += '\n'
                    rc += self._lines[end._line][0:end._col]
        return rc


class Region:
    '''Stores the data of a region, which is a part of the file given by a start and an end position.
    '''

    def __init__(self, parent, startRuleList=None, endRuleList=None, endIsIncluded=False):
        '''Constructor.
        @param parent: the TextProcessor instance
        @param startRuleList: None or the compiled rules defining the start of the region
        @param startRuleList: None or the compiled rules defining the end of the region
        @param endIsIncluded: True: if the last rule is a search: the hit belongs to the region
        '''
        self._parent = parent
        self._startRules = startRuleList
        self._endRules = endRuleList
        self._startPosition = Position(0, 0)
        # index of the first line below the region (exclusive)
        self._endPosition = Position(0, 0)
        self._endIsIncluded = endIsIncluded
        self._start = None
        self._end = None

    def next(self):
        '''Search the next region from current region end.
        @param ixFirst: the index of the first line (in parent._lines) to inspect
        @return: True: the start has been found False: not found
        '''
        rc = self._parent.apply(
            self._startRules, self._endPosition, self._parent._endOfFile)
        return rc

    def find(self, pattern):
        '''Searches the pattern in the region.
        @param pattern: a string or a RegExp instance to search
        @return: -1: not found otherwise: the index of the first line matching the pattern
        '''
        rc = self._parent.findLine(pattern, self._start, self._end)
        return rc


class Rule:
    '''Describes a single action: search, reposition, set label/bookmark, print....
    @see RuleList vor details.
    '''

    def __init__(self, ruleType, param=None):
        '''Constructor.
        @param ruleType: the type: '<' (search backwards) '>': search forward 'l': line:col 'a': anchor
        @param parameter: parameter depending on ruleType: RegExp instance for searches,
            names for anchors or a [<line>, <col>] array for ruleType == 'l'
        '''
        self._ruleType = ruleType
        self._param = param
        self._flowControl = FlowControl()

    def name(self, extended=False):
        '''Returns the command name.
        @return the command name
        '''
        rc = None
        if self._ruleType == '%':
            rc = 'label' + ((' ' + self._param) if extended else '')
        elif self._ruleType == '>':
            rc = 'search (forward)' + ((' /' +
                                        self._param._regExpr.pattern + '/') if extended else '')
        elif self._ruleType == '<':
            rc = 'search (backward)' + ((' /' +
                                         self._param._regExpr.pattern + '/') if extended else '')
        elif self._ruleType == '+':
            rc = 'reposition'
            if extended:
                rc += ' {}{}:{}'.format(self._param[2],
                                        self._param[0], self._param[1])
        elif self._ruleType == 'anchor':
            rc = self._param
        else:
            rc = self._ruleType
        return rc

    def searchForward(self, state):
        '''Searches forward in lines in the range given by startRange and endRange.
        @param processState: IN/OUT: the context of searching, an instance of ProcessState
        '''
        state._safePosition.clone(state._cursor)
        state._success = state.inRange()
        if state._success:
            startIx = state._cursor._line
            endIx = min(len(state._lines), state._endRange._line + 1)
            if self._param._rangeLines is not None:
                endIx = min(startIx + self._param._rangeLines, endIx)
            match = None
            regExpr = self._param._regExpr
            for ix in range(startIx, endIx):
                if ix == state._startRange._line:
                    match = regExpr.search(
                        state._lines[ix], state._startRange._col)
                elif ix == state._endRange._line:
                    match = regExpr.search(
                        state._lines[ix], 0, state._endRange._col)
                else:
                    match = regExpr.search(
                        state._lines[ix], state._startRange._col)
                if match is not None:
                    break
            state._success = match is not None
            state._lastMatch = match
            if state._success:
                state._cursor._line = ix
                state._cursor._col = match.end(
                    0) if self._param._useEnd else match.start(0)
                state._success = state.inRange()

    def searchBackward(self, state):
        '''Searches backward in lines in the range given by startRange and endRange.
        @param processState: IN/OUT: the context of searching, an instance of ProcessState
        '''
        state._safePosition.clone(state._cursor)
        state._success = state.inRange()
        if state._success:
            regExpr = self._param._regExpr
            startIx = max(0, min(state._cursor._line, len(state._lines) - 1))
            endIx = state._startRange._line - 1
            state._lastMatch = None
            if self._param._rangeLines is not None:
                endIx = max(state._startRange._line - 1,
                            max(-1, startIx - self._param._rangeLines))
            for ix in range(startIx, endIx, -1):
                if ix == state._startRange._line:
                    iterator = regExpr.finditer(
                        state._lines[ix], state._startRange._col)
                elif ix == state._endRange._line:
                    iterator = regExpr.finditer(
                        state._lines[ix], 0, state._endRange._col)
                else:
                    iterator = regExpr.finditer(
                        state._lines[ix], state._startRange._col)
                # Look for the last match:
                for match in iterator:
                    state._lastMatch = match
                if state._lastMatch is not None:
                    break
            state._success = state._lastMatch is not None
            if state._success:
                state._cursor._line = ix
                state._cursor._col = state._lastMatch.end(
                    0) if self._param._useEnd else state._lastMatch.start(0)
                state._success = state.inRange()

    def reposition(self, state):
        '''Apply the reposition rule: an anchor or a line/col move.
        @param processState: IN/OUT: the context of searching, an instance of ProcessState
        '''
        if self._ruleType == '+':
            if self._param[2] == ':':
                state._cursor._line = self._param[0]
                state._cursor._col = self._param[1]
            else:
                state._cursor._line += self._param[0]
                state._cursor._col += self._param[1]
                # if the new line is shorter than the old col position: goto last column
                # except the column is explicitly set
                if self._param[1] == 0 and state._cursor._line < len(state._lines):
                    lineLength = len(state._lines[state._cursor._line])
                    if state._cursor._col >= lineLength:
                        state._cursor._col = max(0, lineLength - 1)
        elif self._param == 'bof':
            state._cursor._line = state._cursor._col = 0
        elif self._param == 'eof':
            state._cursor._line = len(state._lines)
            state._cursor._col = 0
        elif self._param == 'bol':
            state._cursor._col = 0
        elif self._param == 'eol':
            # overflow is allowed:
            state._cursor._line += 1
            state._cursor._col = 0
        elif self._param == 'bopl':
            state._cursor._line -= 1
            state._cursor._col = 0
        elif self._param == 'eopl':
            state._cursor._col = 0
        elif self._param == 'bonl':
            # overflow is allowed:
            state._cursor._line += 1
            state._cursor._col = 0
        elif self._param == 'eonl':
            # overflow is allowed:
            state._cursor._line += 2
            state._cursor._col = 0
        else:
            state._logger.error(
                'reposition(): unknown anchor: {}'.format(self._param))
        state._success = state.inRange()

    def state(self, after, state):
        '''Returns the "state" of the rule, used for tracing.
        @param after: True: the state is after the rule processing
        @param state: the ProcessState instance
        @return: the specific data of the rule
        '''
        def cursor():
            return state._cursor.toString()

        def marker():
            name = self._param._marker
            return '{}[{}]'.format(name, '-' if name not in state._markers else state.getMarker(self._param._marker).toString())

        def register():
            name = self._param._register
            return ((name if name is not None else '<none>') + ':'
                    + ('<none>' if name not in state._registers else state.getRegister(name, 40)))
        name = self._ruleType
        if not after:
            state._traceCursor = cursor()
            state._traceState = ''
            rc = ''
        else:
            rc = '{} => {}, {} => '.format(
                state._traceCursor, cursor(), state._traceState)
        if name in ('>', '<', '+', 'anchor', 'swap'):
            rc += '-'
        elif name in ('add', 'insert', 'set', 'expr', 'state'):
            rc += register()
        elif name == 'cut':
            # cut-m
            # cut-R-m
            rc += '' if after else marker() + ' / '
            if after and self._param._register is not None:
                rc += register()
            else:
                rc += '-'
        elif name == 'group':
            rc += register()
        elif name == 'jump':
            if after and self._param._marker is not None:
                rc += state.getMarker(self._param._marker).toString()
            else:
                rc += '-'
        elif name == 'mark':
            rc += marker()
        elif name == 'print':
            if self._param._marker is not None:
                rc += marker() if after else '-'
            elif self._param._register is not None:
                rc += register() if after else ''
        elif name == 'replace':
            if self._param._register is not None:
                rc += register()
            elif self._param._marker is not None and after:
                rc += marker()
            else:
                rc += '-'
            if after:
                rc += ' hits: {}'.format(state._lastHits)
        if not after:
            state._traceState = rc
        return rc

    def toString(self):
        '''Returns a string describing the instance.
        @return: a string describing the instance
        '''
        name = self._ruleType
        if name in ('>', '<'):
            rc = name + '/' + \
                base.StringUtils.limitLength2(
                    self._param._regExpr.pattern, 40) + '/'
        elif name == '+':
            rc = 'reposition {}{}:{}'.format(
                self._param[2], self._param[0], self._param[1])
        elif name == 'anchor':
            rc = self._param
        elif name == 'jump':
            rc = name + '-' + \
                (self._param._marker if self._param._marker is not None else self._param._text)
        elif name == '%':
            rc = 'label ' + self._param
        elif name == 'replace':
            rc = name
            if self._param._register is not None:
                rc += '-' + self._param._register
            if self._param._marker is not None:
                rc += '-' + self._param._marker
            rc += (':/' + base.StringUtils.limitLength2(self._param._text, 20)
                   + '/' + base.StringUtils.limitLength2(self._param._text2, 20))
        else:
            rc = name
            if self._param._register is not None:
                rc += '-' + self._param._register
            if self._param._marker is not None:
                rc += '-' + self._param._marker
            if self._param._text is not None:
                rc += ':"' + \
                    base.StringUtils.limitLength2(self._param._text, 40) + '"'
        return rc


class RuleList:
    '''A list of rules to find a new position or do some other things.
    @see describe() for detailed description.
    '''
    #..........................rule
    # .........................1
    __reRule = re.compile(r'%[a-zA-Z_]\w*%:'
                          #        rule
                          #........A
                          + r'|(?:[be]of|[be]o[pn]?l'
                          #...........line........col
                          #.............1...1......2...2
                          + r'|[+-]?(\d+):[+-]?(\d+)'
                          #..............sep.....sep rows/cols
                          #..............3..3........C.......C
                          + r'|[<>FB](\S).+?\3\s?(?::?\d+)?\s?[ie]{0,2}'
                          #.command.name
                          # .......4E
                          + r'|((?:add|cut|expr|group|insert|jump'
                          # ........................................./name
                          # .........................................E
                          + r'|mark|print|replace|set|state|swap)'
                          #..suffix1 name...............suffix2.........text.delim......txt-opt /t /command
                          # ......F...G........... ....GF.H...........H.I...5.....5.....J......J.I.4
                          + r'(?:-(?:[a-zA-Z]|\d\d?))?(?:-[a-zA-Z])?(?::([^\s]).*?\5(?:e=\S)?)?)'
                          #.......A
                          + r')')
    __reRuleExprParams = re.compile(r'[-+/*%](\$[A-Z]|\d+)?')
    # .........................1......12..............2.3.........3
    __reCommand = re.compile(r'([a-z]+)(-[a-zA-Z]|-\d+)?(-[a-zA-Z])?')
    __reRuleStateParam = re.compile(r'rows?|col|size-[A-Z]|rows-[A-Z]|hits')
    __reFlowControl = re.compile(
        r'(success|error):(continue|error|stop|%\w+%)')
    # ....................................A.........  A..1......12...2..3..3..4...........4
    __reRuleReplace = re.compile(
        r'replace(?:-[a-zA-Z])?:([^\s])(.+?)\1(.*?)\1(e=.|,|c=\d+)*')
    # x=re.compile(r'replace:([^\s])(.+)\1(.*)\1(e=.)?')

    def __init__(self, logger, rules=None):
        '''Constructor.
        @param rules: None or the rules as string
            Example: '>/logfile:/ -2:0 bol':
            search forwards "logfile:" go backward 2 line 0 column, go to begin of line
        '''
        self._logger = logger
        self._col = 0
        self._currentRule = ''
        self._errorCount = 0
        self._rules = []
        self._labels = {}
        self._markers = {}
        self._fpTrace = None
        self._maxLoops = None
        if rules is not None:
            self.parseRules(rules)

    def appendCommand(self, name, commandData):
        '''Stores the command data in the _rules.
        Stores markers defined by "mark".
        Tests used markers for a previous definition.
        @param name: the name of the command, e.g. 'add'. Will be used as _ruleType
        @param commandData: an instance of CommandData
        '''
        if name == 'mark':
            self._markers[commandData._marker] = self._col
        elif commandData._marker is not None and commandData._marker not in self._markers:
            self.parseError(
                'marker {} was not previously defined'.format(commandData._marker))
        self._rules.append(Rule(name, commandData))

    def apply(self, state):
        '''Executes the internal stored rules in a given list of lines inside a range.
        @param state: IN/OUT IN: the context to search OUT: the state at the end of applying the rule list
        '''
        ix = 0
        count = 0
        maxCount = len(state._lines) * state._maxLoops
        while ix < len(self._rules):
            if count >= maxCount:
                state._logger.error(
                    'Rule.apply(): to many loops: {}'.format(self._maxLoops))
                break
            item = self._rules[ix]
            if self._fpTrace is not None:
                ixTrace = ix
                self.trace(ixTrace, False, state)
            flowControl = self._rules[ix]._flowControl
            ix += 1
            if item._ruleType == '>':
                item.searchForward(state)
            elif item._ruleType == '<':
                item.searchBackward(state)
            elif item._ruleType == '%':
                # label
                pass
            elif item._ruleType == 'anchor' or item._ruleType == '+':
                item.reposition(state)
            elif item._ruleType >= 'p':
                self.applyCommand2(item, state)
            else:
                ix2 = self.applyCommand1(item, state)
                if ix2 is not None:
                    ix = ix2
            if self._fpTrace is not None:
                self.trace(ixTrace, True, state)
            if flowControl is not None:
                reaction = flowControl._onSuccess if state._success else flowControl._onError
                if reaction == 'c':
                    pass
                elif reaction == 's':
                    break
                elif reaction == 'e':
                    self._logger.error('{} stopped with error')
                    break
                elif reaction in self._labels:
                    ix = self._labels[reaction] + 1

    def applyCommand1(self, rule, state):
        '''Executes the action named 'a*' to 'p*' (exclusive)
        @param processState: IN/OUT IN: the context to search OUT: the state at the end of applying the rule list
        @return: None: normal processing otherwise: the index of the next rule to process
        '''
        rc = None
        name = rule._ruleType
        checkPosition = False
        if name == 'add':
            # add-R-m
            # add-R-S
            # add-R D<text>D
            if rule._param._marker is not None:
                text = state.textToMarker(rule._param._marker)
            elif rule._param._register2 is not None:
                text = state.getRegister(rule._param._register2)
            elif rule._param._text is not None:
                text = rule._param.getText(state)
            else:
                state._logger.error('add: nothing to do')
                text = ''
            state.putToRegister(rule._param._register, text, append=True)
        elif name == 'cut':
            # cut-m
            # cut-R-m
            if rule._param._register is not None:
                text = state.textToMarker(rule._param._marker)
                state.putToRegister(rule._param._register, text)
            state.deleteToMarker(rule._param._marker)
        elif name == 'expr':
            # expr-R:"+4"
            value = base.StringUtils.asInt(
                state.getRegister(rule._param._register), 0)
            param = rule._param.getText(state)
            value2 = base.StringUtils.asInt(param[1:], 0)
            op = param[0]
            if op == '+':
                value += value2
            elif op == '-':
                value -= value2
            elif op == '*':
                value *= value2
            elif op == '/':
                if value2 == 0:
                    state._success = self._logger.error(
                        'division by 0 is not defined')
                else:
                    value //= value2
            elif op == '%':
                if value2 == 0:
                    state._success = self._logger.error(
                        'modulo 0 is not defined')
                else:
                    value %= value2
            state._registers[rule._param._register] = str(value)
        elif name == 'insert':
            # insert-R
            # insert D<content>D
            text = ''
            if rule._param._register is not None:
                text = state.getRegister(rule._param._register)
            elif rule._param._text is not None:
                text = rule._param.getText(state)
            state.insertAtCursor(text)
        elif name == 'group':
            # group-G-R
            state._success = state._lastMatch is not None and state._lastMatch.lastindex <= rule._param._group
            if state._success:
                text = '' if state._lastMatch.lastindex < rule._param._group else state._lastMatch.group(
                    rule._param._group)
                state.putToRegister(rule._param._register, text)
        elif name == 'jump':
            if rule._param._marker is not None:
                state._cursor.clone(state.getMarker(rule._param._marker))
                checkPosition = True
            else:
                rc = self._labels[rule._param._text]
        elif name == 'mark':
            state.setMarker(rule._param._marker)
        else:
            state._logger.error('applyCommand1: unknown command')
        if checkPosition:
            state._success = state.inRange()
        return rc

    def applyCommand2(self, rule, state):
        '''Executes the actions named 'p*' to 'z*' (inclusive)
        @param processState: IN/OUT IN: the context to search OUT: the state at the end of applying the rule list
        '''
        name = rule._ruleType
        if name == 'print':
            state._success = True
            if rule._param._register is not None:
                print(state.getRegister(rule._param._register))
            elif rule._param._marker is not None:
                print(state.textToMarker(rule._param._marker))
            elif rule._param._text is not None:
                print(rule._param.getText(state))
        elif name == 'replace':
            param = rule._param
            if param._register is not None:
                replaced, state._lastHits = re.subn(
                    param._text, param._text2, state.getRegister(param._register))
                state._registers[param._register] = replaced
            elif param._marker is not None:
                self.applyReplaceRegion(state._cursor, state.getMarker(param._marker),
                                        re.compile(param._text), param._text2, state)
            else:
                # replace in the current line:
                line = state._lines[state._cursor._line]
                replaced, state._lastHits = re.subn(
                    param._text, param._text2, line)
                if line != replaced:
                    state._hasChanged = True
                    state._lines[state._cursor._line] = replaced
        elif name == 'set':
            if rule._param._marker is not None:
                text = state.textToMarker(rule._param._marker)
            elif rule._param._register2 is not None:
                text = state.textToMarker(rule._param._marker)
            elif rule._param._text is not None:
                text = rule._param.getText(state)
            else:
                state._logger.error('set: nothing to do')
                text = ''
            state.putToRegister(rule._param._register, text)
        elif name == 'state':
            name = rule._param._text
            if name == 'row':
                value = state._cursor._line + 1
            elif name == 'col':
                value = state._cursor._col + 1
            elif name == 'rows':
                value = len(state._lines)
            elif name.startswith('size-'):
                value = len(state.getRegister(name[5]))
            elif name.startswith('rows-'):
                value = state.getRegister(name[5]).count('\n')
            elif name == 'hits':
                value = state._lastHits
            else:
                value = '?'
            state._registers[rule._param._register] = str(value)
        elif name == 'swap':
            marker = state.getMarker(rule._param._marker)
            if marker is None:
                state._success = False
                state._logger.error(
                    'swap: marker {} is not defined'.format(rule._param._marker))
            else:
                state._tempRange.clone(state._cursor)
                state._cursor.clone(marker)
                marker.clone(state._tempRange)
                state._success = state.inRange()
        else:
            self._logger.error(
                'unknown command {} in {}'.format(name, rule._ruleType))

    def applyReplaceRegion(self, start, end, what, replacement, state):
        '''Replaces inside the region.
        @param start: first bound of the region
        @param end: second bound of the region
        @param what: the regular expression to search
        @param replacement: the string to replace
        @param state: a ProcessState instance
        '''
        if start.compare(end) > 0:
            start, end = end, start
        state._lastHits = 0
        if start._line == end._line:
            value = state._lines[start._line][start._col:end._col]
            value2, hits = what.subn(replacement, value)
            if value != value2:
                state._lastHits += hits
                state._hasChanged = True
                state._lines[start._line] = state._lines[start._line][0:start._col] + \
                    value2 + state._lines[end._line][end._col:]
        else:
            startIx = start._line
            if start._col > 0:
                value = state._lines[start._line][start._col:]
                value2, hits = what.subn(replacement, value)
                if value != value2:
                    state._lastHits += hits
                    state._hasChanged = True
                    state._lines[start._line] = state._lines[start._line][0:start._col] + value2
                startIx += 1
            for ix in range(startIx, end._line):
                value = state._lines[ix]
                value2, hits = what.subn(replacement, value)
                if value != value2:
                    state._lastHits += hits
                    state._hasChanged = True
                    state._lines[ix] = value2
            if end._col > 0:
                value = state._lines[end._line][0:end._col]
                value2, hits = what.subn(replacement, value)
                if value != value2:
                    state._lastHits += hits
                    state._hasChanged = True
                    state._lines[end._line] = value2 + \
                        state._lines[end._line][end._col:]

    def check(self):
        '''Tests the compiled rules, e.g. existence of labels.
        @return: None OK otherwise: the error message
        '''
        self._labels = {}
        ix = -1
        for rule in self._rules:
            ix += 1
            if rule._ruleType == '%':
                self._labels[rule._param] = ix
        for rule in self._rules:
            if rule._flowControl is not None:
                label = rule._flowControl._onSuccess
                if label.startswith('%') and label not in self._labels:
                    self._logger.error(
                        'unknown label (on success) {}'.format(label))
                    self._errorCount += 1
                label = rule._flowControl._onError
                if label.startswith('%') and label not in self._labels:
                    self._logger.error(
                        'unknown label (on error): {}'.format(label))
                    self._errorCount += 1
                if rule._ruleType == 'jump' and rule._param._text is not None and rule._param._text not in self._labels:
                    self._logger.error(
                        'unknown jump target: {}'.format(rule._text))
                    self._errorCount += 1
        rc = self._errorCount == 0
        return rc

    @staticmethod
    def describe():
        '''Describes the rule syntax.
        '''
        print(r'''A "rule" describes a single action: find a new position, set a marker/register, display...
A "register" is a container holding a string with a single uppercase letter as name, e.g. 'A'
A "marker" is a position in the text with a lowercase letter as name, e.g. "a"
A "label" is named position in the rule list delimited by '%', e.g. '%eve_not_found%'
Legend:
    D is any printable ascii character (delimiter) except blank and ':', e.g. '/' or "X"
    R is a uppercase character A..Z (register name), e.g. "Z"
    m is a lowercase ascii char a..z (marker name), e.g. "f"
    G is a decimal number, e.g. 0 or 12 (group number)
    cursor: the current position
Rules:
a label:
    <label>:
a regular expression for searching forwards:
    >D<expression>D[<range>]<search-options>
    FD<expression>D[<range>]<search-options>
a regular expression for searching backwards:
    <D<expression>D[<range>]<search-options>
    BD<expression>D[<range>]<search-options>
<search-option>:
    <lines> search only in the next/previous <lines> lines, e.g. >/Joe/8
    :<cols> search only in the next/previous <cols> columns, e.g. </Eve/:30
    i ignore case
    e position is behind the found pattern. Example: lines: ["abcd"] rule: >/bc/e cursor: 0-3
an absolute line/column <line>:<col>
    line and col are numbers starting with 1, e.g. 24:2
a relative line/column count [+-]<line>:[+-]<col>
    line and col can be positive or negative or 0, negative means backwards
an anchor: <anchor>
    'bol': begin of line 'eol': end of line
    'bonl': begin of next line 'eonl': end of next line
    'bopl': end of previous line 'eopl': end of previous line
    'bof': begin of file 'eof': end of file
<command>:
    add-R-m   adds the content from marker m until cursor onto register R
    add-R-S   adds the content of register S onto the register R
    add-R:D<text>D[<text-options>]
        add the text onto register R
    cut-m     deletes the content from marker m to the cursor
    cut-R-m   deletes the content from marker m to the cursor and store it into register R
    expr-R:D<operator><operand>D
        calculate R = R <operator> <operand>
        <operator>:
            '+', '-', '*', '/', '%'
        <operand>:
            a decimal number or $<register>
        Examples: expr-A:"*32" expr-Z:"+$F"
    group-G-R stores the group G of the last regular expression into register R
    insert-R  inserts the content of register R at the cursor. cursor is moved behind the insertion.
    insert:D<content>D[<text-options>]
        put the <content> at the cursor. cursor is moved behind the insertion.
    jump-m   cursor is get from marker m
    jump:<label>   next rule to process is behind label <label>
    mark-m  sets the marker m
    print-m  displays the content from marker m to the cursor
    print-R  displays the register R
    print:D<text>D<text-option>
        displays the <text>
    replace:D<expression>D<replacement>D[<repl-options>]
        replaces <expression> with <replacement> in the current line
    replace-m:D<expression>D<replacement>D[<repl-options>]
        replaces <expression> with <replacement> from marker m to cursor
    replace-R:D<expression>D<replacement>D[<repl-options>]
        replaces <expression> with <replacement> in register R
        <repl-option>:
            c=<count> the count of replacements in one line, e.g. c=12
            e=<char> esc char used as prefix of the register placeholder
                example: e=$ Than $A will be replaced in <expression> and <replacement>
                by the content of register 'A'
    set-R-m stores the content from marker m to register R
    set-R:D<text>D[<text-options>]
        stores the <text> into register R, e.g. set-A:"Hi!"
    state-R:D<variable>D
        store the variable into register R, e.g. state-A row
        <variable>:
            row: the cursor line number (1..N)
            col: the cursor column (1..N)
            rows: number of lines
            size-R: the length of the content of register R
            rows-R: the number of lines in register R
            hits: the number of hits of the last replacement command
    swap-m    swaps cursor and marker m
    <text-option>:
        e=<char>
            esc char used as prefix of the register placeholder. More info see replace
<flow-control>:
    Note: "successful" means: a pattern is found (search) or reposition is inside the range etc.
    Note: default behaviour: success:continue and error:error
    success:<reaction>
        reaction is done if the rule is finished with success
    error:<reaction>
        reaction is done if the rule is finished without success
    <reaction>:
    continue
        continues with the next rule
    stop
        stop processing
    error
        stop processing with an error message
    %<label>%
        continue processing at label %<label>%
Examples:
>/jonny/:80i success:stop >/eve/4 error:stop print "eve found but not jonny"
    search "jonny" but only in the next 80 columns, ignore case
    stop if found. If not found: search "eve", but only 4 lines
    stop without error if not found. if found display "eve found but not jonny"
>/Address:/ error:error >/EMail:/s
    if "Address" is not found, the result is "not found"
    otherwise if "EMail" is found behind, the new Position is at "Email:" if not the new position is "Address"
10:0 error:%missingLines% >/Name:\s+/ label-n >/[A-Za-z ]+/ print-N-n success:stop;%missingLines% print:"less than 10 lines"
    searches for a name starting in line 10. Prints an informative message if line 10 does not exist
10:0 >/Firstname:\s+/e label-f >/[A-Za-z ]+/e store-F-n
print:"Full name: " print-F print:" " print-N
    this example searches for firstname and name below line 10 and display them
''')

    def parseAnchor(self, match):
        '''Parses and stores an anchor.
        'bol': begin of line 'eol': end of line
        'bonl': begin of next line 'eonl': end of next line
        'bopl': end of previous line 'eopl': end of previous line
        'bof': top of file 'eof': end of file
        @param match: the match of the regular expression
        '''
        rule = match.group(0)
        parts = rule.split(';')
        name = parts[0].strip()
        rule = Rule('anchor', name)
        return rule

    def parseCommand(self, rule):
        '''Parses a command.
        A command is a rule except searching or repositioning:
        @see RuleList.describe() for details.
        @param rule: the rule to parse
        @return: True: success False: error
        '''
        def isRegister(name):
            return name is not None and 'A' <= name[0] <= 'Z'

        def isMarker(name):
            return name is not None and 'a' <= name[0] <= 'z'

        def isGroup(name):
            return name is not None and '0' <= name[0] <= '9'

        def getText(param):
            text = None
            esc = None
            if param.startswith(':'):
                param = param[1:]
            if param != '':
                sep = param[0]
                ixEnd = param.find(sep, 1)
                if ixEnd > 0:
                    text = param[1:ixEnd]
                    rest = param[ixEnd + 1:]
                    if rest.startswith('e='):
                        esc = rest[2]
            return (text, esc)
        match = RuleList.__reCommand.match(rule)
        success = True
        if match is None:
            success = self.parseError('missing command name')
        else:
            name = match.group(1)
            var1 = None if match.lastindex < 2 else match.group(2)[1:]
            var2 = None if match.lastindex < 3 else match.group(3)[1]
            params = rule[len(match.group(0)):].lstrip()
            text, esc = getText(params)
            if name == 'add':
                # add-R-m
                # add-R-S
                # add-R D<text>D
                if isRegister(var2) and text is None:
                    self.appendCommand(name, CommandData(
                        register=var1, register2=var2))
                elif isMarker(var2) and text is None:
                    self.appendCommand(name, CommandData(
                        register=var1, marker=var2))
                elif var2 is None and text is not None:
                    self.appendCommand(name, CommandData(
                        register=var1, text=text, escChar=esc))
                else:
                    success = self.parseError(
                        'invalid syntax: add-R-m or add_R-S or add-R DtextD expected')
            elif name == 'cut':
                # cut-m
                # cut-R-m
                if isMarker(var1) and var2 is None and text is None:
                    self.appendCommand(name, CommandData(marker=var1))
                elif isRegister(var1) and isMarker(var2) and text is None:
                    self.appendCommand(name, CommandData(
                        marker=var2, register=var1))
                elif isRegister(var2) and isMarker(var1) and text is None:
                    self.appendCommand(name, CommandData(
                        marker=var1, register=var2))
                else:
                    success = self.parseError(
                        'invalid syntax: cut-m or cut-R-m expected')
            elif name == 'expr':
                # expr-R-S:D<operator>D
                #    calculate R = R <operator> S
                #    <operator>:
                #        '+', '-', '*', '/', '%'
                # expr-R:D<operator><constant>D
                #    calculate R = R <operator> <constant>
                matcher = RuleList.__reRuleExprParams.match(text)
                if matcher is None:
                    success = self.parseError(
                        '<operator><operand> expected, not "{}"'.format(text))
                elif isRegister(var1) and var2 is None and text is not None:
                    self.appendCommand(name, CommandData(
                        register=var1, text=text, escChar='$'))
                else:
                    success = self.parseError(
                        'invalid syntax: expr-R:"<operator><operand>" expected')
            elif name == 'group':
                # group-G-R
                if isGroup(var1) and isRegister(var2) and text is None:
                    self.appendCommand(name, CommandData(
                        group=int(var1), register=var2))
                else:
                    success = self.parseError(
                        'invalid syntax: group-G-R expected')
            elif name == 'insert':
                # insert-R
                # insert D<content>D
                if isRegister(var1) and var2 is None and text is None:
                    self.appendCommand(name, CommandData(register=var1))
                elif var1 is None and var2 is None:
                    self.appendCommand(
                        name, CommandData(text=text, escChar=esc))
                else:
                    success = self.parseError(
                        'invalid syntax: insert-R or insert DtextD expected')
            elif name == 'jump':
                # jump-m
                # jump-L
                if isMarker(var1) and var2 is None:
                    self.appendCommand(name, CommandData(marker=var1))
                elif var1 is None and params != '' and params.startswith(':%') and params[-1] == '%':
                    self.appendCommand(name, CommandData(text=params[1:]))
                else:
                    success = self.parseError(
                        'invalid syntax: jump-m or jump:<label> expected')
            elif name == 'mark':
                # mark-m
                if isMarker(var1) and var2 is None:
                    self.appendCommand(name, CommandData(marker=var1))
                else:
                    success = self.parseError(
                        'invalid syntax: mark-m expected')
            elif name == 'print':
                # print-m
                # print-R
                # print D<text>D display text
                if isMarker(var1) and var2 is None and text is None:
                    self.appendCommand(name, CommandData(marker=var1))
                elif isRegister(var1) and var2 is None and text is None:
                    self.appendCommand(name, CommandData(register=var1))
                elif var1 is None and var2 is None and text is not None:
                    self.appendCommand(
                        name, CommandData(text=text, escChar=esc))
                else:
                    success = self.parseError(
                        'invalid syntax: print-m or print-R or print DtextD expected"')
            elif name == 'replace':
                # replace-m D<expression>D<replacement>D
                # replace-R D<expression>D<replacement>D
                what = None
                if len(params) > 3:
                    sep = params[0]
                    ix1 = params.find(sep, 1)
                    ix2 = params.find(sep, ix1 + 1)
                    if ix1 < 0 or ix2 < 0:
                        what = params[1:ix1]
                        replacement = params[ix1 + 1:ix2]
                elif isMarker(var1) and var2 is None and what is not None:
                    self.appendCommand(name, CommandData(
                        marker=var1, text=what, text2=replacement))
                elif isRegister(var1) and var2 is None:
                    self.appendCommand(name, CommandData(
                        register=var1, text=what, text2=replacement))
                else:
                    success = self.parseError(
                        'invalid syntax: replace-m:DwhatDwithD or replace-R:DwhatDwithD expected')
            elif name == 'set':
                # set-R-m
                # set-R D<text>D
                if isRegister(var1) and isMarker(var2) and text is None:
                    self.appendCommand(name, CommandData(
                        register=var1, marker=var2))
                elif isRegister(var1) and var2 is None and text is not None:
                    self.appendCommand(name, CommandData(
                        register=var1, text=text, escChar=esc))
                else:
                    success = self.parseError(
                        'invalid syntax: set-R-m or set-R DtextD expected')
            elif name == 'swap':
                # swap-m
                if isMarker(var1) and var2 is None and text is None:
                    self.appendCommand(name, CommandData(marker=var1))
                else:
                    success = self.parseError(
                        'invalid syntax: swap-m expected')
            elif name == 'state':
                # state-R:D<variable>D
                var3 = None if text is None or RuleList.__reRuleStateParam.match(
                    text) is None else text
                if isRegister(var1) and var2 is None and var3 is not None:
                    self.appendCommand(name, CommandData(
                        register=var1, text=var3))
                else:
                    success = self.parseError(
                        'invalid syntax: state-R:"{row|col|rows|size-R|rows-R}" expected')
            else:
                success = self.parseError(
                    'unknown name {} in {}'.format(name, rule))
        return success

    def parseError(self, message):
        '''Logs a parser error.
        @param message: the error message
        @return: False (for chaining)
        '''
        self._logger.error('{}: {} rule: {}'.format(
            self._col, message, self._currentRule))
        self._errorCount += 1
        return False

    def parseRules(self, rules):
        '''Parses the rules given as string and put it in a prepared form into the list
        @param rules: the rules as string,
            Example: '>/logfile:/ -2:0 bol':
            search forwards "logfile:" go backward 2 line 0 column, go to begin of line
        '''
        self._col = 0
        rules = rules.lstrip('\t\n\r ;')
        while rules != '':
            currentRule = None
            lengthCommand = None
            ready = False
            if rules.startswith('replace'):
                lengthCommand = self.parseRuleReplace(rules)
                ready = True
            if not ready:
                match = RuleList.__reRule.match(rules)
                if match is None:
                    break
                else:
                    singleRule = self._currentRule = match.group(0)
                    lengthCommand = len(singleRule)
                    ruleType = singleRule[0]
                    if ruleType in ('<', '>', 'F', 'B'):
                        sep = singleRule[1]
                        ixEnd = singleRule.find(sep, 2)
                        param = SearchData()
                        msg = param.setData(
                            singleRule[2:ixEnd], singleRule[ixEnd + 1:])
                        if msg is not None:
                            self.parseError(msg)
                        if ruleType == 'F':
                            ruleType = '>'
                        elif ruleType == 'B':
                            ruleType = '<'
                        currentRule = Rule(ruleType, param)
                    elif ruleType == '%':
                        # label:
                        currentRule = Rule(ruleType, singleRule[0:-1])
                    elif '0' <= ruleType <= '9':
                        currentRule = Rule(
                            '+', [int(match.group(1)), int(match.group(2)), ':'])
                    elif ruleType in ('+', '-'):
                        # reposition:
                        factor = 1 if ruleType == '+' else -1
                        currentRule = Rule('+', [factor * int(match.group(1)),
                                                 factor * int(match.group(2)), '+'])
                    elif singleRule.startswith('bo') or singleRule.startswith('eo'):
                        currentRule = self.parseAnchor(match)
                    else:
                        self.parseCommand(singleRule)
            if currentRule is not None:
                self._rules.append(currentRule)
            if lengthCommand == 0:
                break
            self._col += lengthCommand
            rules = rules[lengthCommand:].lstrip('\t\n\r ;')
            matcher = RuleList.__reFlowControl.match(rules)
            if matcher is not None:
                controls = matcher.group(0)
                if self._rules:
                    self._rules[len(self._rules) -
                                1]._flowControl.setControl(controls)
                length = len(controls)
                self._col += length
                rules = rules[length:].lstrip('\t\n\r ;')
        if rules != '':
            self.parseError('not recognized input: ' + rules)
        rc = self._errorCount == 0
        return rc

    def parseRuleReplace(self, rules):
        '''Parses the 'replace' command.
        @param rules: the rules starting with 'replace'...
        @return: the length of the replace command
        '''
        rc = len('replace')
        # .......A.........  A..1.....12..2..3..3..4...4
        # replace(?:-[a-zA-Z])?:([^\s])(.+)\1(.*)\1(e=.)?')
        matcher = RuleList.__reRuleReplace.match(rules)
        if matcher is None:
            self.parseError('wrong syntax for replace: ' +
                            base.StringUtils.limitLength(rules, 40))
        else:
            name = None if rules[7] != '-' else rules[8]
            register = None if name is None or name > 'Z' else name
            marker = None if name is None or name < 'a' else name
            what = matcher.group(2)
            replacement = matcher.group(3)
            options = matcher.group(4)
            escChar = None if options is None or options == '' else options[2]
            param = CommandData(register, escChar, marker, what, replacement)
            rule = Rule('replace', param)
            self._rules.append(rule)
            rc = len(matcher.group(0))
        return rc

    def startTrace(self, filename, append=False):
        '''Starts tracing the rule execution.
        @param filename: the name of the trace file
        @param append: True: the trace will be appended
        '''
        self._fpTrace = open(filename, 'a' if append else 'w')
        self._fpTrace.write('= start\n')

    def stopTrace(self):
        '''Stops tracing the rule execution.
        @param filename: the name of the trace file
        @param append: True: the trace will be appended
        '''
        if self._fpTrace is not None:
            self._fpTrace.close()
            self._fpTrace = None

    def trace(self, index, after, state):
        '''Traces the state applying the current rule.
        @param index: index in _rules
        @param after: True: called after processing the rule
        @param state: the ProcessState instance
        '''
        rule = self._rules[index]
        rc = rule.state(after, state)
        if after:
            success = 'success' if state._success else 'error'
            self._fpTrace.write('{:03d}: {} {}\n    {}\n'.format(
                index, success, rule.toString(), rc))


class SearchData:
    '''Data for seaching (forward and backward)
    '''
    __reRange = re.compile(r':?(\d+)')

    def __init__(self):
        '''Constructor:
        @param igoreCase: searching 'a' finds 'A' and 'a'
        @param useEnd: True: the cursor is set behind the found string
            False: the cursor is set at the beginning of the found string
        '''
        self._ignoreCase = None
        self._useEnd = None
        self._rangeColumns = None
        self._rangeLines = None
        self._regExpr = None

    def setData(self, string, options):
        '''Sets the variables by inspecting the string and the options.
        @param string: the search string (regular expression)
        @param options: the search options, e.g. 'i' for ignore case
        @return: None: success otherwise: an error message
        '''
        rc = None
        match = SearchData.__reRange.match(options)
        if match is not None:
            if options.startswith(':'):
                self._rangeColumns = int(match.group(1))
            else:
                self._rangeLines = int(match.group(1))
            options = options[len(match.group(0)):]
        options = options.rstrip()
        while options != '':
            if options.startswith('i'):
                self._ignoreCase = True
            elif options.startswith('e'):
                self._useEnd = True
            else:
                rc = 'unknown search option: ' + options[0]
                break
            options = options[1:].rstrip()
        self._regExpr = re.compile(
            string, base.Const.IGNORE_CASE if self._ignoreCase else 0)
        return rc


class TextProcessor:
    '''A processor for finding/modifying text.
    '''

    def __init__(self, logger):
        self._filename = None
        self._lines = None
        self._logger = logger
        self._region = Region(self)
        self._cursor = Position(0, 0)
        self._endOfFile = Position(0, 0)
        self._beginOfFile = Position(0, 0)
        self._lastState = None
        self._hasChanged = False
        self._traceFile = None

    def cursor(self, mode='both'):
        '''Returns the cursor as pair (line, col), or the line or the column, depending on mode.
        @param mode: 'both', 'line' or 'col'
        @return [line, col], line or col, depending on mode
        '''
        rc = ([self._cursor._line, self._cursor._col] if mode == 'both' else
              (self._cursor._col if mode == 'col' else self._cursor._line))
        return rc

    def executeRules(self, rulesAsString, maxLoops=1):
        '''Compiles the rules and executes them.
        @param rules: a sequence of rules given as string
        @return True: success False: error
        '''
        ruleList = RuleList(self._logger)
        rc = ruleList.parseRules(rulesAsString)
        if rc:
            rc = ruleList.check()
        if rc:
            status = ProcessState(self._lines, self._region._startPosition, self._region._endPosition,
                                  self._cursor, self._logger, maxLoops)
            if self._traceFile is not None:
                ruleList.startTrace(self._traceFile, True)
            ruleList.apply(status)
            self._cursor.clone(status._cursor)
            self._lastState = status
            self._hasChanged = status._hasChanged
            rc = status._success
            if self._traceFile is not None:
                ruleList.stopTrace()
        return rc

    def findLine(self, pattern, firstIndex=0, lastIndex=None):
        '''Search a line matching a given regular expression.
        @param pattern: the pattern to find: a string or a RegExpr instance
        @param firstIndex: the index of the first line to inspect
        @param endIndex: exclusive: the index below the last line to inspect
        @return: -1: not found otherwise: the line index 0..N-1
        '''
        rc = -1
        regExpr = re.compile(pattern) if isinstance(pattern, str) else pattern
        ixLine = firstIndex
        last = min(lastIndex, len(self._lines)
                   ) if lastIndex is not None else len(self._lines)
        while ixLine < last:
            if regExpr.search(self._lines[ixLine]):
                rc = ixLine
                break
            ixLine += 1
        return rc

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
            self._lines = base.StringUtils.fromFile(filename, '\n')
        self.setEndOfFile(self._endOfFile)
        self._region._startPosition.clone(self._beginOfFile)
        self._region._endPosition.clone(self._endOfFile)
        self._cursor.clone(self._beginOfFile)
        return rc

    def replace(self, pattern, replacement, groupMarker=None, noRegExpr=False, countHits=False):
        '''Replaces all occurrences of what with a replacement in the current region.
        @param pattern: a regular expression of the string to search unless noRegExpr==True:
        @param replacement: what will be replaced with this. May contain a placeholder for groups in what
        @param groupMarker: None: no group placeholder otherwise: the prefix of a group placeholder
            example: groupMarker='$' then "$1" means the first group in what
        @param noRegExpr: True: pattern is a plain string, not a regular expression
        @param countHits: False: the result is the number of changed lines True: the result is the number of replacements
        @return: the number of replaced lines/replacements depending on countHits
        '''
        rc = 0
        if noRegExpr:
            for ix in range(len(self._lines)):
                if self._lines[ix].find(pattern) >= 0:
                    rc += self._lines[ix].count(pattern) if countHits else 1
                    self._lines[ix] = self._lines[ix].replace(
                        pattern, replacement)
        else:
            reWhat = re.compile(pattern) if isinstance(
                pattern, str) else pattern
            repl = replacement if groupMarker is None else replacement.replace(
                groupMarker, '\\')
            for ix in range(len(self._lines)):
                if reWhat.search(self._lines[ix]):
                    self._lines[ix], count = reWhat.subn(repl, self._lines[ix])
                    rc += count if countHits else 1
        return rc

    def setContent(self, content):
        '''Sets the lines without a file.
        @param content: the content for later processing: a string or a list of strings.
            the single string will be splitted by '\n'
        '''
        if isinstance(content, str):
            self._lines = content.split('\n')
        else:
            self._lines = content
        self.setEndOfFile(self._endOfFile)
        self._region._startPosition.clone(self._beginOfFile)
        self._region._endPosition.clone(self._endOfFile)
        self._cursor.clone(self._beginOfFile)

    def setEndOfFile(self, position):
        '''Sets the position to end of file.
        '''
        position._line = len(self._lines)
        position._col = 0

    def writeFile(self, filename=None, backupExtension=None):
        '''Reads a file into the internal buffer.
        @param filename: the file to write: if None _filename is taken
        @param backupExtension: None or: if the file already exists it will be renamed with this extension
                macros: '%date%' replace with the  current date %datetime%: replace with the date and time
                '%seconds%' replace with the seconds from epoche
        '''
        filename = self._filename if filename is None else filename
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
        base.StringUtils.toFile(filename, self._lines, '\n')


if __name__ == '__main__':
    pass
