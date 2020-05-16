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
import sys, os
from .base import BaseExecFile
from .engine    import Engine, SimulationExecFile, HardwareExecFile, VcdFile
from .instantiable import Instantiable
from .exceptions import *
from .bit_vector import Value, bv, bvbundle

from typing import Tuple, Any, Union, Dict, List, Callable, Type, Optional, Sequence, Set, cast, ClassVar, Iterable

Wiring     = Union['Wire','WireHierarchy']
WiringDict = Dict[str,Wiring]
ClockDict = Dict[str,'Clock']

#a Useful functions
def split_name(name:str, sep:str="__") -> Tuple[Optional[str],str]:
    name_split = name.split(sep, 1)
    if len(name_split)<2: return (None, name)
    return (name_split[0], name_split[1])

def join_name(prefix:List[str], name:str, sep:str="__") -> str:
    if len(prefix)==0: return name
    return sep.join(prefix)+sep+name

#a Wires
#c WireBase
class WireBase(object): # was _nameable
    def _name_list(self, inname:str) -> List[str]: ...
    # for input signals (should be a subtype)
    def value(self) -> Value: ...
    # for output signals (should be a subtype)
    def drive(self, value:Value) -> None: ...
    def reset(self, value:Value) -> None: ...
    _name : str
    _size : int
    _full_name: str
    _anonid: ClassVar[int] = 0
    @classmethod
    def get_name(cls, hint:str="") -> str:
        name = "%s_%d"%(cls.__name__,cls._anonid)
        cls._anonid = cls._anonid+1
        return name
    def assure_name(self, hint:str="") -> None:
        if self._name=="":
            self._name = self.get_name(hint=hint)
            pass
        pass

    #f __init__
    def __init__(self, name:str="", size:int=1, full_name:str=""):
        self._size = size
        self._name = name
        self._full_name = full_name
        pass

    #f flatten
    def flatten(self, name:str) -> List[Tuple[str, 'WireBase']]:
        return [(name, self)]

    #f passed - for wires that are childen of hardware
    def passed(self) -> bool: return True

    def __str__(self) -> str:
        return self._full_name

    def has_name(self) -> bool:
        if not hasattr(self, "_name"): return False
        if self._name is None: return False
        if self._name=="": return False
        return True

    def full_name_list(self, name:str, prefix:List[str]=[]) -> List[str]:
        """
        Return list of names for a wire called 'name' within this prefix
        If this were a bundle, the list would be longer
        """
        return ["__".join(prefix) + self._name]

    def str_short(self) -> str:
        return "%s[%d]"%(self._name, self._size)
    pass

#c Wire - nameable that is driven_by something and drives something
class Wire(WireBase):
    """
    The object that represents a wire.
    """
    # _cdl_signal : PyEngSim.Global # Global wire created in hardware when the hardware is built - passed in at _connect_cdl_signal
    _instantiated_name : str # Given to the wire in the hardware when the hardware is built
    _drives :   List['Wire']
    _driven_by: Optional['Wire']
    _size : int
    _cdl_signal : Optional[Any]
    _reset_value : Optional[int]

    #f __init__
    def __init__(self, name:str="", size:int=1, full_name:Optional[str]=None):
        if full_name is None:
            full_name_nn = name
            pass
        else:
            full_name_nn = full_name
            pass
        WireBase.__init__(self, name=name, size=size, full_name=full_name_nn)
        self._drives = []
        self._driven_by = None
        self._cdl_signal = None
        self._reset_value = None
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

    #f All done
    pass

