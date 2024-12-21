#a Imports
from cdl.sim import ThExecFile
from cdl.sim import HardwareThDut, OptionsDict
from cdl.sim import TestCase

#c gc_test_harness_exec_file
class gc_test_harness_exec_file(ThExecFile):
    th_name = "clock_gate test harness"
    def run(self) -> None:
        self.signal__data_in.drive(0)
        self.bfm_wait(10)
        self.signal__clock_divider.wait_for_value(16)
        expected_value = 0xf0a3c390f0a3c390
        actual_value = 0
        while self.signal__clock_divider.value()!=64:
            self.signal__data_in.drive(self.signal__data_out.value())
            self.bfm_wait(1)
            pass
        for pos in range(64):
            chosen_bit = (expected_value >> pos) & 1
            actual_value = (actual_value>>1) | (self.signal__data_out.value()<<63)
            self.compare_expected("data out value", chosen_bit, self.signal__data_out.value())
            self.signal__data_in.drive(self.signal__data_out.value())
            self.bfm_wait(1)
            pass
        self.verbose.info("Actual value received from dut: %016x"%actual_value)
        self.passtest("Test succeeded")
        pass

#c DutHardware
class DutHardware(HardwareThDut):
    clock_desc = [("clk",(0,1,1)),
    ]
    module_name = "gc_simple"
    dut_outputs = {"clock_divider":8,
                   "data_out":1,
                   "data_sub_out":1,
    }
    dut_inputs = {"data_in":1,
    }
    th_options = {"signal_object_prefix":"signal__",
                 }
    reset_desc = {"name":"reset_in", "init_value":1, "wait":19}
    th_exec_file_object_fn = gc_test_harness_exec_file
    pass

#c TestVector
class TestVector(TestCase):
    hw = DutHardware
    def test_gc_1(self)->None:
        self.run_test(run_time=500)
        pass
    pass
