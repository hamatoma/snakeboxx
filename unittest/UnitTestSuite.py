'''
Created on 22.04.2018

@author: hm
'''

import os.path
import re
import sys
import importlib

sys.path.insert(0, '/usr/share/snakeboxx')

class UnitTestSuite:
    '''Tests a group of test cases.
    '''
    def __init__(self, name):
        '''Constructor.
        @param name: name of the suite (for logging)
        '''
        self._name = name
        self._testCases = []
        self._imports = []
        self._base = '/home/ws/py/snakeboxx/'
        self._summary = []
        self._debugList = []

    def addByPattern(self, relPath, pattern = r'.*[.]py$'):
        '''Adds the test cases given by a directory and a filename pattern (of modules, not test cases).
        @param relPath: the directory containing the modules to test, relative to the parent of 'unittest'
        @param pattern: a regular expression for selecting the modules
        '''
        basePath = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        path = basePath + os.sep + relPath
        files = os.listdir(path)
        regExpr = re.compile(pattern)
        for node in files:
            if regExpr.match(node):
                self.addFromFile(relPath, node)

    def addFromFile(self, package, node):
        '''Adds a test case given by the name of the module.
        @param package: the package name of the module
        @param node: the file containing the module
        '''
        moduleName = node[0:-3] + 'Test'
        #moduleWithPackage = package + '.' + moduleName
        #self._imports.append([moduleName, moduleWithPackage])
        full = self._base + 'unittest/' + package + '/' + moduleName + '.py'
        if os.path.exists(full):
            self._imports.append([moduleName, package])
            self._testCases.append(moduleName)

    def addList(self, testCases):
        '''Adds a list of test cases for inspecting.
        @param testCases: a list of class names
        '''
        for item in testCases:
            if item not in self._testCases:
                self._testCases.append(item)

    def instantiate(self, clazz ):
        '''Instantiate a class object given by name
        @param clazz: the classes name
        @return the instance
        '''
        parts = clazz.split('.')
        moduleName = ".".join(parts[:-1])
        className = parts[-1]
        module = importlib.import_module(moduleName)
        instance = getattr(module, className)
        return instance

    def process(self):
        '''Instantiate the classes collected in _imports and call the class.run() method.
        '''
        tests = []
        for name, package in self._imports:
            if not name.startswith('__'):
                if name.find('AppTest') > 0:
                    package = 'app'
                instance = self.instantiate('unittest.' + package + '.' + name + '.' + name)()
                clazz = self.instantiate('unittest.' + package + '.' + name + '.' + name)
                tests.append((clazz, instance))
        for (clazz, instance) in tests:
            clazz.__init__(instance)
            clazz.setInTestSuite(instance, True)
            clazz.run(instance)
            if instance.debugFlag():
                self._debugList.append(clazz.__name__)
            self._summary.append(clazz.getSummary(instance))

    def summary(self):
        print('=== Summary ===')
        errors = ''
        countErrors = 0
        asserts = 0
        units = 0
        for item in self._summary:
            print(item)
            units += 1
            # 0...1....2...............3..4.........5....6
            # === unit LinuxUtilsTest: 84 assert(s) with 0 error(s)
            parts = item.split()
            asserts += int(parts[3])
            countErrors += int(parts[6])
            if parts[6] != '0':
                errors += '{}: {} '.format(parts[2][0:-1], parts[6])
        if errors != '':
            print ('=== {} units with {} assert(s) and {} error(s) in:\n{}'.format(
                units, asserts, countErrors, errors))
        if len(self._debugList) > 0:
            names = 'Debug flag is set in:' + ' '.join(self._debugList)
            print(names)


if __name__ == '__main__':
    paths = sys.path
    suite = UnitTestSuite('base')
    suite.addByPattern('base')
    suite.addByPattern('net')
    suite.addByPattern('app')
    suite.process()
    suite.summary()