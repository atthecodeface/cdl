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
from .exceptions    import *
from .verbose import Verbose
from .exec_file import SlMemory, SlEvent, SlFifo, SlRandom, ExecFile, ExecFileThreadFn
from .engine    import Engine, SimulationExecFile, HardwareExecFile, VcdFile
from .waves     import Waves
from .wires     import Wire
from .instantiable     import Instantiable
from .modules       import Module
from .connectivity  import Connectivity

from typing import Tuple, Any, Union, Dict, List, Callable, Type, Optional, Sequence, Set, cast, ClassVar

#a Hardware module description
#c HardwareDescription
class HardwareDescription(HardwareExecFile):
    _hw : 'Hardware'
    error_count : int

    #f __init__
    def __init__(self, hw:'Hardware'):
        self._name = "hardware_exec_file"
        self._hw = hw
        self._running = False
        HardwareExecFile.__init__(self)
        self.error_count = 0
        Module.clear_instances()
        pass

    #f report_error
    def report_error(self, msg:str) -> None:
        self._hw.verbose.error("ERROR (in hardware description):%s"%msg)
        self.error_count = self.error_count + 1
        pass

    #f check_errors
    def check_errors(self, stage:str) -> None:
        if self.error_count>0:
            raise Exception("Hardware had errors during %s"%stage)
        return None

    #f instantiate_modules
    def instantiate_modules(self)->None:
        for i in self._hw._children:
            i.instantiate(self, self._hw)
            pass
        # for i in self._hw._children:
        #     i.debug()
        #     pass
        self.check_errors("module instantiation")
        pass

    #f get_connectivity
    def get_connectivity(self)->None:
        self.connectivity = Connectivity(self, self._hw)
        for i in self._hw._children:
            i.add_connectivity(self, self.connectivity)
            pass
        self.check_errors("creating wiring")
        pass

    #f check_connectivity
    def check_connectivity(self)->None:
        self.connectivity.check()
        self.check_errors("checking connectivity")
        pass

    #f connect_wires
    def connect_wires(self)->None:
        self.connectivity.connect_wires()
        self.check_errors("wiring module instances")
        pass

    #f exec_run - create the hardware
    def exec_run(self)->None:
        self.instantiate_modules()
        self.get_connectivity()
        self.check_connectivity()
        self.connect_wires()
        # self._set_up_reset_values()

        # Hook up any waves.
        self._hw.connect_waves()

        # Say we're in business.
        self._running = True
        pass
    #f All done
    pass

#a Hardware - really an engine
# class Hardware(Engine):
class Hardware(object):
    """
    The object that represents a piece of hardware.
    """
    _children: List[Instantiable]
    _wavesinst : Waves
    _engine    : Engine

    @classmethod
    def get_engine(cls) -> None:
        if hasattr(Hardware, "_engine"): return
        Hardware._engine = Engine()
        pass

    #f __init__
    def __init__(self, verbosity:int=2, children:List[Instantiable]=[], thread_mapping:Optional[Dict[str,Any]]=None):
        # Engine.__init__(self)
        # self._engine = self
        self.get_engine()
        self._engine.reset_errors()
        self._name = "hardware"
        self._children = children
        self.verbose = Verbose(verbosity,file=sys.stdout)

        if thread_mapping is not None:
            self._engine.thread_pool_init()
            for x in list(thread_mapping.keys()):
                self._engine.thread_pool_add(x)
                pass
            for x in list(thread_mapping.keys()):
                for module_name in thread_mapping[x]:
                    r = self._engine.thread_pool_map_module(x,module_name)
                    print("Map returned",r)
                    pass
                pass
            pass

        self.verbose.info("Prepare to build")
        self.display_all_errors()
        try:
            self.hw_desc_th = HardwareDescription(self)
            self._engine.describe_hw(self.hw_desc_th)
            pass
        except e:
            self.verbose.error("Failed to build - exception %s"%str(e))
            pass
        self.display_all_errors()
        self.verbose.info("Built")
        pass

    #f get_module_ios
    def get_module_ios(self, instance_name:str) -> Tuple[List[Any],List[Any],List[Any]]:
        io_list = Engine.get_module_ios(self._engine, instance_name)
        if io_list is None:
            raise WireError("Failed to get ports on module instance '%s' - perhaps the module type could not be found"%(instance_name))
        return (io_list[0], io_list[1], io_list[2])

    #f get_test_verbose
    def get_test_verbose(self)->Verbose:
        return self.verbose
    #f passed
    def passed(self) -> bool:
        passed = True
        for i in self._children:
            passed = passed and i.passed()
            pass
        if not passed:
            self.verbose.error("Not all tests passed")
            return False
        self.verbose.message("All tests passed")
        return True

    #f display_all_errors
    def display_all_errors( self, max:int=10000, force_exception=True )->None:
        # self.verbose.error("Check errors")
        passed = True
        for i in range(max):
            x = self._engine.get_error(i)
            if x==None: break
            (level,err) = x
            if level>=2: passed=False
            self.verbose.error("%s"%err)
            pass
        self._engine.reset_errors()
        if force_exception and not passed:
            raise Exception("simulation engine error")
        pass

    #f ensure_waves
    def ensure_waves(self, x):
        self._engine.create_vcd_file(x)
        pass

    #f connect_waves
    def connect_waves(self) -> None:
        #if hasattr(self, "_wavesinst"):
        #    self._wavesinst._connect_waves()
        #    pass
        pass

    def waves(self) -> Waves:
        if not hasattr(self, "_wavesinst"):
            self._wavesinst = Waves(self._engine.vcd_file())
            pass
        return self._wavesinst

    def reset(self)->None:
        """
        Reset the hardware running in the engine.
        """
        Engine.reset(self._engine)
        self.display_all_errors()
        pass

    def step(self, cycles:int=1)->None:
        """
        Step for n cycles.
        """
        Engine.step(self._engine, cycles, 1)
        self.display_all_errors()
        pass

    #f set_run_time
    def set_run_time(self, num_cycles:int) -> None:
        for c in self._children:
            if hasattr(c,"set_global_run_time"):
                c.set_global_run_time(num_cycles)
                pass
            pass
        pass

    # def run_console( self, port:int=8745, locals:Dict[str,str]={} ) -> None:
    #     from .c_python_telnetd import c_python_telnet_server
    #     console_server = c_python_telnet_server( port=port, locals=locals )
    #     console_server.serve()
    #     pass
    pass


