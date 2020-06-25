'''
Created on 12.04.2018

@author: hm
'''
from unittest.UnitTestCase import UnitTestCase
import base.TextProcessor

debug = False

class TextProcessorTest(UnitTestCase):

    def __init__(self):
        UnitTestCase.__init__(self)
        self._trace = self.tempFile('rules.log', 'trace')

    def testBasics(self):
        if debug: return
        processor = base.TextProcessor.TextProcessor(self._logger)
        processor._traceFile = self._trace
        self.assertEquals(0, processor._logger._errors)

    def testReplace(self):
        if debug: return
        content = '''# simple example? complete example?
[Test]
intVar = 993
strVar = "abc $strVar"
'''
        processor = base.TextProcessor.TextProcessor(self._logger)
        processor.setContent(content)
        self.assertEquals(1, processor.replace('strVar', 'stringVar'))
        self.assertEquals('''# simple example? complete example?
[Test]
intVar = 993
stringVar = "abc $stringVar"
''', '\n'.join(processor._lines))

        processor.setContent(content)
        self.assertEquals(3, processor.replace('([a-z]+)Var', 'var_%1', '%', countHits=True))
        self.assertEquals('''# simple example? complete example?
[Test]
var_int = 993
var_str = "abc $var_str"
''', '\n'.join(processor._lines))

        processor.setContent(content)
        self.assertEquals(1, processor.replace('example?', 'sample?', noRegExpr=True))
        self.assertEquals('''# simple sample? complete sample?
[Test]
intVar = 993
strVar = "abc $strVar"
''', '\n'.join(processor._lines))

        processor.setContent(content)
        self.assertEquals(2, processor.replace('example?', 'sample?', noRegExpr=True, countHits=True))
        self.assertEquals('''# simple sample? complete sample?
[Test]
intVar = 993
strVar = "abc $strVar"
''', '\n'.join(processor._lines))

    def testRuleSearchForward(self):
        if debug: return
        processor = base.TextProcessor.TextProcessor(self._logger)
        processor._traceFile = self._trace
        processor.setContent('Hello World!')
        processor.executeRules(r'>/world/i')
        self.assertEquals(0, processor.cursor('line'))
        self.assertEquals(6, processor.cursor('col'))

    def testRuleSearchBackward(self):
        if debug: return
        processor = base.TextProcessor.TextProcessor(self._logger)
        processor._traceFile = self._trace
        processor.setContent('abc\nHello World!\nHi!')
        processor.executeRules(r'eof;</O/ie')
        self.assertEquals(1, processor.cursor('line'))
        self.assertEquals(8, processor.cursor('col'))

    def testRuleAnchors(self):
        if debug: return
        processor = base.TextProcessor.TextProcessor(self._logger)
        processor._traceFile = self._trace
        processor.setContent('abc\nHello World!\nHi!')
        processor.executeRules(r'eof;eopl')
        self.assertEquals(3, processor.cursor('line'))
        self.assertEquals(0, processor.cursor('col'))

        processor.executeRules(r'eof;bof')
        self.assertEquals(0, processor.cursor('line'))
        self.assertEquals(0, processor.cursor('col'))

        processor.executeRules(r'bof;>/W/ bol')
        self.assertEquals(1, processor.cursor('line'))
        self.assertEquals(0, processor.cursor('col'))

        processor.executeRules(r'bof;>/W/;eol')
        self.assertEquals(2, processor.cursor('line'))
        self.assertEquals(0, processor.cursor('col'))

        processor.executeRules(r'bof >/W/;bonl')
        self.assertEquals(2, processor.cursor('line'))
        self.assertEquals(0, processor.cursor('col'))

        processor.executeRules(r'bof >/W/;eonl')
        self.assertEquals(3, processor.cursor('line'))
        self.assertEquals(0, processor.cursor('col'))

        processor.executeRules(r'bof >/W/;bopl')
        self.assertEquals(0, processor.cursor('line'))
        self.assertEquals(0, processor.cursor('col'))

        processor.executeRules(r'bof >/W/;eopl')
        self.assertEquals(1, processor.cursor('line'))
        self.assertEquals(0, processor.cursor('col'))

    def testRuleReposition(self):
        if debug: return
        processor = base.TextProcessor.TextProcessor(self._logger)
        processor._traceFile = self._trace
        processor.setContent('abc\ndef\nHello World!\nHi\nGreetings!')
        processor.executeRules(r'bof >/W/ +2:1')
        self.assertEquals(2+2, processor.cursor('line'))
        self.assertEquals(6+1, processor.cursor('col'))

        processor.executeRules(r'bof >/W/ -2:1')
        self.assertEquals(2-2, processor.cursor('line'))
        self.assertEquals(6-1, processor.cursor('col'))

        processor.executeRules(r'bof 2:3')
        self.assertEquals(2, processor.cursor('line'))
        self.assertEquals(3, processor.cursor('col'))


    def testRuleMarkSwap(self):
        if debug: return
        processor = base.TextProcessor.TextProcessor(self._logger)
        processor._traceFile = self._trace
        processor.setContent('abc\ndef\nHello World!\nHi\nGreetings!')
        processor.executeRules(r'bof >/W/;mark-b;-2:4;swap-b')
        self.assertEquals(2, processor.cursor('line'))
        self.assertEquals(6, processor.cursor('col'))

    def testRuleSet(self):
        if debug: return
        processor = base.TextProcessor.TextProcessor(self._logger)
        processor._traceFile = self._trace
        processor.setContent('abc\ndef\nHello World!\nHi\nGreetings!')
        processor.executeRules(r'bof >/W/;mark-z;>/!/e;set-Q-z set-A:"!Q!BA"e=!')
        self.assertEquals('World!', processor._lastState.getRegister('Q'))
        self.assertEquals('World!A', processor._lastState.getRegister('A'))

    def testRuleAdd(self):
        if debug: return
        processor = base.TextProcessor.TextProcessor(self._logger)
        processor._traceFile = self._trace
        processor.setContent('abc\ndef\nHello World!\nHi\nGreetings!')
        processor.executeRules(r'set-X:"+" bof >/W/ mark-z >/!/ set-A-z add-A:".!X."e=! add-A-A')
        self.assertEquals('World.+.World.+.', processor._lastState.getRegister('A'))

    def testRuleCut(self):
        if debug: return
        processor = base.TextProcessor.TextProcessor(self._logger)
        processor._traceFile = self._trace

        processor.setContent('a\n123\nZ')
        processor.executeRules(r'bof >/2/;mark-b;+0:1;cut-b')
        self.assertEquals('a\n13\nZ', '\n'.join(processor._lines))

        processor.setContent('ab\n123\nZ')
        processor.executeRules(r'bof >/b/;mark-b;>/3/;cut-b-Q')
        self.assertEquals('a3\nZ', '\n'.join(processor._lines))
        self.assertEquals('b\n12', processor._lastState.getRegister('Q'))

    def testRuleInsert(self):
        if debug: return
        processor = base.TextProcessor.TextProcessor(self._logger)
        processor._traceFile = self._trace

        processor.setContent('ab\n123\nZ')
        processor.executeRules(r'bof >/b/;mark-b;>/2/e;set-A-b;insert-A')
        self.assertEquals('ab\n12b\n123\nZ', '\n'.join(processor._lines))
        self.assertEquals(2, processor.cursor('line'))
        self.assertEquals(2, processor.cursor('col'))

        processor.setContent('a\n123\nZ')
        processor.executeRules(r'set-D:"$" set-E:":" bof >/2/;mark-f;insert:"?EFoo?D"e=?')
        self.assertEquals('a\n1:Foo$23\nZ', '\n'.join(processor._lines))
        self.assertEquals(1, processor.cursor('line'))
        self.assertEquals(6, processor.cursor('col'))

    def testRuleGroup(self):
        if debug: return
        processor = base.TextProcessor.TextProcessor(self._logger)
        processor._traceFile = self._trace

        processor.setContent('ab\n123\nZ')
        processor.executeRules(r'bof >/(\d+)/;group-1-Z')
        self.assertEquals('123', processor._lastState.getRegister('Z'))

    def testRulePrint(self):
        if debug: return
        processor = base.TextProcessor.TextProcessor(self._logger)
        processor._traceFile = self._trace

        processor.setContent('ab\n123\nZ')
        processor.executeRules(r'set-Z:"&" bof >/2/;mark-g;</b/;set-X-g;print-g;print:"%Z%Zreg-x: "e=%;print-X')
        self.assertTrue(processor._lastState is not None and processor._lastState._success)

    def testRuleReplace(self):
        if debug: return
        processor = base.TextProcessor.TextProcessor(self._logger)
        processor._traceFile = self._trace

        processor.setContent('ab\n123\nZ')
        processor.executeRules(r'1:0 replace:/\d+/#/')
        self.assertTrue(processor._lastState is not None and processor._lastState._success)
        self.assertEquals('#', processor._lines[1])

        processor.setContent('ab')
        processor.executeRules(r'set-R:"a123b" replace-R:/\d+/#/')
        self.assertTrue(processor._lastState is not None and processor._lastState._success)
        self.assertEquals('a#b', processor._lastState.getRegister('R'))

        processor.setContent('abc\n123456\nxyz')
        processor.executeRules(r'>/2/ mark-a >/5/ replace-a:/\d/#/')
        self.assertTrue(processor._lastState is not None and processor._lastState._success)
        self.assertEquals('1###56', processor._lines[1])

        processor = base.TextProcessor.TextProcessor(self._logger)
        processor._traceFile = self._trace
        processor.setContent('abc\n123456\nxyz')
        processor.executeRules(r'>/c/ mark-a >/z/ replace-a:/./#/')
        self.assertTrue(processor._lastState is not None and processor._lastState._success)
        self.assertEquals('ab#\n######\n##z', '\n'.join(processor._lines))

    def testRuleJump(self):
        if debug: return
        processor = base.TextProcessor.TextProcessor(self._logger)
        processor._traceFile = self._trace

        processor.setContent('ab\n123\nZ')
        processor.executeRules(r'bof >/b/ jump:%X% +2:1 %X%:')
        self.assertTrue(processor._lastState is not None and processor._lastState._success)
        self.assertEquals(0, processor.cursor('line'))
        self.assertEquals(1, processor.cursor('col'))

        processor.setContent('ab\n123\nZ')
        processor.executeRules(r'>/b/ mark-f >/3/ jump-f')
        self.assertTrue(processor._lastState is not None and processor._lastState._success)
        self.assertEquals(0, processor.cursor('line'))
        self.assertEquals(1, processor.cursor('col'))

    def testFlowControlOnSuccess(self):
        if debug: return
        processor = base.TextProcessor.TextProcessor(self._logger)
        processor._traceFile = self._trace
        processor.setContent('ab\n123\nZ')
        processor.executeRules(r'bof;success:%x%; +1:0 %x%: +1:0')
        self.assertEquals(1, processor.cursor('line'))

    def testRuleExpr(self):
        if debug: return
        processor = base.TextProcessor.TextProcessor(self._logger)
        processor._traceFile = self._trace

        processor.setContent('ab')
        # ............................................5..........2..........16..........5
        processor.executeRules(r'set-A:"5" expr-B:"+$A" expr-B:"-3" expr-B:"*8" expr-B:"/3"')
        self.assertTrue(processor._lastState is not None and processor._lastState._success)
        self.assertEquals('5', processor._lastState.getRegister('B'))

    def testRuleState(self):
        #if debug: return
        processor = base.TextProcessor.TextProcessor(self._logger)
        processor._traceFile = self._trace

        processor.setContent('ab\n1234567\nx')
        # ............................................5..........2..........16..........5
        processor.executeRules(r'1:4 state-A:"row" state-B:"col" state-C:"rows" set-Z:"$A:$B:$C"e=$')
        self.assertTrue(processor._lastState is not None and processor._lastState._success)
        self.assertEquals('2:5:3', processor._lastState.getRegister('Z'))

if __name__ == '__main__':
    #import sys;sys.argv = ['', 'Test.testName']
    tester = TextProcessorTest()
    tester.run()
