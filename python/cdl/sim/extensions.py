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
from .base import BaseExecFile
from .engine    import Engine, SimulationExecFile, HardwareExecFile, VcdFile
from .exec_file import SlMemory, SlEvent, SlFifo, SlRandom, ExecFile, ExecFileThreadFn
from .waves     import Waves
from .wires     import Wire, Clock, TimedAssign
from .modules import Module, BaseTestHarnessModule
from .exceptions import *
from .th_exec_file import ThExecFile
from .hardware import Hardware

from typing import Tuple, Any, Union, Dict, List, Callable, Type, Optional, Sequence, Set, cast, ClassVar
from typing import TypeVar
T = TypeVar('T')
from typing_extensions import Protocol

#a Extended hardware classes
#c HardwareThDut
class HardwareThDut(Hardware):
    """
    Simple instantiation of a module with just clock and reset, and some specified th ports
    """
    wave_hierarchies = []
    th_forces = {}
    module_name = ""
    loggers = []
    clock_half_period = 1
    clocks = { "clk":(0,None,None)}
    reset_desc = {"name":"reset_n", "init_value":0, "wait":7}
    dut_inputs   = {}
    dut_outputs  = {}
    thread_mapping = None
    th_exec_file_object_fn = None
    #f test_harness_module_fn - the default
    def test_harness_module_fn(self, **kwargs):
        return BaseTestHarnessModule(exec_file_object=self.th_exec_file_object_fn, **kwargs)
    #f __init__
    def __init__(self): #, test_dict:Dict[str,object]):
        self.wave_file = self.__class__.__module__+".vcd"

        children = []
        inputs = {}
        outputs = {}
        clocks = {}
        for clk_pin in self.clocks:
            (delay, low, high) = self.clocks[clk_pin]
            if low  is None: low  = self.system_clock_half_period
            if high is None: high = self.system_clock_half_period
            cdl_clock = Clock(name=clk_pin, init_delay=delay, cycles_low=low, cycles_high=high)
            clocks[clk_pin] = cdl_clock
            children.append( cdl_clock )
            pass

        reset_n = TimedAssign(name        = self.reset_desc["name"],
                              init_value  = self.reset_desc["init_value"],
                              wait        = self.reset_desc["wait"],
                              later_value = self.reset_desc["init_value"] ^ 1)
        children.append(reset_n)
        inputs[self.reset_desc["name"]] = reset_n

        th_inputs = {}
        th_outputs = {}
        for (n,wiring) in self.dut_inputs.items():
            cdl_wire      = Wire(name=n,size=wiring)
            inputs[n]     = cdl_wire
            th_outputs[n] = cdl_wire
            pass
        for (n,wiring) in self.dut_outputs.items():
            cdl_wire     = Wire(name=n,size=wiring)
            outputs[n]   = cdl_wire
            th_inputs[n] = cdl_wire
            pass

        hw_forces = dict(self.th_forces.items())
        self.dut = Module( module_type=self.module_name,
                           clocks  = clocks,
                           inputs  = inputs,
                           outputs = outputs,
                           forces  = hw_forces,
        )
        children.append(self.dut)

        self.test_harness_0 = self.test_harness_module_fn(clocks=clocks,
                                                          inputs=th_inputs,
                                                          outputs=th_outputs)
        children.append(self.test_harness_0)

        for l in self.loggers:
            log_module = pycdl.module( "se_logger", options=self.loggers[l] )
            children.append(log_module)
            pass
        Hardware.__init__(self,
                          thread_mapping=self.thread_mapping,
                          children=children,
                          )
        self.wave_hierarchies = [self.dut]
        pass
    #f set_run_time
    def set_run_time(self, num_cycles):
        self.test.set_run_time(num_cycles/2/self.system_clock_half_period)
        pass

#c HardwareDut
class HardwareDut(Hardware):
    """
    Simple instantiation of a module with just clock and reset, and some specified th ports
    """
    wave_hierarchies = []
    th_forces = {}
    module_name = ""
    loggers = []
    clock_half_period = 1
    clocks = { "clk":(0,None,None)}
    reset = {"name":"reset_n", "init_value":0, "wait":7}
    thread_mapping = None
    #f __init__
    def __init__(self): #, test_dict:Dict[str,object]):
        self.wave_file = self.__class__.__module__+".vcd"

        children = []
        inputs = {}
        outputs = {}
        clocks = {}
        for clk_pin in self.clocks:
            (delay, low, high) = self.clocks[clk_pin]
            if low  is None: low  = self.system_clock_half_period
            if high is None: high = self.system_clock_half_period
            cdl_clock = Clock(name=clk_pin, init_delay=delay, cycles_low=low, cycles_high=high)
            clocks[clk_pin] = cdl_clock
            children.append( cdl_clock )
            pass

        reset_n = TimedAssign(name        = self.reset["name"],
                              init_value  = self.reset["init_value"],
                              wait        = self.reset["wait"],
                              later_value = self.reset["init_value"] ^ 1)
        children.append(reset_n)
        inputs[self.reset["name"]] = reset_n

        hw_forces = dict(self.th_forces.items())
        hw_forces["%s.object"%test_harness] = test
        self.dut = pycdl.module( self.module_name,
                                 clocks  = self.cdl_clocks,
                                 inputs  = inputs,
                                 outputs = outputs,
                                 forces  = hw_forces,
                                 )
        children.append(self.dut)
        for l in self.loggers:
            log_module = pycdl.module( "se_logger", options=self.loggers[l] )
            children.append(log_module)
            pass
        Hardware.__init__(self,
                          thread_mapping=self.thread_mapping,
                          children=children,
                          )
        self.wave_hierarchies = [self.dut]
        pass
    #f set_run_time
    def set_run_time(self, num_cycles):
        self.test.set_run_time(num_cycles/2/self.system_clock_half_period)
        pass

