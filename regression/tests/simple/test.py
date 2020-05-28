#a Imports
from cdl.sim import ThExecFile
from cdl.sim import Hardware, Wire, Clock, TimedAssign, Module, TestHarnessModule
from cdl.sim import TestCase

from typing import Any

#c test_harness_exec_file
class test_harness_exec_file(ThExecFile):
    th_name = "clock_gate test harness"
    def test_values(self, last_expected_value:int, expected_value:int) -> None:
        self.verbose.info( "Cycle %d, testing values constants %x last expected %d expected %d"%
                           (self.global_cycle(),
                            self.signal__constants_out.value(),
                            last_expected_value, expected_value))
        self.compare_expected("high_0 high", 1, self.signal__high_0.value())
        self.compare_expected("high_1 high", 1, self.signal__high_1.value())
        self.compare_expected("low_0 low",   0, self.signal__low_0.value())
        self.compare_expected("toggle_0 expected_value",   expected_value, self.signal__toggle_0.value())
        self.compare_expected("invert_0 expected_value",         1^expected_value, self.signal__invert_0.value())
        self.compare_expected("invert chain 0 expected_value",   1^expected_value, self.signal__invert_chain_0.value())
        self.compare_expected("invert chain 2 expected_value",   1^expected_value, self.signal__invert_chain_2.value())
        self.compare_expected("invert chain 4 expected_value",   1^expected_value, self.signal__invert_chain_4.value())
        self.compare_expected("invert chain 6 expected_value",   1^expected_value, self.signal__invert_chain_6.value())
        self.compare_expected("invert chain 1 expected_value",   expected_value, self.signal__invert_chain_1.value())
        self.compare_expected("invert chain 3 expected_value",   expected_value, self.signal__invert_chain_3.value())
        self.compare_expected("invert chain 5 expected_value",   expected_value, self.signal__invert_chain_5.value())
        self.compare_expected("invert chain 7 expected_value",   expected_value, self.signal__invert_chain_7.value())

        if last_expected_value==0:
            self.compare_expected("consants_out when last_expected_value==0", 0, self.signal__constants_out.value())
            pass
        else:
            self.compare_expected("consants_out when last_expected_value!=0", 8191, self.signal__constants_out.value())
            pass
        pass

    def run(self) -> None:
        self.bfm_wait(4)
        self.test_values(0,0)
        self.bfm_wait(1)
        self.test_values(0,0)
        self.verbose.info("%d:%d:Async reset should still be asserted (1 == %d)"%(self.global_cycle(), self.bfm_cycle(), self. signal__test_reset.value()))
        self.bfm_wait(1)
        self.test_values(0,0)
        self.verbose.info("%d:%d:Released async reset (0 == %d)"%(self.global_cycle(), self.bfm_cycle(), self. signal__test_reset.value()))
        # ? self.test_values(0,1)
        for i in range(10):
            self.bfm_wait(1)
            self.test_values(0,1)
            self.bfm_wait(1)
            self.test_values(1,0)
            pass
        self.passtest("Test succeeded")
        pass

#c DutHardware
class DutHardware(Hardware):
    #f __init__
    def __init__(self, **kwargs) -> None:
        self.wave_file = self.__class__.__module__+".vcd"

        children = []
        system_clock = Clock(name="System_clock", init_delay=0, cycles_low=1, cycles_high=1)
        children.append(system_clock)

        test_reset = TimedAssign( name="test_reset", init_value=1, wait=11, later_value=0)
        children.append(test_reset)

        high_0   = Wire(struct=1)
        high_1   = Wire(struct=1)
        low_0    = Wire(struct=1)
        toggle_0 = Wire(struct=1)
        invert_0 = Wire(struct=1)
        and_0    = Wire(struct=1)
        invert_chain = [Wire(struct=1) for i in range(8)]
        and_in = (Wire(struct=1), Wire(struct=1))
        constants_out = Wire(struct=13)

        children.append( Module( module_type="tie_high", outputs={"value":high_0} ) )

        children.append( Module( module_type="tie_both", outputs={"value_high":high_1, "value_low":low_0,}  ) )

        children.append( Module( module_type="toggle", module_name="toggle_i",
                                 clocks={"io_clock":system_clock},
                                 inputs={"io_reset":test_reset,
                                 },
                                 outputs={"toggle":toggle_0} ) )

        children.append( Module( module_type="invert",
                                 inputs={"in_value":toggle_0,},
                                 outputs={"out_value":invert_0} ) )

        children.append( Module( module_type="and",
                                 inputs={"in_value_0":and_in[0], "in_value_1":and_in[1],},
                                 outputs={"out_value":and_0} ) )

        children.append( Module( module_type="invert_chain",
                                 inputs={"in_value":toggle_0,},
                                 outputs=dict([("out_value_%d"%i,invert_chain[i]) for i in range(8)]) ))

        children.append( Module( module_type="constants",
                                 clocks={"clk":system_clock},
                                 inputs={"test_reset":test_reset,
                                         "in":toggle_0,},
                                 outputs={"out":constants_out} ) )

        th_clocks = {"clock":system_clock}
        th_options = {"signal_object_prefix":"signal__"}
        th_inputs = {"high_0": high_0,
                     "high_1": high_1,
                     "low_0": low_0,
                     "toggle_0": toggle_0,
                     "invert_0": invert_0,
                     "and_0": and_0,
                     "invert_chain_0": invert_chain[0],
                     "invert_chain_1": invert_chain[1],
                     "invert_chain_2": invert_chain[2],
                     "invert_chain_3": invert_chain[3],
                     "invert_chain_4": invert_chain[4],
                     "invert_chain_5": invert_chain[5],
                     "invert_chain_6": invert_chain[6],
                     "invert_chain_7": invert_chain[7],
                     "constants_out": constants_out,
                     "test_reset": test_reset }
        th_outputs = {"and_in_0":and_in[0], "and_in_1":and_in[1]}
        def th_exec_file_object_fn(**kwargs):
            return test_harness_exec_file(**kwargs)
        children.append( TestHarnessModule( module_name="th",
                                            exec_file_object_fn=th_exec_file_object_fn,
                                            clocks=th_clocks,
                                            inputs=th_inputs,
                                            outputs=th_outputs,
                                            options=th_options) )

        Hardware.__init__(self,
                          thread_mapping=None,
                          children=children,
                          **kwargs
                          )
        pass

#c TestVector
class TestVector(TestCase):
    hw = DutHardware
    def test_simple_1(self)->None:
        self.run_test(hw_args={"verbosity":0}, run_time=500)
        pass
    pass