#c WireHierarchy
class WireHierarchy(object):
    """
    Fully flattened hierarchy
    This is a dictionary of dictionaries of ... of Wires
    """
    wiring : WiringDict # Recursive really

    #f __init__
    def __init__(self) -> None:
        self.wiring = {}
        pass

    #f add_wire
    def add_wire(self, full_name:str, size:int) -> Wire:
        """
        Add a wire of the bit size with full hierarchical name in to the dictionary hierarchy
        """
        return self.add_wire_hierarchy(self.wiring, full_name, full_name, size)

    #f add_wire_hierarchy
    def add_wire_hierarchy(self, wiring_dict:WiringDict, full_name:str, remaining_name:str, size:int) -> Wire:
        (root, rest) = split_name(remaining_name)
        if root is None:
            if rest in wiring_dict:
                raise Exception("Bug in wire bundle in adding '%s' as part of '%s' - duplicate wire or wire which is also a bundle"%(rest, full_name))
            wire = Wire(name=rest, size=size, full_name=full_name)
            wiring_dict[rest] = wire
            return wire
        if root not in wiring_dict: wiring_dict[root] = {}
        if type(wiring_dict[root])!=dict:
            raise Exception("Bug in wire bundle in adding '%s' as part of '%s' - already a wire, now also a bundle"%(remaining_name, full_name))
        return self.add_wire_hierarchy(wiring_dict[root], full_name=full_name, remaining_name=rest, size=size)

    #f get_element
    def get_element(self, name:str) -> Union[None, Wire, Dict[str,Any]]:
        if name not in self.wiring: return None
        return self.wiring[name]

    #f iter_element
    def iter_element(self, w:Union[Wire, Dict[str,Any]], name:str, prefix:List[str]=[]) -> Iterable[Tuple[List[str],str,Wire]]:
        if isinstance(w,Wire):
            yield(prefix,name,w)
            pass
        else:
            for (k,w) in w.items():
                self.iter_elementdict(w,k,prefix+[name])
            pass
        pass

    #f flatten_element
    def flatten_element(self, name:str, element:Union[Wire, Dict[str,Any]]) -> Dict[str,Wire]:
        result = {}
        for (p,k,w) in self.iter_element(element, name=name, prefix=[]):
            result[join_name(prefix=p, name=k)] = w
            pass
        return result

    #f iter_elements
    def iter_elements(self, prefix:List[str]=[]) -> Iterable[Tuple[List[str],str,Wire]]:
        return self.iter_element(self.wiring, "", prefix)

    #f flatten - not used
    def flatten(self, name:str) -> List[Tuple[str, WireBase]]:
        result = []
        for (n,w) in self.wiring:
            result.extend(self.flatten_element(n,w))
            pass
        return result

    #f as_flattened_list
    def as_flattened_list(self, prefix:List[str]=[]):
        result = []
        for (pfx,k,w) in self.iter_elements(prefix):
            result.append(pfx,k,w)
            pass
        return result

    #f get_wiring - is this used?
    def get_wiring(self, wiring_dict:Dict[str,Wiring], remaining_name:str) -> Wiring:
        (root, rest) = split_name(remaining_name)
        if root is None:
            if rest in wiring_dict: return wiring_dict[rest]
            return None
        if root not in wiring_dict: return None
        if type(wiring_dict[root])!=dict:
            raise Exception("Bug in wire bundle in finding '%s' - it is a wire, not a bundle"%remaining_name)
        return self.get_wiring(wiring_dict[root], remaining_name=rest)

    #f str_short
    def str_short(self) -> str:
        r = ""
        for (pfx,k,w) in self.iter_elements():
            r+=" %s[%d]"%(join_name(pfx,k,"."),w.size())
            pass
        return r

    #f __str__
    def __str__(self):
        return self.str_short()
    #f All done
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
    _reset_value : Optional[bvbundle]
    def __init__(self, name:str="", bundletype:Optional[WireBundleDefn]=None, **kw:Any):
        WireBase.__init__(self, name=name, full_name=name)
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
        pass

    #f _name_list
    def _name_list(self, inname:str) -> List[str]:
        retval = []
        for i in self._dict:
            subval = self._dict[i]._name_list(i)
            for j in subval:
                retval.append("%s__%s" % (inname, j))
        return retval

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

#c Clock - special type of wire that corresponds to a simulation clock - it can be a child of hardware, and so is instantiable
class Clock(WireBase, Instantiable):
    _drives :   List['clock'] = []
    _driven_by: Optional['clock'] = None
    _size : int
    def __init__(self, name:str="", init_delay:int=0, cycles_high:int=1, cycles_low:int=1):
        Instantiable.__init__(self)
        self._init_delay = init_delay
        self._cycles_high = cycles_high
        self._cycles_low = cycles_low
        WireBase.__init__(self, name=name, size=1)
        pass

    #f instantiate
    def instantiate(self, hwex:'HardwareDescription', hw:'Hardware') -> None:
        self.assure_name()
        print("Create clock driving %s"%(self._name))
        hwex.cdlsim_instantiation.clock(self._name, self._init_delay, self._cycles_high, self._cycles_low)
        pass

    #f add_connectivity
    def add_connectivity(self, hwex:'HardwareDescription', connectivity:'Connectivity') -> None:
        print("Driving clock %s"%self._name)
        connectivity.add_clock_driver(self, self._name)
        pass
    def __str__(self):
        return str(self.__repr__())
    pass

#c TimedAssign
class TimedAssign(WireBase, Instantiable):
    """
    A timed assignment, often used for a reset sequence.
    """
    _firstval : int
    _wait : int
    _afterval : int
    _name : str
    def __init__(self, name:str="", size:int=1, init_value:int=0, wait:Optional[int]=None, later_value:Optional[int]=None):
        Instantiable.__init__(self)
        if wait is None:
            wait = 1<<31
            pass
        if later_value is None:
            later_value = init_value
            pass
        # self._outputs = {"sig": signal}
        # self._ports = Ports(clocks=[], inputs=[], outputs=[["sig", signal._size]])
        self._firstval = init_value
        self._wait = wait
        self._afterval = later_value
        WireBase.__init__(self, name=name, size=size)
        pass

    #f instantiate
    def instantiate(self, hwex:'HardwareDescription', hw:'Hardware') -> None:
        self.assure_name()
        print("Create timed_assign driving '%s'"%(self._name))
        print(self._name, self._firstval, self._wait, self._afterval)
        hwex.cdlsim_instantiation.wire(self._name)
        hwex.cdlsim_instantiation.assign(self._name, self._firstval, self._wait, self._afterval)
        pass

    #f add_connectivity
    def add_connectivity(self, hwex:'HardwareDescription', connectivity:'Connectivity') -> None:
        connectivity.add_wiring_source_driver(self, self)
        pass
    def str_short(self):
        return "timed_assign[%d](%d,%d,%d)"%(self._size,self._firstval,self._wait,self._afterval)
    pass

