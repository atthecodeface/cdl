#!/usr/bin/env python

#a Copyright
#
#  This file '__init__' copyright Gavin J Stark 2011
#
#  This program is free software; you can redistribute it and/or modify it under
#  the terms of the GNU General Public License as published by the Free Software
#  Foundation, version 2.0.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even implied warranty of MERCHANTABILITY
#  or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
#  for more details.


"""
This file implements PyCDL, which is the human-friendly interface from Python
code to CDL's py_engine interface.
"""
from .exceptions import *
from .th_exec_file import ThExecFile
from .instantiable import Instantiable
from .types import *
from .wires import Clock, Wire, WireHierarchy, WiringHierarchy
from typing import Tuple, Any, Union, Dict, List, Callable, Type, Optional, Sequence, Set, cast, ClassVar

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .hardware import HardwareDescription, Hardware
    from .connectivity import Connectivity
    pass
else:
    HardwareDescription=Type
    Hardware=Type
    Connectivity = Type
    pass

OptionsDict = Dict[str,Union[str,int,object]]

#a Hardware modules
#c Instance
class Instance(object):
    module_type : str
    forces  : OptionsDict
    options : OptionsDict
    #f __init__
    def __init__(self, module_type:str,
                 force_options:OptionsDict,
                 options:OptionsDict ) -> None:
        self.module_type = module_type
        self.options     = options
        self.forces      = force_options
        pass
    #f instantiate
    def instantiate(self, hwex:'HardwareDescription', instance_name:str) -> None:
        for [fk,f] in self.forces.items():
            (submodule,s,option) = fk.rpartition(".")
            submodule = instance_name + "." + submodule
            if isinstance(f, str):
                hwex.cdlsim_instantiation.module_force_option_string(submodule, option, f)
                pass
            elif isinstance(f, int):
                hwex.cdlsim_instantiation.module_force_option_int(submodule, option, f)
                pass
            else:
                hwex.cdlsim_instantiation.module_force_option_object(submodule, option, f)
                pass
            pass
        for [ok,o] in self.options.items():
            if isinstance(o, str):
                hwex.cdlsim_instantiation.option_string(ok, o)
                pass
            elif isinstance(o, int):
                hwex.cdlsim_instantiation.option_int(ok, o)
                pass
            else:
                hwex.cdlsim_instantiation.option_object(ok, o)
                pass
            pass
        print("Instantiated %s as %s options %s"%(self.module_type, instance_name, self.options))
        hwex.cdlsim_instantiation.module(self.module_type, instance_name)
        pass
    #f debug
    def debug(self) -> None:
        print("Instance:\n")
        for (n,o) in self.options.items():
            print("  Option '%s':'%s'"%(n,str(o)))
            pass
        for (n,o) in self.forces.items():
            print("  Force '%s':'%s'"%(n,str(o)))
            pass
    pass

#c Ports
class Ports(object):
    """
    This object represents the ports *as seen by the engine*
    """
    clocks  : Set[str]
    inputs  : WireHierarchy
    outputs : WireHierarchy
    def __init__(self, hardware:Hardware, instance_name:str):
        (clocks, inputs, outputs) = hardware.get_module_ios(instance_name)
        print("Hardware Clocks: %s"%(str(clocks)))
        print("Hardware Inputs: %s"%(str(inputs)))
        print("Hardware Outputs: %s"%(str(outputs)))
        self.clocks  = set()
        for (ck,_) in clocks: self.clocks.add(ck)
        self.inputs  = WireHierarchy()
        for (full_name, size) in inputs:
            self.inputs.add_wire(full_name, size)
            pass
        self.outputs  = WireHierarchy()
        for (full_name, size) in outputs:
            self.outputs.add_wire(full_name, size)
            pass
        pass
    def has_clock(self, name:str) -> bool:
        return name in self.clocks
    def debug(self) -> None:
        print("Ports:")
        for c in self.clocks:
            print("  Clock '%s'"%(c))
            pass
        print("  Inputs: '%s'"%(self.inputs.str_short()))
        print("  Outputs: '%s'"%(self.outputs.str_short()))
        pass

