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
from .verbose import Verbose
from .engine    import SlMessage, Engine, SimulationExecFile, HardwareExecFile, VcdFile
from .exec_file import SlMemory, SlEvent, SlFifo, SlRandom, ExecFile, ExecFileThreadFn
# from .waves     import Waves
from .exceptions import *
class _thfile(SimulationExecFile):
    pass

from typing import Tuple, Any, Union, Dict, List, Callable, Type, Optional, Sequence, Set, cast, ClassVar
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .modules  import TestHarnessModule
    from .hardware import Hardware, HardwareDescription

#a Test harness for now
#c ThExecFile
class ThExecFile(SimulationExecFile):
    """
    Class to be subclassed for a test's th instance, to provide standard mechanisms
    for passing/failing, accessors for engine methods, and so on.

    th_name should be provided to identify the test for pass/fail

    A test harness must invoke passtest at least once to indicate a pass
    If the test harness invokes failtes even once, though, the test fails.
    """
    th_name : str
    verbose : Verbose
    hardware : 'Hardware'
    __failures : int
    __ticks_per_cycle : int
    __global_cycle_at_last_tick : int
    __bfm_cycle_at_last_tick : int
    def __init__(self, hardware:'Hardware', th_module:'TestHarnessModule', **kwargs:Any):
        self.hardware = hardware
        self.verbose = self.hardware.get_test_verbose()
        SimulationExecFile.__init__(self)
        pass

    def exec_init(self) -> None:
        SimulationExecFile.exec_init(self)
        self.hardware.ensure_waves(self)
        # Would auto-create input / output bundles here
        self.__failures = 0
        self.__ticks_per_cycle = 0
        pass

    def th_get_name(self) -> str:
        if hasattr(self, "th_name"): return self.th_name
        return self.__class__.__name__

    def run(self) -> None: ...
    def exec_run(self) -> None:
        try:
            self.run()
        except:
            self.failtest("Exception raised in run method!"+traceback.format_exc())
            raise

    #f exec_reset
    def exec_reset(self) -> None:
        SimulationExecFile.exec_reset(self)
        pass

    #f sim_message
    def sim_message(self) -> SlMessage:
        self.cdlsim_reg.sim_message( "_temporary_object" )
        x = cast(SlMessage,self._temporary_object)
        del self._temporary_object
        return x

    #f sim_event
    def sim_event(self) -> SlEvent:
        self.sys_event.event( "_temporary_object")
        x = cast(SlEvent,self._temporary_object)
        del self._temporary_object
        return x

    #f sim_memory
    def sim_memory(self, num_words:int, width:int) -> SlMemory:
        self.sys_memory.memory( "_temporary_object", num_words, width )
        x = cast(SlMemory,self._temporary_object)
        del self._temporary_object
        return x

    #f set_global_run_time - in global cycles
    def set_global_run_time(self, num_cycles: int):
        self.__run_time = num_cycles
        pass

    #f run_time_remaining - in bfm cycles
    def run_time_remaining(self) -> int:
        if self.__ticks_per_cycle==0: return self.__run_time
        return (self.__run_time-self.global_cycle()) // self.__ticks_per_cycle

    #f bfm_wait
    def bfm_wait(self, cycles:int) -> None:
        x = self.global_cycle()
        self.cdlsim_sim.bfm_wait(cycles)
        self.__ticks_per_cycle = (self.global_cycle()-x) // cycles
        pass

    #f bfm_wait_until_test_done
    def bfm_wait_until_test_done(self, margin:int) -> None:
        """
        Wait until the global run time for the test is over, with a safety margin in BFM clock ticks
        """
        self.bfm_wait(1)
        self.bfm_wait(1)
        self.bfm_wait(self.run_time_remaining-margin)
        pass

    #f spawn
    def spawn(self, boundfn:ExecFileThreadFn, *args:Any) -> None:
        self.py.pyspawn(boundfn, args)
        pass

    #f bfm_cycle
    def bfm_cycle(self) -> int:
        return self.cdlsim_sim.bfm_cycle()

    #f global_cycle
    def global_cycle(self) -> int:
        return self.cdlsim_sim.global_cycle()

    #f passtest
    def passtest(self, message:str) -> None:
        return self.py.pypass(self.global_cycle(), message)

    #f failtest
    def failtest(self, message:str) -> None:
        self.__failures = self.__failures + 1
        return self.py.pyfail(self.global_cycle(), message)

    #f passed
    def passed(self) -> int:
        if self.__failures>0: return False
        return self.py.pypassed()

    #f compare_expected
    def compare_expected(self, reason, expectation, actual):
        if actual!=expectation:
            self.failtest("Mismatch in %s act/exp (%d/%d)"%(reason,actual,expectation))
            pass
        pass

    #f compare_expected_list
    def compare_expected_list(self, reason, expectation, actual):
        expectation = list(expectation[:])
        for t in actual:
            if len(expectation)>0:
                et = expectation.pop(0)
                if t!=et:
                    self.failtest("Mismatch in %s (%d/%d)"%(reason,t,et))
                    pass
                pass
            else:
                self.failtest("Unexpected %s (%d)"%(reason,t,))
                pass
            pass
        if len(expectation)>0:
            self.failtest("Expected more %ss: %s"%(reason,str(expectation),))
            pass
        pass

    #f All done
    pass

