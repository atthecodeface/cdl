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
from .engine    import SlMessage, SlLogEvent, SlLogRecorder, SlLogEventOccurrence, Engine, SimulationExecFile, HardwareExecFile, VcdFile
from .exec_file import SlMemory, SlEvent, SlFifo, SlRandom, ExecFile, ExecFileThreadFn
# from .waves     import Waves
from .exceptions import *
class _thfile(SimulationExecFile):
    pass

from typing import Tuple, Any, Union, Dict, List, Callable, Type, Optional, Sequence, Set, cast, ClassVar, TypeVar
T = TypeVar('T')
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .modules  import TestHarnessModule
    from .hardware import Hardware, HardwareDescription

#a Test harness for now
class LogEvent(object):
    def __init__(self, log_type:str, global_cycle:str, data:List[str], attr_map:Dict[str,int]):
        self.log_type = log_type
        self.global_cycle = int(global_cycle)
        self.data = data
        self.attr_map = attr_map
        for (k,n) in attr_map.items():
            setattr(self, k, int(data[n],16))
            pass
        pass
    def __str__(self) -> str:
        r = ""
        r += "log_event[%s]"%self.log_type
        r += ":%d:"%self.global_cycle
        r += "["+",".join(["%s:%x"%(n,getattr(self,n)) for n in self.attr_map.keys()])+"]"
        return r
    pass
class LogEventParser(object):
    def filter_module(self, module_name:str) -> bool : return True
    def map_log_type(self, log_type:str) -> Optional[str]: return log_type
    attr_map = {"args":{"arg0":0, "arg1":1, "arg2":2, "arg3":3}}
    def parse_log_event(self, log_occurrence:SlLogEventOccurrence) -> Optional[LogEvent]:
        l = log_occurrence.split(",")
        if not self.filter_module(l[0]): return None
        log_type = self.map_log_type(l[1])
        if log_type is None: return None
        return LogEvent(log_type=l[1], global_cycle=l[2], data=l[3:], attr_map=self.attr_map[log_type])
    pass

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
        self.__subthread_count = 0
        self.__subthread_count_completed = 0
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

    #f sim_fifo
    def sim_fifo(self, size:int, ne_wm:int=0, nf_wm:int=0) -> SlFifo:
        self.sys_fifo.fifo( "_temporary_object", size, ne_wm, nf_wm )
        x = cast(SlFifo,self._temporary_object)
        del self._temporary_object
        return x

    #f log_event
    def log_event(self, name:str, *args:Any) -> SlLogEvent:
        object_needs_replacement = hasattr(self,name)
        if object_needs_replacement: oldx=getattr(self,name)
        self.cdlsim_log.log_event( name, *args )
        x = cast(SlLogEvent,getattr(self, name))
        if object_needs_replacement: setattr(self,name,oldx)
        return x

    #f log_recorder
    def log_recorder(self, *args:Any) -> SlLogRecorder:
        self.cdlsim_log.log_recorder( "_temporary_object", *args )
        x = cast(SlLogRecorder,self._temporary_object)
        del self._temporary_object
        return x

    #f set_global_run_time - in global cycles
    def set_global_run_time(self, num_cycles: int) -> None:
        self.__run_time = num_cycles
        pass

    #f ticks_per_cycle
    def ticks_per_cycle(self) -> int:
        if self.__ticks_per_cycle==0: return 1
        return self.__ticks_per_cycle

    #f run_time_remaining - in bfm cycles
    def run_time_remaining(self) -> int:
        return (self.__run_time-self.global_cycle()) // self.ticks_per_cycle()

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
        self.verbose.info("%d:Starting to wait for test to be done"%(self.global_cycle()))
        self.bfm_wait(1)
        self.bfm_wait(1)
        self.bfm_wait(self.run_time_remaining()-margin)
        pass

    #f spawn
    def spawn(self, boundfn:ExecFileThreadFn, *args:Any, **kwargs:Any) -> None: # boundfn(a,b,c) where args=a,b,c
        self.__subthread_count = self.__subthread_count + 1
        def invoke_boundfn(*x:Any) -> None: # Invoke the required spawn function
            boundfn(*args, **kwargs)
            self.__subthread_count_completed = self.__subthread_count_completed + 1
            pass
        self.py.pyspawn(invoke_boundfn,tuple())
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
        self.verbose.error("%s:%s"%(self.global_cycle(), message))
        return self.py.pyfail(self.global_cycle(), message)

    #f passed
    def passed(self) -> int:
        if (self.__subthread_count != self.__subthread_count_completed):
            self.verbose.error("Some subthreads have not completed: spawned %d, only %d finished"%(self.__subthread_count, self.__subthread_count_completed))
            return False
        if self.__failures>0: return False
        return self.py.pypassed()

    #f compare_expected
    def compare_expected(self, reason:str, expectation:T, actual:T) -> None:
        if actual!=expectation:
            self.failtest("Mismatch in %s act/exp (%s/%s)"%(reason,str(actual),str(expectation)))
            pass
        pass

    #f compare_expected_list
    def compare_expected_list(self, reason:str, expectation:List[T], actual:List[T]) -> None:
        expectation = list(expectation[:])
        for t in actual:
            if len(expectation)>0:
                et = expectation.pop(0)
                self.compare_expected(reason,et,t)
                pass
            else:
                self.failtest("Unexpected %s (%s)"%(reason,str(t)))
                pass
            pass
        if len(expectation)>0:
            self.failtest("Expected more %ss: %s"%(reason,str(expectation)))
            pass
        pass

    #f All done
    pass

