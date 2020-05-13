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
from .exec_file import SysMemory, SysEvent, SysFifo, SysRandom, ExecFile
from .waves     import Waves
from .exceptions import *
class _thfile(SimulationExecFile):
    pass

from typing import Tuple, Any, Union, Dict, List, Callable, Type, Optional, Sequence, Set, cast, ClassVar
from typing import TypeVar
T = TypeVar('T')
from typing_extensions import Protocol

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

#a Nameable
#c Types - should be recursive (for Any, read Nameable)
Nameable = Union['_nameable', List[Any], Dict[str,Any]]
HardwareType = Type['hw']
Hardware = 'hw'
ModuleForces = Dict[str,str]
WireDict = Dict[str,Union['clock','wire']]
ClockDict = Dict[str,'clock'] #Hardware]
InputDict  = Dict[str,'wire']
OutputDict = Dict[str,'wire']
OptionsDict = Dict[str,Union[str,int,object]]

#c _nameable - a class with a _name, given to it by a _namegiver
class _nameable(object):
    """
    An object that should get named when assigned to a namegiver object.
    """
    _name : str # Once given...
    def __repr__(self)->str: return str(self._name)
    pass

#c _nameable - a class that gives names to _nameables/List[_nameable]/Dict[str,_nameable]
class _namegiver(object):
    """
    An object that gives nameable objects a name.
    """
    def _give_name(self, name:str, value:Union[Nameable,List[Nameable],Dict[str,Nameable]]) -> None:
        if isinstance(value, _nameable) and (not hasattr(value, "_name") or value._name is None or value._name==""):
            value._name = name
            pass
        elif isinstance(value, list):
            for i in range(len(value)):
                self._give_name("%s_%d" % (name, i), value[i])
                pass
            pass
        elif isinstance(value, dict):
            for s in list(value.keys()):
                self._give_name("%s_%s" % (name, str(s)), value[s])
                pass
            pass
        pass

    def __setattr__(self, name:str, value:Any) -> None:
        self._give_name(name, value)
        object.__setattr__(self, name, value)
        pass
    pass

#a Bit vector class
#c bv - sized int
class bv(object):
    """
    A bit-vector. Has a size and a value.
    """
    Access = Union[slice,int]
    _val : int
    _size : Optional[int]
    def __init__(self, val:int, size:Optional[int]=None):
        self._val = val
        self._size = size
        if size is not None:
            self._val &= (1<<size)-1
            pass
        pass

    def value(self) -> int:
        return self._val

    __int__ = value # this allows us to use a bv where we otherwise use a number

    def __eq__(self, other:object) -> bool:
        if isinstance(other, bv):
            if other._size != self._size:
                return False
            else:
                return self._val == other._val
        else:
            return self._val == other

    def __ne__(self, other:object) -> bool:
        return not self.__eq__(other)

    def __cmp__(self, other:object) -> int:
        if isinstance(other, bv):
            return self._val - other._val
        return self._val - cast(int,other)

    def size(self) -> Optional[int]:
        return self._size

    def _getset(self, key:Access, item:int, isset:bool) -> int:
        # Figure out the start and stop.
        if isinstance(key, slice):
            start = key.start
            stop = key.stop
            step = key.step
        else:
            start = key
            stop = key
            step = 1
        if step is not None and step != 1:
            raise IndexError
        if start is None:
            if self._size is None:
                raise IndexError
            start = self._size - 1
        if stop is None:
            stop = 0
        if start < 0:
            if self._size is None:
                raise IndexError
            start = self._size - start
        if stop < 0:
            if self._size is None:
                raise IndexError
            stop = self._size - stop
        if stop > start:
            (start, stop) = (stop, start)
        if start >= 64 or (self._size is not None and start >= self._size):
            raise IndexError

        # OK, now we have a known-sane start and stop.
        unshiftedmask = (1 << (start - stop + 1)) - 1
        shiftedmask = unshiftedmask << stop

        if (isset):
            self._val &= ~shiftedmask
            self._val |= (item & unshiftedmask) << stop
            return self._val
        result : int =  (self._val & shiftedmask) >> stop
        return result

    def __getitem__(self, key:Access) -> int:
        return self._getset(key, 0, False)

    def __setitem__(self, key:Access, item:int) -> None:
        self._getset(key, item, True)
        return None

    pass

