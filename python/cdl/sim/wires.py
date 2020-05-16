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
from .types     import *
from .base      import BaseExecFile, split_name, join_name
from .engine    import Engine, SimulationExecFile, HardwareExecFile, VcdFile
from .instantiable import Instantiable
from .exceptions import *
from .bit_vector import Value, bv, bvbundle
from .hierarchy import Hierarchy, HierarchyElement
from typing import Tuple, Any, Union, Dict, List, Callable, Type, Optional, Sequence, Set, cast, ClassVar, Iterable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .hardware import Hardware, HardwareDescription
    from .connectivity import Connectivity
    pass

#a Wires
#c WireBase
class WireBase(object):
    _name : str
    _full_name: str
    _anonid: ClassVar[int] = 0
    def iter_element(self, name:Optional[str]=None, prefix:Prefix=[]) -> Iterable[Tuple[Prefix,str,'Wire']]: ...

    #f get_name
    @classmethod
    def get_name(cls, hint:str="") -> str:
        name = "%s_%d"%(cls.__name__,cls._anonid)
        cls._anonid = cls._anonid+1
        return name

    #f assure_name
    def assure_name(self, hint:str="") -> None:
        if self._name=="":
            self._name = self.get_name(hint=hint)
            pass
        pass

    #f __init__
    def __init__(self, name:str="", full_name:str=""):
        self._name = name
        self._full_name = full_name
        pass

    #f flatten
    def flatten(self, name:str) -> List[Tuple[str, 'WireBase']]:
        return [(name, self)]

    #f passed - for wires that are childen of hardware
    def passed(self) -> bool: return True

    #f __str__
    def __str__(self) -> str:
        return self._full_name

    #f has_name
    def has_name(self) -> bool:
        if not hasattr(self, "_name"): return False
        if self._name is None: return False
        if self._name=="": return False
        return True

    #f full_name_list
    def full_name_list(self, name:str, prefix:Prefix=[]) -> Prefix:
        """
        Return list of names for a wire called 'name' within this prefix
        If this were a bundle, the list would be longer
        """
        return ["__".join(prefix) + self._name]

    #f flatten_element
    def flatten_element(self, name:str) -> Dict[str,'Wire']:
        result = {}
        for (p,k,w) in self.iter_element(name=name, prefix=[]):
            result[join_name(prefix=p, name=k)] = w
            pass
        return result

    #f All done
    pass

#c Wire - an endpoint in a Wiring hierarchy
class Wire(WireBase, HierarchyElement):
    """
    The object that represents a wire.
    """
    _size : int

    #f __init__
    def __init__(self, name:str="", size:int=1, full_name:Optional[str]=None):
        if full_name is None:
            full_name_nn = name
            pass
        else:
            full_name_nn = full_name
            pass
        WireBase.__init__(self, name=name, full_name=full_name_nn)
        self._size = size
        pass

    #f str_short
    def str_short(self) -> str:
        if self._name=="":
            return "<unnamed>[%d]"%(self._size)
        return "%s[%d]"%(self._name, self._size)

    #f __str__
    def __str__(self) -> str:
        return self.str_short()

    #f size
    def size(self) -> int:
        return self._size

    #f iter_element
    def iter_element(self, name:Optional[str]=None, prefix:Prefix=[]) -> Iterable[Tuple[Prefix,str,'Wire']]:
        if name is None:
            yield(prefix, self._name, self)
            pass
        else:
            yield(prefix,name,self)
            pass
        pass

    #f All done
    pass

#c WireHierarchy
class WireHierarchy(WireBase, Hierarchy):
    """
    Fully flattened hierarchy
    This is a dictionary of dictionaries of ... of Wires
    """
    #f __init__
    def __init__(self) -> None:
        Hierarchy.__init__(self)
        pass

    #f create_subhierarchy
    def create_subhierarchy(self, name:str) -> Hierarchy:
        return self.set_subhierarchy(name, WireHierarchy())

    #f create_hierarchy_element
    def create_hierarchy_element(self, name:str, element_args:Any) -> None:
        (full_name,size) = element_args
        x = self.create_subhierarchy(name)
        elt = Wire(name=name, size=size, full_name=full_name)
        x.set_endpoint(elt)
        return

    #f get_element
    def get_element(self, name:str) -> Optional['WireHierarchy']:
        x = Hierarchy.get_element(self, name)
        return cast(Optional['WireHierarchy'], x)

    #f add_wire
    def add_wire(self, hierarchical_name:str, size:int) -> None:
        """
        Add a wire of the bit size with full hierarchical name in to the dictionary hierarchy
        """
        print("adding wire",hierarchical_name,size)
        return self.hierarchy_add_element(name=hierarchical_name, element_args=(hierarchical_name,size))

    #f iter_element
    def iter_element(self, name:Optional[str]=None, prefix:Prefix=[]) -> Iterable[Tuple[Prefix,str,Wire]]:
        # print("iter_element of wirehierarchy",self.is_defined(), self.is_endpoint())
        for (pfx, n, elt) in self.hierarchy_iter(name=name, prefix=prefix):
            wire = cast(Wire, elt)
            yield (pfx, n, wire)
            pass
        pass

    #f get_wiring - is this used?
    def get_wiring(self, name:str) -> Optional[Wiring]:
        opt_h = self.get_hierarchical_element(name)
        return cast(Optional[Wiring],opt_h)

    #f str_short
    def str_short(self) -> str:
        r = ""
        for (pfx,k,w) in self.iter_element():
            r+=" %s:%s"%(join_name(pfx,k,"."),str(w))
            pass
        return r

    #f __str__
    def __str__(self) -> str:
        return self.str_short()

    #f All done
    pass

