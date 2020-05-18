#a Imports
import sys, os

import inspect
class xxx: pass
module_root = os.path.dirname(inspect.getfile(xxx))

from cdl.sim import ThExecFile            as ThExecFile
from cdl.sim import HardwareThDut, OptionsDict
from cdl.sim import TestCase
from cdl.sim import load_mif

from typing import Optional, Type, Any

#a Test harness classes
#c single_port_memory_th
class single_port_memory_th(ThExecFile):
    def __init__(self, test_vector_mif:str, is_mrw:bool, **kwargs):
        ThExecFile.__init__(self, **kwargs)
        self.test_vector_mif = test_vector_mif
        self.is_mrw = is_mrw
        pass

    def run(self) -> None:
        if not self.is_mrw:
            self.read_not_write_0 = self.read_not_write
            self.address_0        = self.address
            self.write_data_0     = self.write_data
            if hasattr(self, "write_enable"):
                self.write_enable_0   = self.write_enable
                pass
            self.data_out_0       = self.data_out
            pass
        if not hasattr(self, "write_enable_0"):
            class dummy_output(object):
                def reset(self, x): pass
                def drive(self, x): pass
            self.write_enable_0 = dummy_output()
            pass
        last_rnw_0 = 0
        last_rnw_1 = 0
        failure = 0
        self.test_vectors = load_mif(self.test_vector_mif, acknowledge_deprecated=True)
        self.read_not_write_0.reset(1)
        self.write_enable_0.reset(0)
        self.bfm_wait(1)
        tv_addr = 0
        last_data_0 : int
        while True:
            rnw_0 = self.test_vectors[tv_addr]
            ben_0 = self.test_vectors[tv_addr+1]
            addr_0 = self.test_vectors[tv_addr+2]
            data_0 = self.test_vectors[tv_addr+3]
            tv_addr += 4
            if rnw_0 > 256:
                break
            self.read_not_write_0.drive(rnw_0)
            self.write_enable_0.drive(ben_0)
            self.address_0.drive(addr_0)
            self.write_data_0.drive(0xdeadbeef)
            if rnw_0 != 1:
                self.write_data_0.drive(data_0)
            self.bfm_wait(1)
            if last_rnw_0 != 0 and last_data_0 != self.data_out_0.value():
                self.verbose.info("Got %x expected %x on read port 0 vector %d" % (self.data_out_0.value(), last_data_0, tv_addr/4))
                failure = 1
            last_rnw_0 = rnw_0
            last_data_0 = data_0

        self.read_not_write_0.reset(1)
        self.write_enable_0.reset(0)
        if failure != 0:
            self.failtest("Test failed")
        else:
            self.passtest("Test succeeded")
            pass
        pass

#c dual_port_memory_th
class dual_port_memory_th(ThExecFile):
    # sim_msg : cdl.sim.PyEngSimCDLSimReg.SlMessage
    def __init__(self, test_vector_mif:str, **kwargs):
        ThExecFile.__init__(self, **kwargs)
        self.test_vector_mif = test_vector_mif
        pass

    def read_sram_location( self, address:int ) -> int:
        self.sim_msg.send_value("dut",8,0,address)
        return self.sim_msg.get_value(2)

    def write_sram_location( self, address:int, data:int ) -> int:
        self.sim_msg.send_value("dut",9,0,address,data)
        return self.sim_msg.get_value(0)

    def run(self) -> None:
        if not hasattr(self, "write_enable_0"):
            class dummy_output(object):
                def reset(self, x): pass
                def drive(self, x): pass
            self.write_enable_0 = dummy_output()
            pass
        if not hasattr(self, "write_enable_1"):
            class dummy_output(object):
                def reset(self, x): pass
                def drive(self, x): pass
            self.write_enable_1 = dummy_output()
            pass
        last_rnw_0 = 0
        last_rnw_1 = 0
        failure = 0
        self.test_vectors = load_mif(self.test_vector_mif, acknowledge_deprecated=True)
        self.read_not_write_0.reset(1)
        self.write_enable_0.reset(0)
        self.read_not_write_1.reset(1)
        self.write_enable_1.reset(0)
        self.bfm_wait(1)
        self.sim_msg = self.sim_message()
        tv_addr = 0
        last_data_0 : int
        last_data_1 : int
        while True:
            rnw_0  = self.test_vectors[tv_addr]
            ben_0  = self.test_vectors[tv_addr+1]
            addr_0 = self.test_vectors[tv_addr+2]
            data_0 = self.test_vectors[tv_addr+3]
            rnw_1  = self.test_vectors[tv_addr+4]
            ben_1  = self.test_vectors[tv_addr+5]
            addr_1 = self.test_vectors[tv_addr+6]
            data_1 = self.test_vectors[tv_addr+7]
            tv_addr += 8
            if rnw_0 > 256:
                break
            self.read_not_write_0.drive(rnw_0)
            self.read_not_write_1.drive(rnw_1)
            self.write_enable_0.drive(ben_0)
            self.write_enable_1.drive(ben_1)
            self.address_0.drive(addr_0)
            self.address_1.drive(addr_1)
            self.write_data_0.drive(0xdeadbeef)
            self.write_data_1.drive(0xdeadbeef)
            if rnw_0 != 1:
                self.write_data_0.drive(data_0)
            if rnw_1 != 1:
                self.write_data_1.drive(data_1)
            self.bfm_wait(1)
            if last_rnw_0 != 0 and last_data_0 != self.data_out_0.value():
                print(self.global_cycle(),"Got %x expected %x on read port 0 vector %d" % (self.data_out_0.value(), last_data_0, tv_addr/8), file=sys.stderr)
                failure = 1
            if last_rnw_1 != 0 and last_data_1 != self.data_out_1.value():
                print(self.global_cycle(),"Got %x expected %x on read port 1 vector %d" % (self.data_out_1.value(), last_data_1, tv_addr/8), file=sys.stderr)
                failure = 1
            last_rnw_0 = rnw_0
            last_data_0 = data_0
            last_rnw_1 = rnw_1
            last_data_1 = data_1

        self.read_not_write_0.reset(1)
        self.read_not_write_1.reset(1)
        self.write_enable_0.reset(0)
        self.write_enable_1.reset(0)
        if failure != 0:
            self.failtest("Test failed")
        else:
            pass
        if False:
            for i in range(64):
                print("%3d %016x"%(i,self.read_sram_location(i)))
        expected_data = []
        for i in range(64):
            d = (i*0x73261fc)>>12
            d = d & 0xffff
            expected_data.append(d)
            self.write_sram_location(i,d)
        for i in range(64):
            if self.read_sram_location(i)!=expected_data[i]:
                self.failtest("Misread of sram written by message got %016x expected %016x"%(self.read_sram_location(i),expected_data[i]))
                pass
            pass
        self.passtest("Test completed")
        pass

