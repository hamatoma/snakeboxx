'''
Administrates a time controlled list of tasks.

Created: 2020.06.24
@license: CC0 https://creativecommons.org/publicdomain/zero/1.0
@author: hm
'''
import time
import random


class TaskInfo:
    '''Abstract class of a task.
    Override process().
    '''
    #@abstractmethod

    def process(self, sliceInfo):
        '''Processes the task.
        @param sliceInfo: the current slice
        '''
        raise Exception('TaskInfo.process not overriden')


class SliceInfo:
    '''Holds the information over an entry in the time table.
    '''

    def __init__(self, taskInfo, scheduler, countCalls=1, interval=60, precision=0.1):
        '''Constructor.
        @param taskInfo: the task to do
        @param scheduler: the parent
        @param countCalls: The task has to be repeated so many times
        @param interval: the time between two process
        @param precision: a factor (< 1.0) of interval to spread the processing timestamps
        '''
        self._scheduler = scheduler
        self._interval = interval
        self._precision = precision
        # None: forever otherwise: the number of rounds in the scheduler
        self._countCalls = countCalls
        self._taskInfo = taskInfo
        self._id = scheduler.nextId()
        self._nextCall = None

    def calculateNextTime(self, interval=None, precision=None):
        '''Calculates the timepoint of the next call.
        @param interval: None: _interval is taken otherwise: the amount of seconds to the next processing
        @param precision: None: self._precision is taken otherwise: a factor of interval to spread processing timestamps
        '''
        if interval is None:
            interval = self._interval
        if precision is None:
            precision = self._precision
        if precision == 0.0:
            self._nextCall = time.time() + interval
        else:
            halfRange = interval * precision
            rand = self._scheduler._random.randrange(0, 123456) / 123456.0
            offset = interval + 2 * halfRange * rand - halfRange
            self._nextCall = time.time() + offset


class Scheduler:
    '''Administrates a time controlled list of tasks.
    Needed: overriding process()
    '''

    def __init__(self, logger):
        '''Constructor.
        @param logger: for messages
        '''
        self._slices = []
        self._logger = logger
        self._random = random.Random()
        self._currentId = 0

    def insertSlice(self, sliceInfo, startInterval=None, startPrecision=None):
        '''Inserts a slice info into the time ordered slice list.
        @param sliceInfo: the slice to insert
        @param startInterval: None: sliceInfo._interval is taken. Otherwise: the amount of seconds to the next processing
        @param startPrecision: a factor (< 1.0) of startInterval to spread the processing timestamps
        '''
        ix = len(self._slices) - 1
        sliceInfo.calculateNextTime(startInterval, startPrecision)
        if sliceInfo._id == 2:
            sliceInfo._id = 2
        while ix >= 0 and self._slices[ix]._nextCall > sliceInfo._nextCall:
            ix -= 1
        self._slices.insert(ix + 1 if ix >= 0 else 0, sliceInfo)

    def check(self):
        '''Checks whether the next task should be processed and returns it.
        @return: None: no processing is needed otherwise: the slice which must be processed
        '''
        sliceInfo = None
        if self._slices:
            now = time.time()
            found = self._slices[0]._nextCall <= now
            if found:
                sliceInfo = self._slices[0]
                del self._slices[0]
        return sliceInfo

    def checkAndProcess(self):
        '''Checks whether the next task should be processed and processes it.
        @return: true: processing has been done
        '''
        sliceInfo = self.check()
        if sliceInfo is not None:
            sliceInfo._taskInfo.process(sliceInfo)
            if sliceInfo._countCalls is not None:
                sliceInfo._countCalls -= 1
            if sliceInfo._countCalls is None or sliceInfo._countCalls > 0:
                sliceInfo.calculateNextTime()
                self.insertSlice(sliceInfo)
        return sliceInfo is not None

    def nextId(self):
        '''Returns the next id for a slice.
        @return: the next id
        '''
        self._currentId += 1
        return self._currentId


if __name__ == '__main__':
    pass