#c Clock - special type of wire that corresponds to a simulation clock - it can be a child of hardware, and so is instantiable
class Clock(WireBase, Instantiable):
    def __init__(self, name:str="", init_delay:int=0, cycles_high:int=1, cycles_low:int=1):
        Instantiable.__init__(self)
        WireBase.__init__(self, name=name)
        self._init_delay = init_delay
        self._cycles_high = cycles_high
        self._cycles_low = cycles_low
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

    #f __str__
    def __str__(self) -> str:
        return str(self.__repr__())
    pass

#c TimedAssign
class TimedAssign(Wire, Instantiable):
    """
    A timed assignment, often used for a reset sequence.
    """
    _firstval : int
    _wait : int
    _afterval : int
    _size : int

    #f __init__
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
        Wire.__init__(self, name=name, size=size)
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

    #f str_short
    def str_short(self)->str:
        return "timed_assign[%d](%d,%d,%d)"%(self._size,self._firstval,self._wait,self._afterval)
    pass

#c WiringHierarchy
#c WiringHierarchyElement - element for the hierarchy, and it is a Wiring
class WiringHierarchyElement(HierarchyElement):
    wired_to : Wiring
    def __init__(self, wired_to:Wiring):
        self.wired_to = wired_to
        return
    pass

class WiringHierarchy(Hierarchy):
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
    #f __init__
    def __init__(self) -> None:
        Hierarchy.__init__(self)
        pass

    #f create_subhierarchy
    def create_subhierarchy(self, name:str) -> Hierarchy:
        return self.set_subhierarchy(name, WiringHierarchy())

    #f create_hierarchy_element
    def create_hierarchy_element(self, name:str, element_args:WiringDict) -> None:
        x = WiringHierarchy()
        x.set_wired_to(wired_to=element_args)
        pass

    #f set_wired_to
    def set_wired_to(self, wired_to:WiringDict) -> None:
        if type(wired_to)==dict:
            wired_to_dict = cast(Dict[str,WiringDict], wired_to)
            for (sn, sig) in wired_to_dict.items():
                self.add_wiring(wired_to=sig, name=sn)
                return
            pass
        wired_to_wiring = cast(Wiring, wired_to)
        if self.is_defined(): raise Exception("Doubly wired")
        elt = WiringHierarchyElement(wired_to_wiring)
        self.set_endpoint(elt)
        pass

    #f add_wiring
    def add_wiring(self, wired_to:WiringDict, name:Optional[str]=None) -> None:
        """
        name may be none if the wiring dictionary should be added directly
          This happens, for example, at an input or output
          If wired_to is a wire at this point then there is no real name
          The name is really a subname of the parent
        """
        if name is None:
            self.set_wired_to(wired_to)
            pass
        else:
            self.hierarchy_add_element(name=name, element_args=wired_to)
            pass
        pass

    #f iter_wiring
    def iter_wiring(self,prefix:Prefix,name:str) -> Iterable[Tuple[Prefix,str,Wiring]]:
        for (pfx, n, elt) in self.hierarchy_iter(name=name, prefix=prefix):
            assert isinstance(elt,WiringHierarchyElement)
            #  elt must be a WiringHierarchyElement
            yield (pfx, n, elt.wired_to)
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
            print("fsnl %s '%s' %s '%s'"%(str(pfx),wn,str(w),ws))
            # Does not work if w is a WireHierarchy
            assert isinstance(w,Wire)
            if w._size>1:
                ws += "[%d]"%w._size
                pass
            result.append(ws)
            pass
        return result

    #f flatten - called by connectivity
    def flatten(self, name:str) -> Dict[str, Wire]:
        d={}
        for (pfx, wn, w) in self.iter_wiring(prefix=[], name=name):
            name = join_name(prefix=pfx[:-1],name=pfx[-1])
            for (k,v) in w.flatten(name): # Currently w is a Wire so this is trivial
                d[k] = cast(Wire,v)
                pass
            pass
        print("Flattened to ",d)
        return d

    #f __str__
    def __str__(self) -> str:
        r = "WiringHierarchy "
        for (pfx, wn, w) in self.iter_wiring(prefix=[], name=""):
            r += "%s '%s' : %s\n"%(str(pfx), wn, w.str_short())
            # r += "%s : %s\n"%(join_name(pfx,wn), w.str_short())
            pass
        return r

    #f all done
    pass