#c bvbundle - Bundle of bit vectors
class bvbundle(object):
    """
    A bundle of bit vectors (or of more bvbundles)
    """
    _dict : Dict[str,str]
    def __init__(self, indict:Optional[Dict[str,Union['wire', 'wirebundle']]]=None, **kw:Any) -> None:
        if indict is not None:
            self.__dict__["_dict"] = indict
            self._dict.update(kw)
            pass
        else:
            self.__dict__["_dict"] = kw
            pass
        pass

    def __getattr__(self, name:str) -> Any:
        if name in self._dict:
            return self._dict[name]
        raise AttributeError

    def __setattr__(self, name:str, value:Any) -> None:
        raise AttributeError # bvbundles are read-only
    pass

#a Wires
#c WireBase - nameable that is driven_by something and drives something
class WireBase(_nameable):
    def _name_list(self, inname:str) -> List[str]: ...
    def _check_connectivity(self:T, other:T) -> None: ...
    def _is_driven_by(self:T, other:T) -> None: ...
    pass

#c wire - nameable that is driven_by something and drives something
class wire(WireBase):
    """
    The object that represents a wire.
    """
    # _cdl_signal : PyEngSim.Global # Global wire created in hardware when the hardware is built - passed in at _connect_cdl_signal
    _instantiated_name : str # Given to the wire in the hardware when the hardware is built
    _drives : List['wire']
    _driven_by: Optional['wire']
    _size : int
    _cdl_signal : Optional[Any]
    _reset_value : Optional[int]
    #f __init__
    def __init__(self, name:str="", size:int=1):
        self._drives = []
        self._driven_by = None
        self._size = size
        self._cdl_signal = None
        self._name = name
        self._reset_value = None
        pass

    #f _name_list
    def _name_list(self, inname:str) -> List[str]:
        return ["%s[%d]" % (inname, self._size)]

    #f _check_connectivity
    def _check_connectivity(self, other:'wire') -> None:
        if self._size and other._size and self._size != other._size:
            raise WireError("Size mismatch: %s has %d, %s has %d" % (repr(self), self._size, repr(other), other._size))
        pass

    #f _is_driven_by
    def _is_driven_by(self, other:'wire') -> None:
        if self._driven_by:
            raise WireError("Double-driven signal at %s" % repr(self))
        self._check_connectivity(other)
        self._driven_by = other
        other._drives.append(self)
        pass

    #f _connect_cdl_signal
    def _connect_cdl_signal(self, signal:str) -> None:
        if self._cdl_signal and self._cdl_signal != signal:
            raise WireError("Connecting two CDL signals on %s: %s and %s" % (repr(self), repr(self._cdl_signal), repr(signal)))
        if not self._cdl_signal:
            #print "CONNECT %s to CDL %s" % (repr(self), repr(signal))
            self._cdl_signal = signal
            pass
        for i in self._drives:
            i._connect_cdl_signal(signal)
            pass
        pass

    #f _connectivity_upwards
    def _connectivity_upwards(self, index:int) -> 'wire':
        if self._driven_by:
            print("%sDriven by %s" % (" "*index, repr(self._driven_by)))
            return self._driven_by._connectivity_upwards(index+2)
        else:
            print("%sROOT AT %s" % (" "*index, repr(self)))
            return self
        pass

    #f _connectivity_downwards
    def _connectivity_downwards(self, index:int)->None:
        print("%sAt %s, CDL signal %s" % (" "*index, repr(self), repr(self._cdl_signal)))
        for i in self._drives:
            print("%sDrives %s" % (" "*index, repr(i)))
            i._connectivity_downwards(index+2)
            pass
        pass

    #f print_connectivity
    def print_connectivity(self) -> None:
        print("Finding connectivity tree for %s:" % repr(self))
        root = self._connectivity_upwards(0)
        print()
        root._connectivity_downwards(0)
        pass

    #f size
    def size(self) -> int:
        return self._size

    #f value
    def value(self) -> bv:
        if self._cdl_signal:
            return bv(self._cdl_signal.value(), self._size)
        else:
            raise WireError("No underlying value for signal %s" % repr(self))

    #f drive
    def drive(self, value:Union[bv,int]) -> None:
        if isinstance(value, bv):
            value = value.value()
            pass
        if self._cdl_signal:
            self._cdl_signal.drive(value)
            pass
        else:
            raise WireError("No underlying signal to drive for %s" % repr(self))

    #f _reset
    def _reset(self, value:int) -> None:
        if self._cdl_signal:
            self._cdl_signal.reset(value)
        else:
            raise WireError("No underlying signal to drive for %s" % repr(self))

    #f reset
    def reset(self, value:int) -> None:
        if self._cdl_signal:
            self._cdl_signal.reset(value)
        self._reset_value = value
        pass

    #f wait_for_value
    def wait_for_value(self, val:int, timeout:int=-1) -> None:
        if self._cdl_signal:
            self._cdl_signal.wait_for_value(val, timeout)
        else:
            raise WireError("No underlying value for signal %s" % repr(self))

    #f wait_for_change
    def wait_for_change(self, timeout:int=-1) -> None:
        if self._cdl_signal:
            self._cdl_signal.wait_for_change(timeout)
        else:
            raise WireError("No underlying value for signal %s" % repr(self))
        pass

    #f All done
    pass

