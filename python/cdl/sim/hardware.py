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
from .wires     import Wire
from .instantiable     import Instantiable
from .modules import Module
from .connectivity import Connectivity
from .exceptions import *
from .bit_vector import Value, bv, bvbundle
from .th_exec_file import ThExecFile

from typing import Tuple, Any, Union, Dict, List, Callable, Type, Optional, Sequence, Set, cast, ClassVar
from typing import TypeVar
T = TypeVar('T')
from typing_extensions import Protocol

#a Hardware module description
#c HardwareDescription
class HardwareDescription(HardwareExecFile):
    _hw : 'Hardware'

    #f __init__
    def __init__(self, hw:'Hardware'):
        self._name = "hardware_exec_file"
        self._hw = hw
        self._running = False
        HardwareExecFile.__init__(self)
        pass

    #f report_error
    def report_error(self, msg:str) -> None:
        print(msg)
        # error count, etc
        pass
    #f instantiate_modules
    def instantiate_modules(self)->None:
        for i in self._hw._children:
            i.instantiate(self, self._hw)
            pass
        for i in self._hw._children:
            i.debug()
            pass
        pass

    #f get_connectivity
    def get_connectivity(self)->None:
        self.connectivity = Connectivity()
        for i in self._hw._children:
            print(i)
            i.add_connectivity(self, self.connectivity)
            pass
        pass

    #f check_connectivity
    def check_connectivity(self)->None:
        self.connectivity.check(self, self._hw)
        pass

    #f connect_wires
    def connect_wires(self)->None:
        self.connectivity.connect_wires(self, self._hw)
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
        if hasattr(cls, "_engine"): return
        cls._engine = Engine()
        pass

    #f __init__
    def __init__(self, children:List[Instantiable]=[], thread_mapping:Optional[Dict[str,Any]]=None):
        # Engine.__init__(self)
        # self._engine = self
        self.get_engine()
        self._name = "hardware"
        self._children = children

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

        print("Prepare to build")
        self.display_all_errors()
        self._engine.describe_hw(HardwareDescription(self))
        self.display_all_errors()
        print("Built")
        pass

    #f get_module_ios
    def get_module_ios(self, instance_name:str) -> Tuple[List[Any],List[Any],List[Any]]:
        io_list = Engine.get_module_ios(self._engine, instance_name)
        if io_list is None:
            raise WireError("Failed to get ports on module instance '%s' - perhaps the module type could not be found"%(instance_name))
        return (io_list[0], io_list[1], io_list[2])

    #f passed
    def passed(self) -> bool:
        passed = True
        for i in self._children:
            passed = passed and i.passed()
            pass
        if not passed:
            print("Not all tests passed")
            return False
        print("ALL TEST HARNESSES PASSED")
        return True

    #f display_all_errors
    def display_all_errors( self, max:int=10000 )->None:
        passed = self._engine.get_error_level() < 2
        print("Max error level %d"%(self._engine.get_error_level()))
        for i in range(max):
            x = self._engine.get_error(i)
            if x==None: break
            print("CDL SIM ERROR %2d %s"%(i+1,x), file=sys.stderr)
            pass
        if not passed: raise Exception("simulation engine error")
        self._engine.reset_errors()
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
        Reset the engine.
        """
        Engine.reset(self._engine)
        pass

    def step(self, cycles:int=1)->None:
        """
        Step for n cycles.
        """
        Engine.step(self._engine, cycles)
        self.display_all_errors()
        pass

    # def run_console( self, port:int=8745, locals:Dict[str,str]={} ) -> None:
    #     from .c_python_telnetd import c_python_telnet_server
    #     console_server = c_python_telnet_server( port=port, locals=locals )
    #     console_server.serve()
    #     pass
    pass

