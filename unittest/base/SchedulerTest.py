'''
Created on 12.04.2018

@author: hm
'''
from unittest.UnitTestCase import UnitTestCase
import base.MemoryLogger
import base.Scheduler

class TestTaskInfo (base.Scheduler.TaskInfo):
    def __init__(self):
        self._count = 0
    def process(self, sliceInfo):
        self._count += 1

class SchedulerTest(UnitTestCase):

    def testBasics(self):
        logger = base.MemoryLogger.MemoryLogger()
        scheduler = base.Scheduler.Scheduler(logger)
        taskInfo = TestTaskInfo()
        sliceInfo = base.Scheduler.SliceInfo(taskInfo, scheduler)
        scheduler.insertSlice(sliceInfo, 2, 0.0)
        sliceInfo = base.Scheduler.SliceInfo(taskInfo, scheduler)
        scheduler.insertSlice(sliceInfo, 1, 0.0)
        self.assertEquals(len(scheduler._slices), 2)
        self.assertEquals(scheduler._slices[0]._id, 2)
        self.assertEquals(scheduler._slices[1]._id, 1)

        scheduler._slices[0]._nextCall -= 2
        slide1 = scheduler.check()
        self.assertEquals(slide1._id, 2)
        self.assertEquals(len(scheduler._slices), 1)
        self.assertEquals(scheduler._slices[0]._id, 1)

        scheduler._slices[0]._nextCall -= 3
        self.assertTrue(scheduler.checkAndProcess())
        self.assertEquals(len(scheduler._slices), 0)

        self.assertEquals(taskInfo._count, 1)

if __name__ == '__main__':
    #import sys;sys.argv = ['', 'Test.testName']
    tester = SchedulerTest()
    tester.run()
