#a Imports
from cdl.sim import ThExecFile
from cdl.sim import HardwareThDut, OptionsDict
from cdl.sim import TestCase

import os, inspect
class xxx: pass
module_root = os.path.dirname(inspect.getfile(xxx))

#c RamThef
class RamThef(ThExecFile):
    th_name = "ram_burst test harness"
    def __init__(self, use_verilated, **kwargs):
        ThExecFile.__init__(self,**kwargs)
        self.use_verilated = use_verilated
        pass
    def do_count(self, count, addr):
        self.signal__count.drive(count)
        self.signal__addr.drive(addr)
        self.signal__go.drive(1)
        self.bfm_wait(1)
        self.signal__go.drive(0)
        self.signal__done.wait_for_value(1)
        self.verbose.info("%d %d"%(self.signal__done.value(), self.signal__data.value()))
        data = self.signal__data.value()
        if self.use_verilated:
            data = ((data>>8) + (data<<8)) & 0xffff
            pass
        return data
    def run(self) -> None:
        self.signal__go.drive(0)
        self.signal__count.drive(0)
        self.signal__addr.drive(0)
        self.bfm_wait(10)
        d = self.do_count(5,0)
        self.compare_expected("Count of 10..6 should be 40",d,10+9+8+7+6)
        self.bfm_wait(5)
        d = self.do_count(5,5)
        self.compare_expected("Count of 5..1 should be 15",d,15)
        self.bfm_wait(1)
        self.passtest("Test succeeded")
        pass

#c DutHardware
class DutHardware(HardwareThDut):
    clock_desc = [("clk",(0,1,1)),
    ]
    reset_desc = {"name":"reset_n", "init_value":0, "wait":5}
    module_name = "ram_burst"
    dut_inputs = {"go":1, "count":8, "addr":16 }
    dut_outputs = {"data":16, "done":1 }
    th_options = {"signal_object_prefix":"signal__" }
    hw_forces = {"ram.filename":module_root+"/ram.mif",
    }
    loggers = { #"dut": {"modules":"dut", "verbose":1}
                }
    def __init__(self, use_verilated=False, **kwargs):
        def ram_thef_fn(**kwargs):
            return RamThef(use_verilated=use_verilated, **kwargs)
        self.th_exec_file_object_fn = ram_thef_fn
        if use_verilated:
            self.dut_options = {"__implementation_name":"verilated"}
            pass
        else:
            self.dut_options = {"__implementation_name":"cdl_model"}
            pass
        HardwareThDut.__init__(self, **kwargs)
        pass
    pass

#c TestVector
class TestVector(TestCase):
    hw = DutHardware
    def test_ram_burst_cdl_1(self)->None:
        self.run_test(hw_args={"verbosity":0}, run_time=500)
        pass
    def test_ram_burst_v_1(self)->None:
        self.run_test(hw_args={"verbosity":0, "use_verilated":True}, run_time=500)
        pass
    pass
