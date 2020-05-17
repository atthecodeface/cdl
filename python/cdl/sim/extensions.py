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

# First, try to import the py_engine that we built. Either something around us
# will have put it in the PYTHONPATH or it will have set the CDL_BUILD_DIR
# environment variable.
import sys, os
import itertools, collections
import traceback
from .exceptions import *
from .exec_file import SlMemory, SlEvent, SlFifo, SlRandom, ExecFile, ExecFileThreadFn
from .instantiable import Instantiable
from .waves     import Waves
from .types     import WireTypeDictOrInt
from .wires     import Wire, Clock, TimedAssign
from .modules   import Module, TestHarnessModule, OptionsDict, EFGenerator
from .th_exec_file import ThExecFile
from .hardware import Hardware

from typing import Tuple, Any, Union, Dict, List, Callable, Type, Optional, Sequence, Set, cast, ClassVar

#a Extended hardware classes
#c HardwareThDut
class HardwareThDut(Hardware):
    """
    Simple instantiation of a module with just clock and reset, and some specified th ports
    """
    wave_hierarchies = []
    module_name = ""
    loggers = []
    clock_half_period = 1
    clock_desc     = [ ("clk",(0,None,None)), ]
    reset_desc     : Dict[str,Any] = {"name":"reset_n", "init_value":0, "wait":7}
    dut_inputs     : Dict[str,WireTypeDictOrInt] = {}
    dut_outputs    : Dict[str,WireTypeDictOrInt] = {}
    dut_options    : OptionsDict = {}
    thread_mapping = None
    th_exec_file_object_fn : Optional[EFGenerator] = None
    th_forces              : OptionsDict = {}

    #f test_harness_module_fn - the default
    def test_harness_module_fn(self, **kwargs:Any) -> TestHarnessModule:
        assert self.th_exec_file_object_fn is not None
        return TestHarnessModule(exec_file_object=self.th_exec_file_object_fn, **kwargs)

    #f __init__
    def __init__(self) -> None: #, test_dict:Dict[str,object]):
        self.wave_file = self.__class__.__module__+".vcd"

        children :List[Instantiable] = []
        inputs  : Dict[str,Wire] = {}
        outputs : Dict[str,Wire] = {}
        clocks = {}
        for (clk_pin, (delay, low, high)) in self.clock_desc:
            if low  is None: low  = self.clock_half_period
            if high is None: high = self.clock_half_period
            cdl_clock = Clock(name=clk_pin, init_delay=delay, cycles_low=low, cycles_high=high)
            clocks[clk_pin] = cdl_clock
            children.append( cdl_clock )
            pass
        th_clocks = {}
        if len(self.clock_desc)>0:
            clk_name = self.clock_desc[0][0]
            th_clocks[clk_name] = clocks[clk_name]
            pass

        if len(self.reset_desc)>0:
            reset_n = TimedAssign(name        = self.reset_desc["name"],
                                  init_value  = self.reset_desc["init_value"],
                                  wait        = self.reset_desc["wait"],
                                  later_value = self.reset_desc["init_value"] ^ 1)
            children.append(reset_n)
            inputs[self.reset_desc["name"]] = reset_n
            pass

        th_inputs  : Dict[str,Wire] = {}
        th_outputs : Dict[str,Wire] = {}
        for (n,wiring) in self.dut_inputs.items():
            cdl_wire      = Wire(name=n,struct=wiring)
            inputs[n]     = cdl_wire
            th_outputs[n] = cdl_wire
            pass
        for (n,wiring) in self.dut_outputs.items():
            cdl_wire     = Wire(name=n,struct=wiring)
            outputs[n]   = cdl_wire
            th_inputs[n] = cdl_wire
            pass

        hw_forces = dict(self.th_forces.items())
        self.dut = Module( module_type=self.module_name,
                           module_name="dut",
                           clocks  = clocks,
                           inputs  = inputs,
                           outputs = outputs,
                           options = self.dut_options,
                           forces  = hw_forces,
        )
        children.append(self.dut)

        if self.th_exec_file_object_fn is not None:
            self.test_harness_0 = self.test_harness_module_fn(clocks=th_clocks,
                                                              inputs=th_inputs,
                                                              outputs=th_outputs)
            children.append(self.test_harness_0)
            pass

        for l in self.loggers:
            log_module = Module("se_logger", options=self.loggers[l] )
            children.append(log_module)
            pass
        Hardware.__init__(self,
                          thread_mapping=self.thread_mapping,
                          children=children,
                          )
        self.wave_hierarchies = [self.dut]
        pass
    #f set_run_time
    def set_run_time(self, num_cycles:int) -> None:
        self.test.set_run_time(num_cycles/2/self.clock_half_period)
        pass