#c clock - special type of wire that corresponds to a CDL simulation clock
class clock(wire):
    def __init__(self, name:str="", init_delay:int=0, cycles_high:int=1, cycles_low:int=1):
        self._init_delay = init_delay
        self._cycles_high = cycles_high
        self._cycles_low = cycles_low
        wire.__init__(self, size=1, name=name)
        pass
    pass

#c wirebundle - nameable that represents a bundle of wires through a dictionary
class wirebundle(WireBase):
    """
    The object that represents a bundle of wires.
    """
    WireBundleDefn = Dict[str,Union[int, Any]]
    WireBundle     = Dict[str,WireBase]
    _dict: WireBundle
    _drives     : List['wirebundle']
    _driven_by  : Optional['wirebundle']
    _size : int
    _cdl_signal : Optional[Any]
    _reset_value : Optional[int]
    def __init__(self, name:str, bundletype:Optional[WireBundleDefn]=None, **kw:Any):
        if bundletype:
            # Build the bundle from a dict.
            self._dict = {}
            for i in bundletype:
                if isinstance(bundletype[i], int):
                    self._dict[i] = wire(name=i, size=bundletype[i])
                    pass
                else:
                    bundledefn = cast(wirebundle.WireBundleDefn, bundletype[i])
                    self._dict[i] = wirebundle(name=i, bundletype=bundledefn)
                    pass
                pass
            pass
        else:
            self._dict = kw
            pass
        self._drives = []
        self._driven_by   = None
        self._reset_value = None
        self._name = name
        pass

    #f _name_list
    def _name_list(self, inname:str) -> List[str]:
        retval = []
        for i in self._dict:
            subval = self._dict[i]._name_list(i)
            for j in subval:
                retval.append("%s__%s" % (inname, j))
        return retval

    def _check_connectivity(self, other:'wirebundle') -> None:
        # Check that all the signals in the bundle match the one we're
        # connecting up.
        unusedkeys = set(other._dict.keys())
        for i in self._dict:
            if i not in other._dict:
                raise WireError("Wire bundle mismatch in %s, missing other's value %s" % (repr(self), i))
            unusedkeys.remove(i)
            self._dict[i]._check_connectivity(other._dict[i])
            pass
        if len(unusedkeys) > 0:
            raise WireError("Wire bundle mismatch in %s, leftover signals" % repr(self))
        pass

    #f _populate_dict
    def _populate_dict(self, other:'wirebundle') -> None:
        # Yay! Now we know what signals we have! If we hooked up signals
        # anonymously, we now need to put together our bundle and check it.
        for i in other._dict:
            if isinstance(other._dict[i], wirebundle):
                other_bundle = cast('wirebundle', other._dict[i])
                this_bundle = wirebundle(name="<anonymous>")
                this_bundle._populate_dict(other_bundle)
                self._dict[i] = this_bundle
                pass
            elif isinstance(other._dict[i], wire):
                other_wire = cast(wire, other._dict[i])
                self._dict[i] = wire(name="<anonymous>",size=other_wire.size())
                pass
            else:
                raise WireError("Unknown wire type %s" % repr(other.__class__))
        # If we've already hooked this thing up, we need to propagate our
        # knowledge of what's in there.
        if self._driven_by:
            self._update_connectivity(self._driven_by)
            pass
        for d in self._drives:
            d._update_connectivity(self)
            pass
        pass

    #f _update_connectivity
    def _update_connectivity(self, other:'wirebundle') -> None:
        if len(self._dict) == 0 and len(other._dict) != 0:
            self._populate_dict(other)
            pass
        if len(other._dict) == 0 and len(self._dict) != 0:
            other._populate_dict(self)
            pass
        if len(self._dict) > 0:
            self._check_connectivity(other)
            pass
        pass

    #f _is_driven_by
    def _is_driven_by(self, other:'wirebundle') -> None:
        if self._driven_by:
            raise WireError("Double-driven signal at %s" % repr(self))
        self._update_connectivity(other)
        for i in self._dict:
            self._dict[i]._is_driven_by(other._dict[i])
        self._driven_by = other
        other._drives.append(self)
        pass

    #f _add_wire
    def _add_wire(self, wirename:str, size:int, name:str) -> WireBase:
        # First see if we need to recurse.
        wirelist = wirename.split("__", 1)
        if len(wirelist) > 1:
            # We need to go down to another level of bundles.
            sub_bundle = cast('wirebundle', self._dict[wirelist[0]])
            if wirelist[0] not in self._dict:
                sub_bundle = wirebundle(name="<anonymous>")
                self._dict[wirelist[0]] = sub_bundle
                pass
            return sub_bundle._add_wire(wirelist[1], size, name)
        else:
            if wirelist[0] in self._dict:
                raise WireError("Double add of wire %s to bundle" % wirelist[0])
            self._dict[wirelist[0]] = wire(size=size, name=name)
            return self._dict[wirelist[0]]
        pass

    #f value - only once in a running simulation
    def value(self) -> bvbundle:
        # We want the value. Fair enough. Go dig and get it.
        outdict = {}
        for i in self._dict:
            outdict[i] = self._dict[i].value()
            pass
        return bvbundle(outdict)

    #f drive - only once in a running simulation
    def drive(self, inbundle:bvbundle) -> None:
        # Drive a whole bundle.
        unusedkeys = set(inbundle._dict.keys())
        for i in self._dict:
            if i not in inbundle._dict:
                raise WireError("Wire bundle mismatch in %s, missing other's value %s" % (repr(self), i))
            unusedkeys.remove(i)
            self._dict[i].drive(inbundle._dict[i])
        if len(unusedkeys) > 0:
            raise WireError("Wire bundle mismatch in %s, leftover signals" % repr(self))
        pass

    def _reset(self, inbundle:bvbundle) -> None:
        # Drive a whole bundle for reset.
        unusedkeys = set(inbundle._dict.keys())
        for i in self._dict:
            if i not in inbundle._dict:
                raise WireError("Wire bundle mismatch in %s, missing other's value %s" % (repr(self), i))
            unusedkeys.remove(i)
            self._dict[i]._reset(inbundle._dict[i])
        if len(unusedkeys) > 0:
            raise WireError("Wire bundle mismatch in %s, leftover signals" % repr(self))

    def reset(self, inbundle:bvbundle) -> None:
        # Set the reset value for the bundle.
        unusedkeys = set(inbundle._dict.keys())
        for i in self._dict:
            if i not in inbundle._dict:
                raise WireError("Wire bundle mismatch in %s, missing other's value %s" % (repr(self), i))
            unusedkeys.remove(i)
            self._dict[i].reset(inbundle._dict[i])
        if len(unusedkeys) > 0:
            raise WireError("Wire bundle mismatch in %s, leftover signals" % repr(self))
        self._reset_value = inbundle

    def __getattr__(self, attr:str) -> Any:
        if attr not in self._dict:
            raise AttributeError
        else:
            return self._dict[attr]

        pass
    pass

