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

# The structure of the module is:
# base
# exceptions
# exec_file
# engine
# th_exec_file: exec_file, engine
# instantiable
# hierarchy: base
# types: hierarchy
# wires: types, hierarchy, instantiable
# modules: types, wires, instantiable, th_exec_file
# connectivity: types, wires, instantiable, modules
# hardware:
#
# Hardware
# Connecivity
# Module
# Wires

from typing import Tuple, Any, Union, Dict, List, Callable, Type, Optional, Sequence, Set, cast, ClassVar

VersionInfo = Tuple[int,int,int,str,int]

version_info : VersionInfo = (1,4,13,"",0)

def version() -> VersionInfo:
    global version_info
    return version_info

def hexversion() -> int:
    global version_info
    v = ( (version_info[0]<<24) |
          (version_info[1]<<16) |
          (version_info[2]<<8) |
          (version_info[4]<<0)  )
    return v

from .mif import load_mif, save_mif
from .th_exec_file import ThExecFile
from .modules  import TestHarnessModule
from .modules  import OptionsDict
from .wires    import Wire as Wire
from .wires    import Clock as Clock
from .wires    import TimedAssign as TimedAssign
from .modules  import Module as Module
from .hardware import Hardware
from .extensions import HardwareThDut
from .unittest import TestCase
