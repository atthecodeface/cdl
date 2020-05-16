#a Copyright
#
#  This file 'waves' copyright Gavin J Stark 2011
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

from .engine    import Engine, SimulationExecFile, HardwareExecFile, VcdFile
from .exec_file import SysMemory, SysEvent, SysFifo, SysRandom, ExecFile
from .exceptions import *

from typing import Tuple, Any, Union, Dict, List, Callable, Type, Optional, Sequence, Set, cast, ClassVar
from typing import TypeVar
T = TypeVar('T')

#a Waves
#c Waves
class Waves(object):
    waves : VcdFile
    """
    The object that controls waves, inside a hardware object. It's
    singletonized per hardware object
    """
    def __init__(self, waves:VcdFile) -> None:
        self._waves = waves
        self._waves_enabled = 0
        pass

    def reset(self)->None:
        self._waves.reset()
        pass

    def open(self, filename:str) -> None:
        self._waves.open(filename)
        pass

    def close(self)->None:
        self._waves.close()
        pass

    def enable(self)->None:
        if not self._waves_enabled:
            self._waves_enabled = 1
            self._waves.enable()
        else:
            self._waves.restart()

    def disable(self)->None:
        self._waves.pause()
        pass

    def file_size(self)->int:
        return self._waves.file_size()

    def _add(self, hierlist:Any) -> None:
        for x in hierlist:
            if isinstance(x, list):
                self._add(x)
                pass
            elif isinstance(x, dict):
                self._add([x[i] for i in list(x.keys())])
                pass
            else:
                self._waves.add(x._name)
                pass
            pass
        pass

    def add(self, *hier:Any) -> None:
        assert hasattr(self, "_waves")
        self._add(hier)
        pass

    def _add_hierarchy(self, hierlist:Any) -> None:
        for x in hierlist:
            if isinstance(x, list):
                self._add_hierarchy(x)
                pass
            elif isinstance(x, dict):
                self._add_hierarchy([x[i] for i in list(x.keys())])
                pass
            else:
                self._waves.add_hierarchy(x._name)
                pass
            pass
        pass
    def add_hierarchy(self, *hier:Any) -> None:
        assert hasattr(self, "_waves")
        self._add_hierarchy(hier)
        pass
    pass