#a Hardware module description
#c _hwexfile
class _hwexfile(HardwareExecFile):
    _hw : 'hw'

    #f __init__
    def __init__(self, hw:'hw'):
        self._name = "hardware_exec_file"
        self._hw = hw
        self._running = False
        self._instantiated_wires = set()
        self._instantiation_anonid = 0
        print("_hwexfile::__init__")
        HardwareExecFile.__init__(self)
        pass

    #f _connect_wire
    def _connect_wire(self, name:str, wireinst:wire, connectedwires:Set[wire], inputs:int, ports:Dict[str,wire], assign:int, firstval:int, wait:int, afterval:int):
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
                print("CLOCK %s" % wireinst._name)
                print("CLOCK %s" % wireinst._size)
                print(wireinst._name, wireinst._init_delay, wireinst._cycles_high, wireinst._cycles_low)
                self.cdlsim_instantiation.clock(wireinst._name, wireinst._init_delay, wireinst._cycles_high, wireinst._cycles_low)
                pass
            else:
                print("WIRE %s" % wireinst._instantiated_name)
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

    def _connect_wires(self, name:str, wiredict:str, connectedwires:str, inputs:str, ports:str, assign:Optional[bool]=False, firstval:Optional[int]=None, wait:Optional[int]=None, afterval:Optional[int]=None) -> None:
        print(name,str(wiredict))
        for i in wiredict:
            if isinstance(wiredict[i], wire):
                print("self._connect_wire", name+i, wiredict[i], connectedwires, inputs, ports, assign, firstval, wait, afterval)
                self._connect_wire(name+i, wiredict[i], connectedwires, inputs, ports, assign, firstval, wait, afterval)
                pass
            elif isinstance(wiredict[i], wirebundle):
                if i not in ports or not isinstance(ports[i], wirebundle):
                    raise WireError("Connecting wire bundle %s to unknown port!" % i)
                self._connect_wires(name+i+"__", wiredict[i]._dict, connectedwires, inputs, ports[i]._dict, assign, firstval, wait, afterval)
                pass
            else:
                raise WireError("Connecting unknown wire type %s" % repr(wiredict[i].__class__))
            pass
        pass
    #f _set_up_reset_values
    def _set_up_reset_values(self)->None:
        # And set up the reset values.
        if not hasattr(self, "_connectedwires"):
            return
        for i in self._connectedwires:
            if i._reset_value:
                i._reset(i._reset_value)


    #f exec_init
    def exec_init(self)->None:
        print("_hwexfile::exec_init")
        print("Create VCD file")
        print("Hwex",dir(self))
        print("Hw",dir(self._hw))
        print("Eng",dir(self._hw._engine))
        # self._hw._engine.create_vcd_file(self._hw)
        pass

    #f exec_reset
    def exec_reset(self)->None:
        print("_hwexfile::exec_reset")
        self._set_up_reset_values()
        pass

    #f exec_reset - create the hardware
    def exec_run(self)->None:
        print("_hwexfile::exec_run")
        anonid = 1
        connectedwires = set()
        for i in self._hw._children:
            if not hasattr(i, "_name") or i._name is None:
                i._name = "__anon%3d" % anonid
                anonid += 1
            if isinstance(i, module):
                for j in list(i._forces.keys()):
                    (submodule,s,option) = j.rpartition(".")
                    if isinstance(i._forces[j], str):
                        self.cdlsim_instantiation.module_force_option_string(i._name+"."+submodule, option, i._forces[j])
                    elif isinstance(i._forces[j], int):
                        self.cdlsim_instantiation.module_force_option_int(i._name+"."+submodule, option, i._forces[j])
                    else:
                        self.cdlsim_instantiation.module_force_option_object(i._name+"."+submodule, option, i._forces[j])
                for j in i._options:
                    if isinstance(i._options[j], str):
                        self.cdlsim_instantiation.option_string(j, i._options[j])
                    else:
                        self.cdlsim_instantiation.option_int(j, i._options[j])
                #print "MODULE %s %s" % (i._type, i._name)
                self.cdlsim_instantiation.module(i._type, i._name)
                ios = self._hw._engine.get_module_ios(i._name)
                if not ios:
                    raise WireError("Failed to find IOs for module '{0}'; probably failed to instantiate it".format(i._name))
                i._ports = i._ports_from_ios(ios, None)
            elif isinstance(i, BaseTestHarnessModule):
                self.cdlsim_instantiation.option_string("clock", " ".join(list(i._clocks.keys())))
                self.cdlsim_instantiation.option_string("inputs", " ".join([" ".join(i._inputs[x]._name_list(x)) for x in i._inputs]))
                self.cdlsim_instantiation.option_string("outputs", " ".join([" ".join(i._outputs[x]._name_list(x)) for x in i._outputs]))
                self.cdlsim_instantiation.option_object("object", i.exec_file_object(self))
                self.cdlsim_instantiation.module("se_test_harness", i._name)
                i._hw = self
                i._ports = i._ports_from_ios(self._hw._engine.get_module_ios(i._name), None) #i._thfile)
            elif isinstance(i, clock):
                pass # we'll hook up later
            elif isinstance(i, timed_assign):
                pass # we'll hook up later
            else:
                raise NotImplementedError

        for i in self._hw._children:
            if hasattr(i, "_ports") and (not i._ports):
                raise WireError("Bad port structure in connecting module '%s' - perhaps a module could not be found?" % (repr(i)))
            if hasattr(i, "_clocks") and hasattr(i, "_ports"):
                self._connect_wires(i._name+".", i._clocks, connectedwires, inputs=True, ports=i._ports[0])
            if hasattr(i, "_inputs") and hasattr(i, "_ports"):
                self._connect_wires(i._name+".", i._inputs, connectedwires, inputs=True, ports=i._ports[1])
            if hasattr(i, "_outputs") and hasattr(i, "_ports"):
                if isinstance(i, timed_assign):
                    self._connect_wires(i._name+".", i._outputs, connectedwires, inputs=False, ports=i._ports[2], assign=True,
                                        firstval = i._firstval, wait=i._wait, afterval=i._afterval)
                else:
                    self._connect_wires(i._name+".", i._outputs, connectedwires, inputs=False, ports=i._ports[2])

        # Now make sure all the CDL signals are hooked up.
        #print "*** Starting CDL signal hookup"
        for i in connectedwires:
            #print "Looking at %s" % repr(i)
            origi = i
            # Find a CDL signal for this tree.
            while not i._cdl_signal and i._driven_by:
                i = i._driven_by
            if i._cdl_signal:
                # Find the root of the driving tree.
                sig = i._cdl_signal
                while i._driven_by:
                    i = i._driven_by
                i._connect_cdl_signal(sig)
            #print "Done looking at %s" % repr(origi)

        self._connectedwires = connectedwires

        self._set_up_reset_values()

        # Hook up any waves.
        self._hw.connect_waves()

        # Say we're in business.
        self._running = True
        pass
    #f All done
    pass

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
    #f sim_message
    def sim_message(self):# -> SimulationExecFile.cdlsim_reg.SlMessage:
        self.cdlsim_reg.sim_message( "_temporary_object" )
        x = cast(SimulationExecFile.SlMessage,self._temporary_object)
        del self._temporary_object
        return x

    #f sim_event
    def sim_event(self) -> SysEvent.SlEvent:
        self.sys_event.event( "_temporary_object", num_words, width )
        x = cast(SysEvent.SlEvent,self._temporary_object)
        del self._temporary_object
        return x

    #f sim_memory
    def sim_memory(self, num_words:int, width:int) -> SysMemory.SlMemory:
        self.sys_memory.memory( "_temporary_object", num_words, width )
        x = cast(SysMemory.SlMemory,self._temporary_object)
        del self._temporary_object
        return x

    #f bfm_wait
    def bfm_wait(self, cycles:int) -> None:
        self.cdlsim_sim.bfm_wait(cycles)
        pass

    #f spawn
    def spawn(self, boundfn:ExecFile.py.ThreadCallable, *args:Any) -> None:
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

