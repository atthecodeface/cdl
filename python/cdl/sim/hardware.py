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
from .wires     import Wire, Wiring
from .modules import Module
from .connectivity import Connectivity
from .exceptions import *
from .bit_vector import Value, bv, bvbundle
from .th_exec_file import ThExecFile

from typing import Tuple, Any, Union, Dict, List, Callable, Type, Optional, Sequence, Set, cast, ClassVar
from typing import TypeVar
T = TypeVar('T')
from typing_extensions import Protocol

#a Nameable
#c Types - should be recursive (for Any, read Nameable)
Nameable = Union['_nameable', List[Any], Dict[str,Any]]
HardwareType = Type['hw']
Hardware = 'hw'

#a Hardware module description
#c HardwareDescription
class HardwareDescription(HardwareExecFile):
    _hw : 'hw'

    #f __init__
    def __init__(self, hw:'hw'):
        self._name = "hardware_exec_file"
        self._hw = hw
        self._running = False
        self._instantiated_wires = set()
        self._instantiation_anonid = 0
        HardwareExecFile.__init__(self)
        pass

    #f _connect_wire
    def _connect_wire(self, name:str, wireinst:Wire, connectedwires:Set[Wire], inputs:int, ports:Dict[str,Wire], assign:int, firstval:int, wait:int, afterval:int):
        wire_basename = name.split('.')[-1].split('__')[-1]
        if wire_basename not in ports:
            raise WireError("Connecting to undefined port '%s' (from name '%s')" % (wire_basename,name))
        port = ports[wire_basename]
        if not hasattr(port, "_size"):
            raise WireError("Port does not have a _size attribute, please check port %s, connection to wire %s." % (wire_basename, wireinst._name))
        elif wireinst._size != port._size:
            raise WireError("Port size mismatch for port %s, wire is size %s got a port size of %s" % (wire_basename, str(wireinst._size), str(port._size)))
                # size mismatch!
        if wireinst not in connectedwires:
            wireinst._instantiated_name = wireinst._name
            if wireinst._instantiated_name in self._instantiated_wires:
                wireinst._instantiated_name += "_INST%03d" % self._instantiation_anonid
                self._instantiation_anonid += 1
                pass
            self._instantiated_wires.add(wireinst._instantiated_name)
            if isinstance(wireinst, clock):
                self.cdlsim_instantiation.clock(wireinst._name, wireinst._init_delay, wireinst._cycles_high, wireinst._cycles_low)
                pass
            else:
                self.cdlsim_instantiation.wire("%s[%d]" % (wireinst._instantiated_name, wireinst._size))
                pass
            print("Adding wire %s to set for %s\n",wireinst._name,name)
            connectedwires.add(wireinst)
        if port not in connectedwires:
            connectedwires.add(port)
        if inputs:
            # This is an input to the module so the wire drives the port.
            self.cdlsim_instantiation.drive(name, wireinst._instantiated_name)
            #print "DRIVE %s %s" % (name, wireinst._instantiated_name)
            #print "Port %s driven by wire %s" % (repr(port), repr(wireinst))
            port._is_driven_by(wireinst)
        else:
            # This is an output from the module, so the port drives the wire.
            if assign is True:
                self.cdlsim_instantiation.assign(wireinst._instantiated_name, firstval, wait, afterval)
                #print "ASSIGN %s %d %d %d" % (wireinst._instantiated_name, firstval, wait, afterval)
            else:
                self.cdlsim_instantiation.drive(wireinst._instantiated_name, name)
                #print "DRIVE %s %s" % (wireinst._instantiated_name, name)
            #print "Wire %s driven by port %s" % (repr(wireinst), repr(port))
            wireinst._is_driven_by(port)
            pass
        pass
    #f _connect_wires
    def _connect_wires(self, name:str, wiredict:str, connectedwires:str, inputs:str, ports:str, assign:Optional[bool]=False, firstval:Optional[int]=None, wait:Optional[int]=None, afterval:Optional[int]=None) -> None:
        print(name,str(wiredict))
        for i in wiredict:
            if isinstance(wiredict[i], wire):
                self._connect_wire(name+i, wiredict[i], connectedwires, inputs, ports, assign, firstval, wait, afterval)
                pass
            elif isinstance(wiredict[i], wirebundle):
                if i not in ports or not isinstance(ports[i], wirebundle):
                    raise WireError("Connecting wire bundle %s to unknown port!" % i)
                self._connect_wires(name+i+"__", wiredict[i]._dict, connectedwires, inputs, ports[i]._dict, assign, firstval, wait, afterval)
                pass
            elif isinstance(wiredict[i], clock):
                self._connect_wire(name+i, wiredict[i], connectedwires, inputs, ports, assign, firstval, wait, afterval)
                pass
            else:
                raise WireError("Connecting unknown wire type %s" % repr(wiredict[i].__class__))
            pass
        pass

    #f instantiate_modules
    def instantiate_modules(self)->None:
        for i in self._hw._children:
            i.instantiate(self, self._hw)
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
    _children : List[Union[Module,Wiring]]
    _wavesinst : Waves
    _engine    : Engine

    @classmethod
    def get_engine(cls):
        if hasattr(cls, "_engine"): return
        cls._engine = Engine()
        pass

    #f __init__
    def __init__(self, thread_mapping=None, children=None, *children_list):
        # Engine.__init__(self)
        # self._engine = self
        self.get_engine()
        self._name = "hardware"
        # Hack arguments
        if (children is None) or (type(children)!=list):
            if children is not None:
                children = [thread_mapping, children]
                thread_mapping = None
                pass
            elif thread_mapping is not None:
                children.append(thread_mapping)
                thread_mapping = None
                pass
            children.extend(children_list)
            pass

        children_unpacked = []
        for child in children:
            if (isinstance(child,list)):
                children_unpacked.extend(child)
                pass
            else:
                children_unpacked.append(child)
                pass
            pass

        print(children_unpacked)
        self._children = list(itertools.chain.from_iterable([children_unpacked]))
        print(self._children)

        if thread_mapping is not None:
            self._engine.thread_pool_init()
            for x in list(thread_mapping.keys()):
                self._engine.thread_pool_add(x)
            for x in list(thread_mapping.keys()):
                for module_name in thread_mapping[x]:
                    r = self._engine.thread_pool_map_module(x,module_name)
                    print("Map returned",r)

        print("Prepare to build")
        self.display_all_errors()
        self._engine.describe_hw(HardwareDescription(self))
        self.display_all_errors()
        print("Built")
        pass

    #f get_module_ios
    def get_module_ios(self, instance_name):
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
    def connect_waves(self):
        if hasattr(self, "_wavesinst"):
            self._wavesinst._connect_waves()
            pass
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

