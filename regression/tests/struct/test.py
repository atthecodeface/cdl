#a Imports
from cdl.sim import ThExecFile
from cdl.sim import HardwareThDut, OptionsDict
from cdl.sim import TestCase

#a Test harness
#c int_value - just an int
class int_value(object):
    value:int
    def __init__(self, value):
        self.value=value
        pass
    def compare(self, other:'struct_int') -> bool:
        return self.value==other.value
    def __str__(self) -> str:
        return str(self.value)
    
#c struct_value - the x,y,z type
class struct_value(object):
    x:int
    y:int
    z:int
    def __init__(self, value:int):
        self.x = value&0xf
        self.y = (((value>>4)&0xf) - self.x) & 0xf
        self.z = (value&0xf) < ((value>>4)&0xf)
        pass
    def compare(self, other:'struct_value') -> bool:
        if (self.x!=other.x): return False
        if (self.y!=other.y): return False
        if (self.z!=other.z): return False
        return True
    def __str__(self):
        return "x:%x y:%x z:%d"%(self.x, self.y, self.z)
    
#c hierarchy_value - the x,y,z type
class hierarchy_value(object):
    valid : 1
    data  : struct_value
    word  : int
    def __init__(self, value:int):
        self.valid = (value & 1)
        self.data = struct_value(value)
        self.word = value
        pass
    def compare(self, other:'struct_value') -> bool:
        if (self.valid!=other.valid): return False
        if (self.word !=other.word): return False
        return self.data.compare(other.data)
    def __str__(self):
        return "word:%08x valid:%d %s"%(self.word, self.valid, str(self.data))
    
#c thef_data_word
class thef_data_word(object):
    def __init__(self, ef:ThExecFile, sig_name:str):
        self.sig = getattr(ef, sig_name)
        pass
    def drive(self, value:int_value):
        self.sig.drive(value.value)
        pass
    def get(self) -> int_value:
        return int_value(self.sig.value())
    pass

#c thef_data_struct
class thef_data_struct(object):
    def __init__(self, ef:ThExecFile, sig_name:str):
        self.sig__x = getattr(ef, sig_name+"__x")
        self.sig__y = getattr(ef, sig_name+"__y")
        self.sig__z = getattr(ef, sig_name+"__z")
        pass
    def drive(self, value:struct_value) -> None:
        self.sig__x.drive(value.x)
        self.sig__y.drive(value.y)
        self.sig__z.drive(value.z)
        pass
    def get(self) -> struct_value:
        value = struct_value(0)
        value.x = self.sig__x.value()
        value.y = self.sig__y.value()
        value.z = self.sig__z.value()
        return value
    pass

#c thef_data_hierachy
class thef_data_hierachy(object):
    def __init__(self, ef:ThExecFile, sig_name:str):
        self.sig__word  = getattr(ef, sig_name+"__word")
        self.sig__valid = getattr(ef, sig_name+"__valid")
        self.sig__data  = thef_data_struct(ef, sig_name+"__data")
        pass
    def drive(self, value:struct_value) -> None:
        self.sig__word.drive(value.word)
        self.sig__valid.drive(value.valid)
        self.sig__data.drive(value.data)
        pass
    def get(self) -> struct_value:
        value = hierarchy_value(0)
        value.word  = self.sig__word.value()
        value.valid = self.sig__valid.value()
        value.data  = self.sig__data.get()
        return value
    pass

#c thef
class thef(ThExecFile):
    th_name = "generic_fifo test harness"
    def __init__(self, hardware, **kwargs):
        self.thef_data_type = hardware.thef_data_type
        self.thef_data      = hardware.thef_data
        ThExecFile.__init__(self, hardware=hardware, **kwargs)
        pass
    def push(self, value:object) -> None:
        self.signal__fifo_push.drive(1)
        self.data_out.drive(value)
        self.pushed.append(value)
        self.bfm_wait(1)
        self.signal__fifo_push.drive(0)
        pass
    def pop(self) -> object:
        self.compare_expected("Fifo not empty when popping",0,self.signal__fifo_empty.value())
        self.signal__fifo_pop.drive(1)
        value = self.data_in.get()
        self.bfm_wait(1)
        self.signal__fifo_pop.drive(0)
        return value
    def run(self) -> None:
        self.pushed = []
        self.popped = []
        self.data_out = self.thef_data_type(self, "signal__fifo_data_in")
        self.data_in  = self.thef_data_type(self, "signal__fifo_data_out")
        self.signal__fifo_push.drive(0)
        self.signal__fifo_pop.drive(0)
        self.bfm_wait(10)
        self.compare_expected("Fifo initially empty",1,self.signal__fifo_empty.value())
        self.push(self.thef_data(12))
        # push and data are valid out now
        self.bfm_wait(1)
        # Fifo has data
        v = self.pop()
        self.popped.append(v)
        self.bfm_wait(10)
        self.compare_expected("Number pushed = number popped",len(self.pushed),len(self.popped))
        for i in range(len(self.pushed)):
            if i<len(self.popped):
                pu = self.pushed[i]
                po = self.popped[i]
                if not pu.compare(po):
                    self.failtest("Value pushed then popped mismatched %s: %s"%(str(pu), str(po)))
                    pass
                pass
            pass
        self.bfm_wait(10)
        self.verbose.info("Actual value received")
        self.passtest("Test succeeded")
        pass

#a Hardware
#c DutHardwareBase
class DutHardwareBase(HardwareThDut):
    clock_desc = [("io_clock",(0,1,1)),]
    reset_desc = {"name":"io_reset", "init_value":1, "wait":5}
    t_fifo_struct = {"z":1, "x":4, "y":4}
    t_fifo_hierarchy = {"word":32, "data":{"z":1, "x":4, "y":4}, "valid":1}
    dut_inputs = {"fifo_push":1,
                  "fifo_pop":1,
    }
    dut_outputs = {"fifo_empty":1,
    }
    th_options = {"signal_object_prefix":"signal__",
                 }
    th_exec_file_object_fn = thef
    def __init__(self, **kwargs):
        self.dut_inputs  = dict(self.dut_inputs.items())
        self.dut_outputs = dict(self.dut_outputs.items())
        self.dut_inputs["fifo_data_in"] = self.gt_fifo_content
        self.dut_outputs["fifo_data_out"] = self.gt_fifo_content
        HardwareThDut.__init__(self, **kwargs)
    pass

#c DutHardwareInt
class DutHardwareInt(DutHardwareBase):
    module_name = "generic_fifo_word"
    gt_fifo_content = 32
    thef_data_type = thef_data_word
    thef_data      = int_value
    pass

#c DutHardwareStruct
class DutHardwareStruct(DutHardwareBase):
    module_name = "generic_fifo_struct"
    thef_data_type = thef_data_struct
    thef_data      = struct_value
    gt_fifo_content = DutHardwareBase.t_fifo_struct

#c DutHardwareHierarchy
class DutHardwareHierarchy(DutHardwareBase):
    module_name = "generic_fifo_hierarchy"
    thef_data_type = thef_data_hierachy
    thef_data      = hierarchy_value
    gt_fifo_content = DutHardwareBase.t_fifo_hierarchy
    pass

#a Tests
#c TestInt
class TestInt(TestCase):
    hw = DutHardwareInt
    def test_struct_1(self)->None:
        self.run_test(hw_args={"verbosity":0}, run_time=500)
        pass
    pass

#c TestStruct
class TestStruct(TestInt):
    hw = DutHardwareStruct

#c TestHierarchy
class TestHierarchy(TestInt):
    hw = DutHardwareHierarchy
    pass
