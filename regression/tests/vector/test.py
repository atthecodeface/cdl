#a Imports
import sys, os
from cdl.sim import ThExecFile            as ThExecFile
from cdl.sim import HardwareThDut, OptionsDict
from cdl.utils import Memory
from cdl.sim import TestCase

from typing import Any
import inspect
class xxx: pass
module_root = os.path.dirname(inspect.getfile(xxx))

#c vector_test_harness_exec_file
class vector_test_harness_exec_file(ThExecFile):
    def __init__(self, vectors_filename:str, **kwargs):
        self.vectors_filename = vectors_filename
        ThExecFile.__init__(self, **kwargs)
        pass

    def test_values(self, vector_number:int) -> None:
        self.verbose.info("Cycle %d vector number %d, testing values" % (self.global_cycle(), vector_number))
        self.vector_input_0.drive(self.test_vectors.get_exc(vector_number*4))
        self.vector_input_1.drive(self.test_vectors.get_exc(vector_number*4+1))
        tv_0 = self.test_vectors.get_exc(vector_number*4+2)
        tv_1 = self.test_vectors.get_exc(vector_number*4+3)
        self.verbose.info("   info: expected %x %x got %x %x" % (tv_0, tv_1, self.vector_output_0.value(), self.vector_output_1.value()))
        if tv_0 != self.vector_output_0.value() or tv_1 != self.vector_output_1.value():
            self.verbose.error("Test failed, vector number %d" % vector_number)
            self.failtest("Test failed in vector %d"%vector_number)

    def run(self) -> None:
        self.test_vectors = Memory()
        with open(self.vectors_filename) as f: self.test_vectors.load_legacy(f)
        self.bfm_wait(1)
        self.test_values(0)
        self.bfm_wait(1)
        self.test_values(1)
        self.bfm_wait(1)
        self.test_values(2)
        for i in range(10):
            self.bfm_wait(1)
            self.test_values(i+3)
        self.passtest("Test succeeded")
        pass

#c vector_hw
class vector_hw(HardwareThDut):
    # dut has an io_clock pin which we want to toggle on every cycle
    clock_desc = [("io_clock",(0,1,1)),
    ]
    # dut has an io_reset pin which we want to be high for 5 global ticks and go low - on negedge of clock so posedge clock logic has no races
    reset_desc = {"name":"io_reset", "init_value":1, "wait":5}
    def __init__(self, width:int, module_name:str, module_mif_filename:str, inst_forces:OptionsDict={}, **kwargs:Any):
        print("Running vector test on module %s with mif file %s" % (module_name, module_mif_filename))
        self.module_name = module_name
        self.dut_outputs = {"vector_output_0":width,"vector_output_1":width}
        self.dut_inputs  = {"vector_input_0":width, "vector_input_1":width}
        self.th_forces = inst_forces
        def fn(**kwargs): return vector_test_harness_exec_file(vectors_filename=module_mif_filename, **kwargs)
        self.th_exec_file_object_fn = fn
        HardwareThDut.__init__(self, **kwargs)
        pass
    pass

#c TestVector
#c TestVector
class TestVector(TestCase):
    hw = vector_hw
    def do_vector_test(self, width:int, module_name:str, module_mif_filename:str, inst_forces:OptionsDict={}, waves=[] ) -> None:
        module_mif_filename = os.path.join(module_root,module_mif_filename)
        hw_args = {"width":width, "module_name":module_name, "module_mif_filename":module_mif_filename, "inst_forces":inst_forces}
        self.run_test(hw_args=hw_args, waves=waves, run_time=500)
        pass

    def test_toggle_16(self)->None:
        self.do_vector_test(16, "vector_toggle__width_16", "vector_toggle__width_16.mif")

    def test_toggle_18_complex(self)->None:
        self.do_vector_test(18, "vector_toggle_complex__width_18", "vector_toggle__width_18.mif") #, inst_forces={"vector_toggle__width_18.__implementation_name":"complex_cdl_model"})

    def test_toggle_18_simple(self)->None:
        self.do_vector_test(18, "vector_toggle__width_18", "vector_toggle__width_18.mif") #, inst_forces={"vector_toggle__width_18.__implementation_name":"cdl_model"})

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