#a Hardware modules
#c _clockable - something that appears in an engine when the hw's hwex file is run in that engine
class _clockable(_namegiver, _nameable):
    """
    The base class for all pieces of hardware.
    """
    #f __init__ - actually not an __init__, but called when engine is instantiated
    def __init__(self, *children:List['_clockable']):
        # Flatten the list of children.
        self._children = list(itertools.chain.from_iterable(children))

    def _clock(self) -> None:
        raise e
        for i in self._children:
            i._clock()
            pass
        pass
    pass

#c _instantiable
class _instantiable(_clockable):
    """
    A module that can be instantiated -- either a CDL module or a Python
    test harness.
    """
    PortMap = Dict[str,Union[wire,wirebundle]]
    Ports = List[PortMap]
    _ports : Ports
    _auto_wire_same_name = True
    def _ports_from_ios(self, iolist:List[List[Tuple[str,int]]], cdl_object:_clockable) -> Ports:
        if not iolist:
            raise WireError("No IOs passed to a module - perhaps the module type could not be found")
        # The I/O list should have three members -- a list of clocks, a list of
        # inputs and a list of outputs.
        # Each of these members contains a list of ports. We'll turn these into
        # wires.
        retlist = []
        for id_type in iolist:
            retdict : PortMap = {}
            for io in id_type:
                if len(io[0])==0: continue
                wirelist = io[0].split("__", 1)
                if len(wirelist) > 1:
                    if wirelist[0] not in retdict:
                        retdict[wirelist[0]] = wirebundle()
                    thewire = retdict[wirelist[0]]._add_wire(wirelist[1], io[1], io[0])
                    pass
                else:
                    retdict[io[0]] = wire(size=io[1], name=io[0])
                    thewire = retdict[io[0]]
                    pass
                print(len(io),io)
                print("'%s'"%io[0], cdl_object)
                print("Creating port wire: %s size %d, result %s" % (io[0], io[1], str(repr(thewire))))
                if cdl_object and hasattr(cdl_object, io[0]) and self._auto_wire_same_name:
                    print("Connecting CDL signal %s" % repr(getattr(cdl_object, io[0])))
                    thewire._connect_cdl_signal(getattr(cdl_object,io[0]))
                    pass
                else:
                    #print "No CDL signal!"
                    pass

            retlist.append(retdict)
        return retlist

