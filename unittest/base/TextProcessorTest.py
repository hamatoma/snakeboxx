'''
Created on 12.04.2018

@author: hm
'''
from unittest.UnitTestCase import UnitTestCase
import base.TextProcessor

DEBUG = False

class TextProcessorTest(UnitTestCase):

    def __init__(self):
        UnitTestCase.__init__(self)
        self._trace = self.tempFile('rules.log', 'trace')

    def debugFlag(self):
        base.StringUtils.avoidWarning(self)
        return DEBUG

    def testBasics(self):
        if DEBUG: return
        processor = base.TextProcessor.TextProcessor(self._logger)
        processor._traceFile = self._trace
        self.assertIsEqual(0, processor._logger._errors)

    def testReplace(self):
        if DEBUG: return
        content = '''# simple example? complete example?
[Test]
intVar = 993
strVar = "abc $strVar"
'''
        processor = base.TextProcessor.TextProcessor(self._logger)
        processor.setContent(content)
        self.assertIsEqual(1, processor.replace('strVar', 'stringVar'))
        self.assertIsEqual('''# simple example? complete example?
[Test]
intVar = 993
stringVar = "abc $stringVar"
''', '\n'.join(processor._lines))

        processor.setContent(content)
        self.assertIsEqual(3, processor.replace('([a-z]+)Var', 'var_%1', '%', countHits=True))
        self.assertIsEqual('''# simple example? complete example?
[Test]
var_int = 993
var_str = "abc $var_str"
''', '\n'.join(processor._lines))

        processor.setContent(content)
        self.assertIsEqual(1, processor.replace('example?', 'sample?', noRegExpr=True))
        self.assertIsEqual('''# simple sample? complete sample?
[Test]
intVar = 993
strVar = "abc $strVar"
''', '\n'.join(processor._lines))

        processor.setContent(content)
        self.assertIsEqual(2, processor.replace('example?', 'sample?', noRegExpr=True, countHits=True))
        self.assertIsEqual('''# simple sample? complete sample?
[Test]
intVar = 993
strVar = "abc $strVar"
''', '\n'.join(processor._lines))

    def testReplaceEscActive(self):
        #if DEBUG: return
        content = '''123<newline>äöüß
<esc-char>xyz
'''
        processor = base.TextProcessor.TextProcessor(self._logger)
        processor.setContent(content)
        self.assertIsEqual(1, processor.replace('<newline>', '\\n', escActive=True))
        self.assertIsEqual(1, processor.replace('<esc-char>', '\\t\\u0045\\U00000046\\x47', escActive=True))
        current = '\n'.join(processor._lines)
        self.assertIsEqual('''123
äöüß
\tEFGxyz
''', current)

    def testRuleSearchForward(self):
        if DEBUG: return
        processor = base.TextProcessor.TextProcessor(self._logger)
        processor._traceFile = self._trace
        processor.setContent('Hello World!')
        processor.executeRules(r'>/world/i')
        self.assertIsEqual(0, processor.cursor('line'))
        self.assertIsEqual(6, processor.cursor('col'))

    def testRuleSearchBackward(self):
        if DEBUG: return
        processor = base.TextProcessor.TextProcessor(self._logger)
        processor._traceFile = self._trace
        processor.setContent('abc\nHello World!\nHi!')
        processor.executeRules(r'eof;</O/ie')
        self.assertIsEqual(1, processor.cursor('line'))
        self.assertIsEqual(8, processor.cursor('col'))

    def testRuleAnchors(self):
        if DEBUG: return
        processor = base.TextProcessor.TextProcessor(self._logger)
        processor._traceFile = self._trace
        processor.setContent('abc\nHello World!\nHi!')
        processor.executeRules(r'eof;eopl')
        self.assertIsEqual(3, processor.cursor('line'))
        self.assertIsEqual(0, processor.cursor('col'))

        processor.executeRules(r'eof;bof')
        self.assertIsEqual(0, processor.cursor('line'))
        self.assertIsEqual(0, processor.cursor('col'))

        processor.executeRules(r'bof;>/W/ bol')
        self.assertIsEqual(1, processor.cursor('line'))
        self.assertIsEqual(0, processor.cursor('col'))

        processor.executeRules(r'bof;>/W/;eol')
        self.assertIsEqual(2, processor.cursor('line'))
        self.assertIsEqual(0, processor.cursor('col'))

        processor.executeRules(r'bof >/W/;bonl')
        self.assertIsEqual(2, processor.cursor('line'))
        self.assertIsEqual(0, processor.cursor('col'))

        processor.executeRules(r'bof >/W/;eonl')
        self.assertIsEqual(3, processor.cursor('line'))
        self.assertIsEqual(0, processor.cursor('col'))

        processor.executeRules(r'bof >/W/;bopl')
        self.assertIsEqual(0, processor.cursor('line'))
        self.assertIsEqual(0, processor.cursor('col'))

        processor.executeRules(r'bof >/W/;eopl')
        self.assertIsEqual(1, processor.cursor('line'))
        self.assertIsEqual(0, processor.cursor('col'))

    def testRuleReposition(self):
        if DEBUG: return
        processor = base.TextProcessor.TextProcessor(self._logger)
        processor._traceFile = self._trace
        processor.setContent('abc\ndef\nHello World!\nHi\nGreetings!')
        processor.executeRules(r'bof >/W/ +2:1')
        self.assertIsEqual(2+2, processor.cursor('line'))
        self.assertIsEqual(6+1, processor.cursor('col'))

        processor.executeRules(r'bof >/W/ -2:1')
        self.assertIsEqual(2-2, processor.cursor('line'))
        self.assertIsEqual(6-1, processor.cursor('col'))

        processor.executeRules(r'bof 2:3')
        self.assertIsEqual(2, processor.cursor('line'))
        self.assertIsEqual(3, processor.cursor('col'))


    def testRuleMarkSwap(self):
        if DEBUG: return
        processor = base.TextProcessor.TextProcessor(self._logger)
        processor._traceFile = self._trace
        processor.setContent('abc\ndef\nHello World!\nHi\nGreetings!')
        processor.executeRules(r'bof >/W/;mark-b;-2:4;swap-b')
        self.assertIsEqual(2, processor.cursor('line'))
        self.assertIsEqual(6, processor.cursor('col'))

    def testRuleSet(self):
        if DEBUG: return
        processor = base.TextProcessor.TextProcessor(self._logger)
        processor._traceFile = self._trace
        processor.setContent('abc\ndef\nHello World!\nHi\nGreetings!')
        processor.executeRules(r'bof >/W/;mark-z;>/!/e;set-Q-z set-A:"!Q!BA"e=!')
        self.assertIsEqual('World!', processor._lastState.getRegister('Q'))
        self.assertIsEqual('World!A', processor._lastState.getRegister('A'))

    def testRuleAdd(self):
        if DEBUG: return
        processor = base.TextProcessor.TextProcessor(self._logger)
        processor._traceFile = self._trace
        processor.setContent('abc\ndef\nHello World!\nHi\nGreetings!')
        processor.executeRules(r'set-X:"+" bof >/W/ mark-z >/!/ set-A-z add-A:".!X."e=! add-A-A')
        self.assertIsEqual('World.+.World.+.', processor._lastState.getRegister('A'))

    def testRuleCut(self):
        if DEBUG: return
        processor = base.TextProcessor.TextProcessor(self._logger)
        processor._traceFile = self._trace

        processor.setContent('a\n123\nZ')
        processor.executeRules(r'bof >/2/;mark-b;+0:1;cut-b')
        self.assertIsEqual('a\n13\nZ', '\n'.join(processor._lines))

        processor.setContent('ab\n123\nZ')
        processor.executeRules(r'bof >/b/;mark-b;>/3/;cut-b-Q')
        self.assertIsEqual('a3\nZ', '\n'.join(processor._lines))
        self.assertIsEqual('b\n12', processor._lastState.getRegister('Q'))

    def testRuleInsert(self):
        if DEBUG: return
        processor = base.TextProcessor.TextProcessor(self._logger)
        processor._traceFile = self._trace

        processor.setContent('ab\n123\nZ')
        processor.executeRules(r'bof >/b/;mark-b;>/2/e;set-A-b;insert-A')
        self.assertIsEqual('ab\n12b\n123\nZ', '\n'.join(processor._lines))
        self.assertIsEqual(2, processor.cursor('line'))
        self.assertIsEqual(2, processor.cursor('col'))

        processor.setContent('a\n123\nZ')
        processor.executeRules(r'set-D:"$" set-E:":" bof >/2/;mark-f;insert:"?EFoo?D"e=?')
        self.assertIsEqual('a\n1:Foo$23\nZ', '\n'.join(processor._lines))
        self.assertIsEqual(1, processor.cursor('line'))
        self.assertIsEqual(6, processor.cursor('col'))

    def testRuleGroup(self):
        if DEBUG: return
        processor = base.TextProcessor.TextProcessor(self._logger)
        processor._traceFile = self._trace

        processor.setContent('ab\n123\nZ')
        processor.executeRules(r'bof >/(\d+)/;group-1-Z')
        self.assertIsEqual('123', processor._lastState.getRegister('Z'))

    def testRulePrint(self):
        if DEBUG: return
        processor = base.TextProcessor.TextProcessor(self._logger)
        processor._traceFile = self._trace

        processor.setContent('ab\n123\nZ')
        processor.executeRules(r'set-Z:"&" bof >/2/;mark-g;</b/;set-X-g;print-g;print:"%Z%Zreg-x: "e=%;print-X')
        self.assertTrue(processor._lastState is not None and processor._lastState._success)

    def testRuleReplace(self):
        if DEBUG: return
        processor = base.TextProcessor.TextProcessor(self._logger)
        processor._traceFile = self._trace

        processor.setContent('ab\n123\nZ')
        processor.executeRules(r'1:0 replace:/\d+/#/')
        self.assertTrue(processor._lastState is not None and processor._lastState._success)
        self.assertIsEqual('#', processor._lines[1])

        processor.setContent('ab')
        processor.executeRules(r'set-R:"a123b" replace-R:/\d+/#/')
        self.assertTrue(processor._lastState is not None and processor._lastState._success)
        self.assertIsEqual('a#b', processor._lastState.getRegister('R'))

        processor.setContent('abc\n123456\nxyz')
        processor.executeRules(r'>/2/ mark-a >/5/ replace-a:/\d/#/')
        self.assertTrue(processor._lastState is not None and processor._lastState._success)
        self.assertIsEqual('1###56', processor._lines[1])

        processor = base.TextProcessor.TextProcessor(self._logger)
        processor._traceFile = self._trace
        processor.setContent('abc\n123456\nxyz')
        processor.executeRules(r'>/c/ mark-a >/z/ replace-a:/./#/')
        self.assertTrue(processor._lastState is not None and processor._lastState._success)
        self.assertIsEqual('ab#\n######\n##z', '\n'.join(processor._lines))

    def testRuleJump(self):
        if DEBUG: return
        processor = base.TextProcessor.TextProcessor(self._logger)
        processor._traceFile = self._trace

        processor.setContent('ab\n123\nZ')
        processor.executeRules(r'bof >/b/ jump:%X% +2:1 %X%:')
        self.assertTrue(processor._lastState is not None and processor._lastState._success)
        self.assertIsEqual(0, processor.cursor('line'))
        self.assertIsEqual(1, processor.cursor('col'))

        processor.setContent('ab\n123\nZ')
        processor.executeRules(r'>/b/ mark-f >/3/ jump-f')
        self.assertTrue(processor._lastState is not None and processor._lastState._success)
        self.assertIsEqual(0, processor.cursor('line'))
        self.assertIsEqual(1, processor.cursor('col'))

    def testFlowControlOnSuccess(self):
        if DEBUG: return
        processor = base.TextProcessor.TextProcessor(self._logger)
        processor._traceFile = self._trace
        processor.setContent('ab\n123\nZ')
        processor.executeRules(r'bof;success:%x%; +1:0 %x%: +1:0')
        self.assertIsEqual(1, processor.cursor('line'))

    def testRuleExpr(self):
        if DEBUG: return
        processor = base.TextProcessor.TextProcessor(self._logger)
        processor._traceFile = self._trace

        processor.setContent('ab')
        # ............................................5..........2..........16..........5
        processor.executeRules(r'set-A:"5" expr-B:"+$A" expr-B:"-3" expr-B:"*8" expr-B:"/3"')
        self.assertTrue(processor._lastState is not None and processor._lastState._success)
        self.assertIsEqual('5', processor._lastState.getRegister('B'))

    def testRuleState(self):
        if DEBUG: return
        processor = base.TextProcessor.TextProcessor(self._logger)
        processor._traceFile = self._trace

        processor.setContent('ab\n1234567\n# end of file')
        # ............................................5..........2..........16..........5
        processor.executeRules(r'1:4 state-A:"row" state-B:"col" state-C:"rows" set-Z:"$A:$B:$C"e=$')
        self.assertTrue(processor._lastState is not None and processor._lastState._success)
        self.assertIsEqual('2:5:3', processor._lastState.getRegister('Z'))

    def testInsertOrReplace(self):
        #if DEBUG: return
        processor = base.TextProcessor.TextProcessor(self._logger)
        processor._traceFile = self._trace

        processor.setContent('#! /bin/sh\n  abc=123\nx')
        processor.insertOrReplace(r'\s*abc\s*=\s*\d+', '  abc=456')
        self.assertIsEqual(3, len(processor._lines))
        self.assertIsEqual('  abc=456', processor._lines[1])

        processor.insertOrReplace(r'\s*xyz\s*=\s*\d+', 'xyz=Hi', '/bin/sh')
        self.assertIsEqual(4, len(processor._lines))
        self.assertIsEqual('xyz=Hi', processor._lines[1])

        processor.insertOrReplace(r'\s*k\s*=\s*\d+', 'k=99', 'end of file', above=True)
        self.assertIsEqual(5, len(processor._lines))
        self.assertIsEqual('k=99', processor._lines[4])

        processor.insertOrReplace(r'LLL=', 'LLL=blub', 'not available', above=True)
        self.assertIsEqual(6, len(processor._lines))
        self.assertIsEqual('LLL=blub', processor._lines[5])

if __name__ == '__main__':
    #import sys;sys.argv = ['', 'Test.testName']
    tester = TextProcessorTest()
    tester.run()
