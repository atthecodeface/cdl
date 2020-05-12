#!/usr/bin/env python
import sys, os, unittest
import cdl.sim

class simple_event_test_harness(cdl.sim.th):
    def __init__(self, clocks:cdl.sim.ClockDict, inputs:cdl.sim.InputDict, outputs:cdl.sim.OutputDict):
        cdl.sim.th.__init__(self, clocks, inputs, outputs)
    def run(self)->None:
        self.e1 = self.event()
        self.e2 = self.event()
        print("Regression batch arg simple event test - *SL_EXEC_FILE TEST*")
        self.bfm_wait(1)
        self.spawn(self.second_thread)
        print("First thread start")
        self.e1.reset()
        self.e1.fire()
        self.e2.wait()
        print("First thread continues")
        self.passtest(0, "Test succeeded")
    def second_thread(self)->None:
        print("Second thread start")
        self.e2.reset()
        self.e1.wait()
        print("Second thread continues")
        self.e2.fire()

class simple_event_hw(cdl.sim.hw):
    def __init__(self)->None:
        self.system_clock = cdl.sim.clock(0, 1, 1)
        self.th = simple_event_test_harness(clocks={"clk": self.system_clock},
                                            inputs={},
                                            outputs={}
                                            )

        cdl.sim.hw.__init__(self, self.th, self.system_clock)

class TestEvent(unittest.TestCase):
    def test_simple_event(self)->None:
        hw = simple_event_hw()
        hw.reset()
        hw.step(50)
        self.assertTrue(hw.passed())

