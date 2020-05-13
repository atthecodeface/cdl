#!/usr/bin/env python
import sys, os, unittest
from cdl.sim import ThExecFile            as ThExecFile
from cdl.sim import BaseTestHarnessModule as ThModule
from cdl.sim import hw                    as Hardware
from cdl.sim import ModuleForces
from cdl.sim import Wire, Clock, Module, TimedAssign
from cdl.sim import load_mif

import inspect
class x: pass
module_root = os.path.dirname(inspect.getfile(x))

#c vector_test_harness_exec_file
class vector_test_harness_exec_file(ThExecFile):
    def __init__(self, vectors_filename:str, s, **kwargs):
        self.vectors_filename = vectors_filename
        ThExecFile.__init__(self, **kwargs)
        self.th = s
        pass
    def exec_init(self):
        self.th._hw._engine.create_vcd_file(self)
        pass

    def test_values(self, vector_number:int) -> None:
        print("Cycle %d vector number %d, testing values" % (self.global_cycle(), vector_number))
        self.vector_input_0.drive(self.test_vectors[vector_number*4])
        self.vector_input_1.drive(self.test_vectors[vector_number*4+1])
        tv_0 = self.test_vectors[vector_number*4+2]
        tv_1 = self.test_vectors[vector_number*4+3]
        print("   info: expected %x %x got %x %x" % (tv_0, tv_1, self.vector_output_0.value(), self.vector_output_1.value()))
        if tv_0 != self.vector_output_0.value() or tv_1 != self.vector_output_1.value():
            print("Test failed, vector number %d" % vector_number)
            self.failtest(vector_number,  "**************************************************************************** Test failed")

    def run(self) -> None:
        self.test_vectors = load_mif(self.vectors_filename, 2048, 64, acknowledge_deprecated=True)
        self.bfm_wait(1)
        self.test_values(0)
        self.bfm_wait(1)
        self.test_values(1)
        self.bfm_wait(1)
        self.test_values(2)
        for i in range(10):
            self.bfm_wait(1)
            self.test_values(i+3)
        self.passtest(self.global_cycle(), "Test succeeded")
        pass

class vector_test_harness(ThModule):
    def __init__(self, vectors_filename:str, **kwargs):
        x = lambda s:vector_test_harness_exec_file(vectors_filename,s)
        ThModule.__init__(self, exec_file_object=x, **kwargs)
        pass
    pass

#c vector_hw
class vector_hw(Hardware):
    def __init__(self, width:int, module_name:str, module_mif_filename:str, inst_forces:ModuleForces={} ):
        print("Running vector test on module %s with mif file %s" % (module_name, module_mif_filename))

        self.test_reset      = Wire()
        self.vector_input_0  = Wire(size=width)
        self.vector_input_1  = Wire(size=width)
        self.vector_output_0 = Wire(size=width)
        self.vector_output_1 = Wire(size=width)
        self.system_clock    = Clock(init_delay=0, cycles_high=1, cycles_low=1)

        dut_forces = dict( list(inst_forces.items()) +
                           list({}.items())
                           )

        self.dut_0 = Module(module_name,
                                  clocks={ "io_clock": self.system_clock },
                                  inputs={ "io_reset": self.test_reset,
                                           "vector_input_0": self.vector_input_0,
                                           "vector_input_1": self.vector_input_1 },
                                  outputs={ "vector_output_0": self.vector_output_0,
                                            "vector_output_1": self.vector_output_1 },
                                  forces = dut_forces
                                  )
        self.test_harness_0 = vector_test_harness(clocks={ "clock": self.system_clock },
                                                  inputs={ "vector_output_0": self.vector_output_0,
                                                           "vector_output_1": self.vector_output_1 },
                                                  outputs={ "vector_input_0": self.vector_input_0,
                                                            "vector_input_1": self.vector_input_1 },
                                                  vectors_filename=module_mif_filename)
        self.rst_seq = TimedAssign(self.test_reset, 1, 5, 0)
        Hardware.__init__(self, self.dut_0, self.test_harness_0, self.system_clock, self.rst_seq)
        pass
    pass

#c TestVector
class TestVector(unittest.TestCase):
    def do_vector_test(self, width:int, module_name:str, module_mif_filename:str, inst_forces:ModuleForces={} ) -> None:
        hw = vector_hw(width, module_name, os.path.join(module_root,module_mif_filename), inst_forces=inst_forces)
        # waves = hw.waves()
        # waves.open(module_name+".vcd")
        # waves.add_hierarchy(hw.dut_0)
        # waves.enable()
        hw.reset()
        hw.step(50)
        self.assertTrue(hw.passed())

    def test_toggle_16(self)->None:
        self.do_vector_test(16, "vector_toggle__width_16", "vector_toggle__width_16.mif")

    def test_toggle_18_complex(self)->None:
        self.do_vector_test(18, "vector_toggle__width_18", "vector_toggle__width_18.mif", inst_forces={"vector_toggle__width_18.__implementation_name":"complex_cdl_model"})

    def test_toggle_18_simple(self)->None:
        self.do_vector_test(18, "vector_toggle__width_18", "vector_toggle__width_18.mif", inst_forces={"vector_toggle__width_18.__implementation_name":"cdl_model"})

    def test_add_4(self)->None:
        self.do_vector_test(4, "vector_add__width_4", "vector_add__width_4.mif")

    def test_mult_11_8(self)->None:
        self.do_vector_test(8, "vector_mult_by_11__width_8", "vector_mult_by_11__width_8.mif")

    def test_reverse_8(self)->None:
        self.do_vector_test(8, "vector_reverse__width_8", "vector_reverse__width_8.mif")

    # Run vector_nest with the vector_reverse file; the functionality is identical
    def test_nest_8(self)->None:
        self.do_vector_test(8, "vector_nest__width_8", "vector_reverse__width_8.mif")

    def test_sum_4(self)->None:
        self.do_vector_test(4, "vector_sum__width_4", "vector_sum__width_4.mif")

    def test_sum_2_4(self)->None:
        self.do_vector_test(4, "vector_sum_2__width_4", "vector_sum_2__width_4.mif")

    def test_op_1_16(self)->None:
        self.do_vector_test(16, "vector_op_1", "vector_op_1.mif")

    def test_op_2_16(self)->None:
        self.do_vector_test(16, "vector_op_2", "vector_op_2.mif")



if __name__ == '__main__':
    unittest.main()