#c BaseTestHarnessModule
class BaseTestHarnessModule(_instantiable):
    """
    The object that represents a test harness.
    """
    exec_file_object = None
    def _flatten_names(self, inobj:Union[List[Any],WireDict], inname:str=None) -> WireDict:
        outdict = {}
        if isinstance(inobj, list):
            for i in range(len(inobj)):
                if inname is None:
                    outdict.update(self._flatten_names(inobj[i], "%d" % i))
                else:
                    outdict.update(self._flatten_names(inobj[i], "%s_%d" % (inname, i)))
        elif isinstance(inobj, dict):
            for i in list(inobj.keys()):
                if inname is None:
                    outdict.update(self._flatten_names(inobj[i], "%s" % str(i)))
                else:
                    outdict.update(self._flatten_names(inobj[i], "%s_%s" % (inname, str(i))))
        else:
            outdict = { inname: inobj }
        return outdict

    #f __init__
    def __init__(self, clocks:ClockDict, inputs:InputDict, outputs:OutputDict, exec_file_object=None):
        self._clocks   = self._flatten_names(clocks)
        self._inputs   = self._flatten_names(inputs)
        self._outputs  = self._flatten_names(outputs)
        self.exec_file_object = exec_file_object
        pass

    #f All done
    pass

#c _internal_th
class _internal_th(BaseTestHarnessModule):
    """
    A sentinel to show an internal test harness that does not need to be considered
    in pass/fail.
    """
    pass