#a Hardware classes
#c single_port_memory_srw_hw
class single_port_memory_srw_hw(HardwareThDut):
    clock_desc = [("sram_clock",(0,1,1),)
    ]
    module_name = "se_sram_srw"
    dut_options = { "num_ports": 1,
                    "size": 1024,
                    "width": 16,
                    "verbose": 0 }
    dut_inputs = { "address": 10,
                   "read_not_write": 1,
                   "write_data": 16
    }
    dut_outputs = { "data_out": 16,
    }
    # SRAM has no reset
    reset_desc = {}

    def __init__(self, bits_per_enable:int, mif_filename:str, tv_filename:str, **kwargs:Any):
        print("Regression batch arg mif:%s" % mif_filename)
        print("Regression batch arg bits_per_enable:%d" % bits_per_enable)
        print("Regression batch arg tv_file:%s" % tv_filename)
        print("Running single port SRAM test on 1024x16 %d bits per enable mrw sram mif file %s test vector file %s" % (bits_per_enable, mif_filename, tv_filename))
        self.dut_options = dict(self.dut_options.items())
        self.dut_options[ "filename" ] = mif_filename
        self.dut_options[ "bits_per_enable" ] = bits_per_enable
        self.dut_inputs = dict(self.dut_inputs.items())
        if bits_per_enable != 0:
            self.dut_inputs["write_enable"] = 16 // bits_per_enable
            pass
        # self.th_forces = inst_forces
        def fn(**kwargs): return single_port_memory_th(test_vector_mif=tv_filename, is_mrw=False, **kwargs)
        self.th_exec_file_object_fn = fn
        HardwareThDut.__init__(self, **kwargs)
        pass
    pass

#c single_port_memory_hw
class single_port_memory_hw(HardwareThDut):
    clock_desc = [("sram_clock_0",(0,1,1),)
    ]
    module_name = "se_sram_mrw"
    dut_options = { "num_ports": 1,
                    "size": 1024,
                    "width": 16,
                    "verbose": 0 }
    dut_inputs = { "address_0": 10,
                   "read_not_write_0": 1,
                   "write_data_0": 16
    }
    dut_outputs = { "data_out_0": 16,
    }
    # SRAM has no reset
    reset_desc = {}

    def __init__(self, bits_per_enable:int, mif_filename:str, tv_filename:str, **kwargs:Any):
        print("Regression batch arg mif:%s" % mif_filename)
        print("Regression batch arg bits_per_enable:%d" % bits_per_enable)
        print("Regression batch arg tv_file:%s" % tv_filename)
        print("Running single port SRAM test on 1024x16 %d bits per enable mrw sram mif file %s test vector file %s" % (bits_per_enable, mif_filename, tv_filename))
        self.dut_options = dict(self.dut_options.items())
        self.dut_options[ "filename" ] = mif_filename
        self.dut_options[ "bits_per_enable" ] = bits_per_enable
        self.dut_inputs = dict(self.dut_inputs.items())
        if bits_per_enable != 0:
            self.dut_inputs["write_enable_0"] = 16 // bits_per_enable
            pass
        # self.th_forces = inst_forces
        def fn(**kwargs): return single_port_memory_th(test_vector_mif=tv_filename, is_mrw=True, **kwargs)
        self.th_exec_file_object_fn = fn
        HardwareThDut.__init__(self, **kwargs)
        pass
    pass