#c Module
class Module(Instantiable):
    """
    A module that can be instantiated -- either a CDL module or a Python
    test harness.
    """
    #v Class properties

    module_names : ClassVar[Dict[str,Set[str]]] = {}
    #t Instance property types
    _ports : Ports
    _name : str
    _clocks:  ClockDict
    _inputs:  Dict[str,WiringHierarchy]
    _outputs: Dict[str,WiringHierarchy]

    #f create_name - class method - create name of module
    @classmethod
    def create_name(cls, module_type:str, hint:str="")->str:
        if hint=="": hint=module_type
        if module_type not in cls.module_names:
            cls.module_names[module_type] = set()
            pass
        mnd = cls.module_names[module_type]
        n = hint
        i=0
        while n in mnd:
            n = "%s_i%d"%(hint,i)
            i+=1
            pass
        mnd.add(n)
        return n

    #f passed
    def passed(self) -> bool: return True

    #f __init__
    def __init__(self, moduletype:str, clocks:ClockDict={}, inputs:WiringDict={}, outputs:WiringDict={}, forces:OptionsDict={}, options:OptionsDict={}):
        self._type = moduletype
        self._name = self.create_name(moduletype, hint="")
        self._clocks = {}
        for (c, ck) in clocks.items():
            self._clocks[c] = ck
            pass
        self._inputs  = {}
        for (i,x) in inputs.items():
            self._inputs[i] = WiringHierarchy()
            self._inputs[i].add_wiring(wired_to=x)
            pass
        self._outputs  = {}
        for (i,x) in outputs.items():
            self._outputs[i] = WiringHierarchy()
            self._outputs[i].add_wiring(wired_to=x)
            pass
        self._options = options
        self._forces = forces
        pass

    #f get_instance
    def get_instance(self, hwex:HardwareDescription, hw:Hardware) -> Instance:
        inst = Instance(module_type   = self._type,
                        force_options = self._forces,
                        options       = self._options
        )
        return inst

    #f instantiate
    def instantiate(self, hwex:HardwareDescription, hw:Hardware) -> None:
        self.inst = self.get_instance(hwex, hw)
        self.inst.instantiate(hwex, self._name)
        self._ports = Ports(hw, self._name)
        pass

    #f add_connectivity
    def add_connectivity(self, hwex:HardwareDescription, connectivity:Connectivity) -> None:
        for (c, ck) in self._clocks.items(): # Explicit wiring
            if self._ports.has_clock(c):
                print(c,type(ck))
                connectivity.add_clock_sink(self, c, ck)
                pass
            else:
                hwex.report_error("module %s has wiring specified to clock '%s' but the hardware module does not have that port"%(self._name, c))
                pass
            pass
        for (name, wiring) in self._inputs.items():
            connectivity.add_wiring_sink(self, name, self._ports.inputs, wiring)
            pass
        for (name, wiring) in self._outputs.items():
            connectivity.add_wiring_source(self, name, self._ports.outputs, wiring)
            pass
        pass

    #f __str__
    def __str__(self) -> str:
        return "<Module {0}>".format(self._type)
    #f debug
    def debug(self) -> None:
        print("Module '%s' as '%s'"%(self._type, self._name))
        if hasattr(self, "_ports"):
            self._ports.debug()
            pass
        if hasattr(self, "inst"):
            self.inst.debug()
            pass
    pass

#c BaseTestHarnessModule
EFGenerator = Callable[...,ThExecFile]
class BaseTestHarnessModule(Module):
    """
    The object that represents a test harness.
    """
    exec_file_object_fn : EFGenerator
    exec_file_object    : ThExecFile
    #f passed
    def passed(self) -> bool:
        if hasattr(self, "exec_file_object"):
            if not self.exec_file_object.passed():
                print("Test harness %s : %s not PASSED" % (self._name,str(th)))
                return False
                pass
            pass
        return True

    #f __init__
    def __init__(self, clocks:ClockDict, inputs:WiringDict, outputs:WiringDict, exec_file_object:EFGenerator):
        Module.__init__(self, moduletype="se_test_harness", clocks=clocks, inputs=inputs, outputs=outputs, options={}, forces={})
        self.exec_file_object_fn = exec_file_object # type: ignore
        pass

    #f get_instance
    def get_instance(self, hwex:HardwareDescription, hw:Hardware) -> Instance:
        self.exec_file_object = self.exec_file_object_fn(hw,self)

        input_names = []
        for (n,i) in self._inputs.items():
            input_names.extend(i.full_sized_name_list(n))
            pass
        output_names = []
        for (n,i) in self._outputs.items():
            output_names.extend(i.full_sized_name_list(n))
            pass

        options : OptionsDict = {}
        options["clock"]   = " ".join(list(self._clocks.keys()))
        options["inputs"]  = " ".join(input_names)
        options["outputs"] = " ".join(output_names)
        options["object"]  = self.exec_file_object
        inst = Instance( module_type="se_test_harness", force_options={}, options=options)
        return inst

    #f All done
    pass

#c th - Standard test harness module used externally
class th(BaseTestHarnessModule):
    pass