#c _wave_hook
class _wave_hook(_internal_th):
    """
    A timed assignment, often used for a reset sequence.
    """
    def __init__(self)->None:
        _internal_th.__init__(self, clocks={}, inputs={}, outputs={})
        pass
    def run(self)->None:
        pass

#c th - Standard test harness module used externally
class th(BaseTestHarnessModule):
    pass

#c timed_assign
class timed_assign(_instantiable):
    """
    A timed assignment, often used for a reset sequence.
    """
    def __init__(self, signal:wire, init_value:int, wait:Optional[int]=None, later_value:Optional[int]=None):
        if wait is None:
            wait = 1<<31
        if later_value is None:
            later_value = init_value
        self._outputs = {"sig": signal}
        self._ports = self._ports_from_ios([[], [], [["sig", signal._size]]], None)
        self._firstval = init_value
        self._wait = wait
        self._afterval = later_value

#c module
class module(_instantiable):
    """
    The object that represents a CDL module.
    """
    _name : str # Because this is nameable, this is defined at hardware instantiation time
    def __init__(self, moduletype:str, options:OptionsDict={}, clocks:ClockDict={}, inputs:InputDict={}, outputs:OutputDict={}, forces:ModuleForces={}):
        self._type = moduletype
        self._clocks = clocks
        self._inputs = inputs
        self._outputs = outputs
        self._options = options
        self._forces = forces
    def __repr__(self) -> str:
        return "<Module {0}>".format(self._type)