#c WiringHierarchy
class WiringHierarchy(object):
    """
    Not flattened hierarchy - endpoints may be WireHierarchy's
    This is either an endpoint or a dictionary str -> WiringHierarchy (i.e. recursive)

    The input is:
    Wiring     = Union['Wire','WiringHierarchy',Dict[str,Wiring]]

    Used in module instantiations
      What a port (somewhere in a WaveHierarchy eventually) maps to
      So this may be a wire or WireHierarchy, or a dictionary of str:...

    Requires a full_name_list method that returns a list of all its elements

    Endpoint : Union[Wire, WireHierarchy]
    wiring : Dict[str,Union[Endpoint,'WiringHierarchy']]

    """
    _is_endpoint : bool
    endpoint : Wiring
    wiring : Dict[str,'WiringHierarchy']

    #f __init__
    def __init__(self):
        self.wiring = {}
        pass

    #f get_element
    def get_element(self, name):
        if self._is_endpoint: return None
        if name not in self.wiring: return None
        return self.wiring[name]

    #f add_wiring
    def add_wiring(self, wired_to:WiringDict, name:Optional[str]=None) -> None:
        """
        name may be none if the wiring dictionary should be added directly
        name may be somewhat flattened
        WireDict = Union[Wire,WireHierarchy,Dict[str,WireDict]]
        """
        if name is not None:
            (root, rest) = split_name(name)
            if root is not None:
                if root not in self.wiring: self.wiring[root] = WiringHierarchy()
                if not isinstance(self.wiring[root], WiringHierarchy):
                    raise Exception("Mis wired")
                return self.wiring[root].add_wiring(name=rest, wired_to=wired_to)
            else:
                if name in self.wiring:
                    raise Exception("Mis wired - already wired")
                self.wiring[name] = WiringHierarchy()
                return self.wiring[name].add_wiring(name=None, wired_to=wired_to)
            pass
        if type(wired_to)==dict:
            for (sn, sig) in wired_to.items():
                self.add_wiring(wired_to=sig, name=sn)
                return
            pass
        if len(self.wiring)!=0: raise Exception("Doubly wired")
        self._is_endpoint = True
        self.endpoint = wired_to
        pass

    #f iter_wiring
    def iter_wiring(self,prefix:List[str],name:str) -> Iterable[Tuple[List[str],str,Wiring]]:
        if self._is_endpoint:
            yield (prefix, name, self.endpoint)
            return
        prefix = prefix + [name]
        for (wn, w) in self.wiring.items():
            w.iter_wiring(prefix=prefix,name=wn)
            pass
        pass

    #f full_name_list - not used?
    def full_name_list(self, name:str) -> List[str]:
        result = []
        for (pfx, wn, _) in self.iter_wiring(prefix=[], name=name):
            result.append(join_name(pfx,wn))
            pass
        return result

    #f full_sized_name_list
    def full_sized_name_list(self, name:str) -> List[str]:
        result = []
        for (pfx, wn, w) in self.iter_wiring(prefix=[], name=name):
            ws = join_name(pfx,wn)
            if w._size>1:
                ws += "[%d]"%w._size
                pass
            result.append(ws)
            pass
        return result

    #f flatten
    def flatten(self, name:str) -> Dict[str, Wire]:
        d={}
        if self._is_endpoint:
            for (k,v) in self.endpoint.flatten(name):
                d[k]=v
                pass
            return d
        raise Exception("die")

    #f __str__
    def __str__(self) -> str:
        r = ""
        for (pfx, wn, w) in self.iter_wiring(prefix=[], name=""):
            r += "%s : %s\n"%(join_name(pfx,wn), w.str_short())
            pass
        return r

    #f all done
    pass

#c WiringSet
class xWiringSet(object):
    """
    Used in Ports:
     fully flattened (endpoints must be individual Wires)
     endpoints are local to the instance

    Wiring          = Wire | Dict[str,Wiring]
    self.wiring     = Wiring
    """
    wiring : WireHierarchy

    #f __init__
    def __init__(self, wiring:List[Tuple[str,int]]):
        self.wiring = WireHierarchy()
        for (full_name, size) in wiring:
            print(full_name, size)
            self.wiring.add_wire(full_name, size)
            pass
        pass

    #f get_element
    def get_element(self, name:str) -> WiringHierarchy:
        return self.wiring.get_element(name)

    #f get_set
    def get_set(self, full_name:str) -> Union[None, Wire, Dict[str,Any]]:
        return self.get_set_from_dict( self.wiring, remaining_name=full_name)

    #f __str__
    def __str__(self) -> str:
        return str(self.wiring)
    pass

