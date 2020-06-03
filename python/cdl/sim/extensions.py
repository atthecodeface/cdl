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

    module_name is the name of the CDL module to instantiate as 'dut' (device-under-test)

    loggers is a dictionary of <name> -> <logger options>
      logger options is a dictionary of <option> -> <value>
        modules is a string of space separated module names (starting with 'dut' usually)
        verbose is 1 to enable display to stdout of log events
        filename is the name of a file to log to (in the cwd)
      each entry makes an se_logger be created

    clock_desc is a list of <clock_name> -> (delay to first high, cycles low, cycles high)
    The first entry in clock_desc is used as the clock for the test harness (if any)
    This is why it is not a dictionary.

    reset_desc is a dictionary of <option> -> <value>
      name is the name of the reset signal for the dut
      init_value is the initial value of the signal
      wait is the delay before the signal changes to !init_value

    dut_inputs is a dictionary of <input port> -> <wiring description of port>

    dut_outputs is a dictionary of <output port> -> <wiring description of port>

    th_bfm_connections is a list of <port name>, for ports that the test harness *implicitly* has
      an se_test_harness module has none, but a BFM may have, e.g., an apb_request interface
      these will not be specified as th_inputs/th_outputs for the test harness to *add*

    hw_forces is a dictionary of <dut submodule.option_name> -> <value>

    th_module_type is an optional string name of the module to use for the test harness
      This defaults (ultimately) to se_test_harness
    """
    wave_hierarchies : Dict[str,List[str]] = {} # user_key -> list of module names (with + for hierarchy)
    module_name = ""
    loggers : Dict[str,OptionsDict] = {} # any key, then options for that se_logger module
    clock_half_period = 1
    clock_desc     = [ ("clk",(0,None,None)), ]
    reset_desc     : Dict[str,Any] = {"name":"reset_n", "init_value":0, "wait":7}
    dut_inputs     : Dict[str,WireTypeDictOrInt] = {}
    dut_outputs    : Dict[str,WireTypeDictOrInt] = {}
    dut_options    : OptionsDict = {}
    thread_mapping = None
    th_exec_file_object_fn : Optional[EFGenerator] = None
    hw_forces              : OptionsDict = {}
    th_options             : OptionsDict = {}
    th_module_type         : Optional[str] = None
    th_bfm_connections     : List[str] = []

    #f test_harness_module_fn - the default
    def test_harness_module_fn(self, **kwargs:Any) -> TestHarnessModule:
        return TestHarnessModule(**kwargs)

    #f __init__
    def __init__(self,
                 th_exec_file_object_fn:Optional[EFGenerator]=None,
                 th_args:Dict[str,Any]={},
                 th_module_type:Optional[str]=None, # Defaults to se_test_harness elsewhere
                 **kwargs:Any) -> None:
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

        hw_forces = dict(self.hw_forces.items())
        self.dut = Module( module_type=self.module_name,
                           module_name="dut",
                           clocks  = clocks,
                           inputs  = inputs,
                           outputs = outputs,
                           options = self.dut_options,
                           forces  = hw_forces,
        )
        children.append(self.dut)

        if th_module_type is None: th_module_type = self.th_module_type
        if th_exec_file_object_fn is None:
            th_exec_file_object_fn = self.th_exec_file_object_fn
            pass
        if th_exec_file_object_fn is not None:
            self.test_harness_0 = self.test_harness_module_fn(module_name="th",
                                                              module_type=th_module_type,
                                                              clocks=th_clocks,
                                                              inputs=th_inputs,
                                                              outputs=th_outputs,
                                                              bfm_connections=self.th_bfm_connections,
                                                              options=self.th_options,
                                                              exec_file_object_fn=th_exec_file_object_fn,
                                                              exec_file_object_fn_args=th_args
            )
            children.append(self.test_harness_0)
            pass

        for l in self.loggers:
            log_module = Module("se_logger", options=self.loggers[l] )
            children.append(log_module)
            pass

        Hardware.__init__(self,
                          thread_mapping=self.thread_mapping,
                          children=children,
                          **kwargs
                          )
        pass