#c hw
class hw(_clockable):
    """
    The object that represents a piece of hardware.
    """
    _engine : ClassVar[Engine] # Created when the object is instantiated
    @classmethod
    def create_engine(cls):
        if hasattr(cls,"_engine"):
            print(dir(cls._engine))
            return
        cls._engine = Engine()
        # cls._engine.vcd_file(cls) - want to do this, but engine does not support it yet
        pass
    _wavesinst     : Waves
    def __init__(self, thread_mapping=None, children=None, *children_list):
        self._name = "hardware"
        self.create_engine()
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
            else:
                children_unpacked.append(child)
        children_unpacked = tuple(children_unpacked)
        _clockable.__init__(self, children_unpacked)

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
        self._hwex = _hwexfile(self)
        self._engine.describe_hw(self._hwex)
        self.display_all_errors()
        print("Built")
        pass

    #f connect_waves
    def connect_waves(self):
        if hasattr(self, "_wavesinst"):
            self._wavesinst._connect_waves()
            pass
        pass

    def passed(self) -> bool:
        for i in self._children:
            if isinstance(i, th) and not isinstance(i, _internal_th):
                if not i.passed():
                    print("Test harness %s not PASSED" % str(th))
                    return False
        print("ALL TEST HARNESSES PASSED")
        return True

    def display_all_errors( self, max:int=10000 )->None:
        for i in range(max):
            x = self._engine.get_error(i)
            if x==None:
                break
            print("CDL SIM ERROR %2d %s"%(i+1,x), file=sys.stderr)
        self._engine.reset_errors()
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
        self._engine.reset()
        pass

    def step(self, cycles:int=1)->None:
        """
        Step for n cycles.
        """
        self._engine.step(cycles)
        self.display_all_errors()
        pass

    # def run_console( self, port:int=8745, locals:Dict[str,str]={} ) -> None:
    #     from .c_python_telnetd import c_python_telnet_server
    #     console_server = c_python_telnet_server( port=port, locals=locals )
    #     console_server.serve()
    #     pass
    pass

