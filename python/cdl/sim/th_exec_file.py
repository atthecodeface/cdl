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
from .exceptions import *
class _thfile(SimulationExecFile):
    pass

from typing import Tuple, Any, Union, Dict, List, Callable, Type, Optional, Sequence, Set, cast, ClassVar
from typing import TypeVar
T = TypeVar('T')
from typing_extensions import Protocol

#a Test harness for now
class _th(SimulationExecFile):
    def exec_run(self) -> None:
        try:
            self.run()
        except:
            self._th.failtest(0, "Exception raised in run method!"+traceback.format_exc())
            raise
    pass

#c ThExecFile
class ThExecFile(_th):
    def exec_init(self) -> None:
        _th.exec_init(self)
        # Would auto-create input / output bundles here
        pass

    def exec_reset(self) -> None:
        _th.exec_reset(self)
        # _set_up_reset_values
        pass

    #f _set_up_reset_values
    def _set_up_reset_values(self)->None:
        """
        If we were to support input/outputs etc as auto-includes (for bundles etc) then this
        is supposed to auto-drive outputs (if they are that) from this test harness
        to the reset values
        """
        # And set up the reset values.
        # if not hasattr(self, "_connectedwires"):
        #     return
        # for i in self._connectedwires:
        #     if hasattr(i, "_reset_value") and i._reset_value:
        #         i._reset(i._reset_value)
        pass

    #f sim_message
    def sim_message(self):# -> SimulationExecFile.cdlsim_reg.SlMessage:
        self.cdlsim_reg.sim_message( "_temporary_object" )
        x = cast(SimulationExecFile.SlMessage,self._temporary_object)
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

    #f bfm_wait
    def bfm_wait(self, cycles:int) -> None:
        self.cdlsim_sim.bfm_wait(cycles)
        pass

    #f spawn
    def spawn(self, boundfn:ExecFileThreadFn, *args:Any) -> None:
        self.py.pyspawn(boundfn, args)
        pass

    #f global_cycle
    def global_cycle(self) -> int:
        return self.cdlsim_sim.global_cycle()

    #f passtest
    def passtest(self, code:int, message:str) -> None:
        return self.py.pypass(code, message)

    #f failtest
    def failtest(self, code:int, message:str) -> None:
        return self.py.pyfail(code, message)

    #f passed
    def passed(self) -> int:
        return self.py.pypassed()

    #f All done
    pass