#c dual_port_memory_hw
class dual_port_memory_hw(HardwareThDut):
    clock_desc = [("sram_clock_0",(0,1,1),),
                  ("sram_clock_1",(0,1,1),),
    ]
    module_name = "se_sram_mrw"
    dut_options = { "num_ports": 2,
                                           "size": 1024,
                                           "width": 16,
                                           "verbose": 0 }
    dut_inputs = { "address_0": 10,
                   "read_not_write_0": 1,
                   "write_data_0": 16,
                   "address_1": 10,
                   "read_not_write_1": 1,
                   "write_data_1": 16,
    }
    dut_outputs = { "data_out_0": 16,
                    "data_out_1": 16,
    }
    # SRAM has no reset
    reset_desc = {}

    def __init__(self, bits_per_enable:int, mif_filename:str, tv_filename:str, **kwargs):
        print("Regression batch arg mif:%s" % mif_filename)
        print("Regression batch arg bits_per_enable:%d" % bits_per_enable)
        print("Regression batch arg tv_file:%s" % tv_filename)
        print("Running dual port SRAM test on 1024x16 %d bits per enable mrw sram mif file %s test vector file %s" % (bits_per_enable, mif_filename, tv_filename))
        self.dut_options = dict(self.dut_options.items())
        self.dut_options[ "filename" ] = mif_filename
        self.dut_options[ "bits_per_enable" ] = bits_per_enable
        self.dut_inputs = dict(self.dut_inputs.items())
        if bits_per_enable != 0:
            self.dut_inputs["write_enable_0"] = 16 // bits_per_enable
            self.dut_inputs["write_enable_1"] = 16 // bits_per_enable
            pass
        # self.th_forces = inst_forces
        def fn(**kwargs): return dual_port_memory_th(test_vector_mif=tv_filename, **kwargs)
        self.th_exec_file_object_fn = fn
        HardwareThDut.__init__(self, **kwargs)
        pass
    pass

#a Tests
#c TestMemory
class TestMemory(TestCase):
    def do_memory_test(self, memory_type:HardwareThDut, bits_per_enable:int, mif_filename:str, tv_filename:str, waves=[])->None:
        self.hw = memory_type
        mif_filename = os.path.join(module_root,mif_filename)
        tv_filename = os.path.join(module_root,tv_filename)
        hw_args = {"bits_per_enable":bits_per_enable, "mif_filename":mif_filename, "tv_filename":tv_filename}
        self.run_test(hw_args=hw_args, waves=waves, run_time=2000)
        pass

    # This is the first single-port test: 1024x16, rnw, no additional enables
    def test_1024x16_srw_rnw_no_enables(self)->None:
        self.do_memory_test(single_port_memory_srw_hw, 0, "single_port_memory_in.mif", "single_port_memory.tv")

    # This is the second single-port test: 1024x16, rnw, with write enable
    def test_1024x16_srw_rnw_write_enable(self)->None:
        self.do_memory_test(single_port_memory_srw_hw, 16, "single_port_memory_in.mif", "single_port_memory_1_be.tv")

    # This is the third single-port test: 1024x16, rnw, with individaul byte write enables
    def test_1024x16_srw_rnw_byte_write_enable(self)->None:
        self.do_memory_test(single_port_memory_srw_hw, 8, "single_port_memory_in.mif", "single_port_memory_2_be.tv")

    # This is the first  single multi-port test: 1024x16, rnw, no additional enables
    def test_1024x16_srnw_byte_write_enable(self)->None:
        self.do_memory_test(single_port_memory_hw, 0, "single_port_memory_in.mif", "single_port_memory.tv")

    # This is the second single multi-port test: 1024x16, rnw, with write enable
    def test_1024x16_srnw_write_enable(self)->None:
        self.do_memory_test(single_port_memory_hw, 16, "single_port_memory_in.mif", "single_port_memory_1_be.tv")

    # This is the third single multi-port test: 1024x16, rnw, with individaul byte write enables
    def test_1024x16_srnw_byte_write_enable2(self)->None:
        self.do_memory_test(single_port_memory_hw, 8, "single_port_memory_in.mif", "single_port_memory_2_be.tv")

    # This is the first  dual-port test: 1024x16, rnw, no additional enables
    def test_1024x16_drnw_byte_write_enable(self)->None:
        self.do_memory_test(dual_port_memory_hw, 0, "dual_port_memory_in.mif", "dual_port_memory.tv")

    # This is the second dual-port test: 1024x16, rnw, with write enable
    def test_1024x16_drnw_write_enable(self)->None:
        self.do_memory_test(dual_port_memory_hw, 16, "dual_port_memory_in.mif", "dual_port_memory_1_be.tv")

    # This is the third dual-port test: 1024x16, rnw, with individaul byte write enables
    def test_1024x16_drnw_byte_write_enable2(self)->None:
        self.do_memory_test(dual_port_memory_hw, 8, "dual_port_memory_in.mif", "dual_port_memory_2_be.tv")


if __name__ == '__main__':
    unittest.main()
