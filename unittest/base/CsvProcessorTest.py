'''
Created on 12.04.2018

@author: hm
'''
from unittest.UnitTestCase import UnitTestCase
import base.StringUtils
import base.CsvProcessor

DEBUG = False

class CsvProcessorTest(UnitTestCase):

    def __init__(self):
        UnitTestCase.__init__(self)
        self._fn = self.tempFile('test.csv', 'csvprocessor')
        self.buildData()

    def debugFlag(self):
        base.StringUtils.avoidWarning(self)
        return DEBUG

    def buildData(self):
        base.StringUtils.toFile(self._fn, '''id,name,age
1,Jonny,22
2,Eve,22
3,Eve,
''')

    def testBasics(self):
        if DEBUG: return
        processor = base.CsvProcessor.CsvProcessor(self._logger)
        self.assertIsEqual(0, processor._logger._errors)

    def testRead(self):
        if DEBUG: return
        processor = base.CsvProcessor.CsvProcessor(self._logger)
        processor.readFile(self._fn)
        self.assertIsEqual('id;name;age', ';'.join(processor._colNames))
        self.assertIsEqual(3, len(processor._rows))
        self.assertIsEqual(3, len(processor._rows[0]))
        self.assertIsEqual(3, len(processor._rows[1]))
        self.assertIsEqual('1', processor._rows[0][0])
        self.assertIsEqual('Jonny', processor._rows[0][1])
        self.assertIsEqual('22', processor._rows[0][2])
        self.assertIsEqual(3, processor._maxCols)
        self.assertIsEqual(3, processor._minCols)
        self.assertIsEqual(2, processor._rowMinCols)
        self.assertIsEqual(2, processor._rowMaxCols)

    def testSetFilterIndexes(self):
        if DEBUG: return
        processor = base.CsvProcessor.CsvProcessor(self._logger)
        processor.readFile(self._fn)
        processor.setFilterIndexes([2, '0'])
        self.assertIsEqual(2, len(processor._indexes))
        self.assertIsEqual(0, processor._indexes[0])
        self.assertIsEqual(2, processor._indexes[1])

    def testSetFilterCols(self):
        if DEBUG: return
        processor = base.CsvProcessor.CsvProcessor(self._logger)
        processor.readFile(self._fn)
        processor.setFilterCols(['na*', 'a*'])
        self.assertIsEqual(2, len(processor._indexes))
        self.assertIsEqual(1, processor._indexes[0])
        self.assertIsEqual(2, processor._indexes[1])

    def testInfoSummary(self):
        #if DEBUG: return
        processor = base.CsvProcessor.CsvProcessor(self._logger)
        processor.readFile(self._fn)
        processor.setFilterIndexes([0, 1, 2])
        processor.info('summary')
        self._logger.contains('= su')
        self._logger.contains("0 \"id\": <class 'int'>")
        self._logger.contains("1 \"name\": <class 'str'>")
        self._logger.contains("2 \"age\": <class 'int'> hasEmpty")

    def testInfoUniqueMinMax(self):
        if DEBUG: return
        processor = base.CsvProcessor.CsvProcessor(self._logger)
        processor.readFile(self._fn)
        processor.setFilterIndexes([0, 1, 2])
        processor.info('unique,min,max')
        self._logger.contains('eve')

    def testSetColumnOrder(self):
        if DEBUG: return
        processor = base.CsvProcessor.CsvProcessor(self._logger)
        processor.readFile(self._fn)
        processor.setColumnOrder(['a*', '*d', 'n*e'])
        self.assertIsEqual(3, len(processor._columnOrder))
        self.assertIsEqual(2, processor._columnOrder[0])
        self.assertIsEqual(0, processor._columnOrder[1])
        self.assertIsEqual(1, processor._columnOrder[2])

    def testWriteFile(self):
        if DEBUG: return
        processor = base.CsvProcessor.CsvProcessor(self._logger)
        processor.readFile(self._fn)
        processor.setColumnOrder(['a*', '*d', 'n*e'])
        processor.writeFile(self._fn, '.bak', ';')
        self.assertFileContent('''id,name,age
1,Jonny,22
2,Eve,22
3,Eve,
''', self._fn.replace('.csv', '.bak'))
        self.assertFileContent('''age;id;name
22;1;Jonny
22;2;Eve
;3;Eve
''', self._fn)

    def testExecute(self):
        if DEBUG: return
        processor = base.CsvProcessor.CsvProcessor(self._logger)
        processor.readFile(self._fn)
        fn2 = self._fn.replace('.csv', '.bak')
        self.ensureFileDoesNotExist(fn2)
        processor.execute('''#test_of_execute:
set-filter:id
info:summary,max
set-order:ag*,id,name
write:,semicolon,.bak
''')
        self.assertFileContent('''age;id;name
22;1;Jonny
22;2;Eve
;3;Eve
''', self._fn)

    def testAddColumn(self):
        if DEBUG: return
        processor = base.CsvProcessor.CsvProcessor(self._logger)
        self.buildData()
        processor.readFile(self._fn)
        fn2 = self.tempFile('with_no.csv', 'csv')
        processor.addColumn('No', 1, 33, 44)
        processor.addColumn('No2', 99, 1, 2)
        processor.writeFile(fn2)
        self.assertFileContent('''id,No,name,age,No2
1,33,Jonny,22,1
2,44,Eve,22,2
3,55,Eve,,3
''', fn2)

    def testExecuteInfoMultiple(self):
        #if DEBUG: return
        processor = base.CsvProcessor.CsvProcessor(self._logger)
        processor.readFile(self._fn)
        fn2 = self._fn.replace('.csv', '.bak')
        self.ensureFileDoesNotExist(fn2)
        processor.execute('''#test_of_execute:
set-filter:age
info:multiple
''')
        self._logger.contains('22: 2')

    def testExecuteInfoMaxLength(self):
        #if DEBUG: return
        processor = base.CsvProcessor.CsvProcessor(self._logger)
        processor.readFile(self._fn)
        fn2 = self._fn.replace('.csv', '.bak')
        self.ensureFileDoesNotExist(fn2)
        processor.execute('''#test_of_execute:
set-filter:name
info:max-length
set-filter:id
info:max
''')
        self._logger.contains('22: 2')


if __name__ == '__main__':
    #import sys;sys.argv = ['', 'Test.testName']
    tester = CsvProcessorTest()
    tester.run()
