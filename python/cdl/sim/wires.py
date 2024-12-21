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
from .exceptions import *
from .base      import BaseExecFile, split_name, join_name, Prefix
from .types     import WireType, WireTypeElement, WireTypeDictOrInt
from .hierarchy import Hierarchy, HierarchyElement
from .instantiable import Instantiable

from typing import Tuple, Any, Union, Dict, List, Callable, Type, Optional, Sequence, Set, cast, ClassVar, Iterable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .hardware import Hardware, HardwareDescription
    from .connectivity import Connectivity
    pass

ClockDict    = Dict[str,'Clock']
WiringDict   = Dict[str,'Wire']
WiringOrDict = Union['Wire','WiringDict']

#a Wire type instances - Wire, Clock, TimedAssign
#c Wire
class Wire(object):
    """
    This is an instance of a WireType - so conceptually an actual bunch of wires
    Potentially this is just a port, or all the inputs, etc of a module

    If this is a real set of wires in a design then it should have a name.
    The name may be explicit (the 'given_name') or it may be derived eventually by the wiring
    when instantiation occurs
    """
    given_name   : str
    derived_name : str
    wire_type : WireType
    _anonid: ClassVar[int] = 0

    #f get_name_from_class
    @classmethod
    def get_name_from_class(cls, hint:str="") -> str:
        name = "%s_%d"%(cls.__name__,cls._anonid)
        cls._anonid = cls._anonid+1
        return name

    #f __init__
    def __init__(self, wire_type:Optional[WireType]=None, size:Optional[int]=None, struct:Optional[WireTypeDictOrInt]=None, name:str=""):
        if wire_type is None:
            wire_type = WireType(size=size, struct=struct)
            pass
        assert wire_type is not None
        assert wire_type.is_defined()
        self.wire_type = wire_type
        self.given_name = name
        self.derived_name = ""
        pass

    #f get_name
    def get_name(self) -> str:
        if self.given_name   != "": return self.given_name
        return self.derived_name

    #f has_name
    def has_name(self) -> bool:
        return self.get_name()==""

    #f get_size
    def get_size(self) -> int:
        assert self.wire_type.is_endpoint()
        return self.wire_type.get_size()

    #f get_or_create_name
    def get_or_create_name(self, hint:str="") -> str:
        name = self.get_name()
        if name!="": return name
        self.derived_name = self.get_name_from_class(hint=hint)
        return self.derived_name

    #f iter
    def iter(self, name:Optional[str]=None, prefix:Prefix=[]) -> Iterable[Tuple[Prefix,str,WireTypeElement]]:
        if name is None: name=self.get_name()
        return self.wire_type.iter_element(name=name, prefix=prefix)

    #f flatten
    def flatten(self, name:Optional[str]=None, prefix:Prefix=[]) -> List[Tuple[str, 'WireTypeElement']]:
        result = []
        for (p,k,w) in self.iter(name=name, prefix=[]):
            result.append( (join_name(prefix=p, name=k), w) )
            pass
        return result

    #f __str__
    def __str__(self) -> str:
        name = self.get_name()
        return self.wire_type.as_string(name=name)

    #f All done
    pass

#c Clock - special type of wire that corresponds to a simulation clock - it can be a child of hardware, and so is instantiable
class Clock(Wire, Instantiable):
    init_delay: int
    cycles_high : int
    cycles_low : int
    def __init__(self, name:str="", init_delay:int=0, cycles_high:int=1, cycles_low:int=1):
        Instantiable.__init__(self)
        Wire.__init__(self, name=name, size=1)
        self.init_delay = init_delay
        self.cycles_high = cycles_high
        self.cycles_low = cycles_low
        pass

    #f instantiate
    def instantiate(self, hwex:'HardwareDescription', hw:'Hardware') -> None:
        name = self.get_or_create_name()
        Instantiable.set_instance_name(self, name)
        hwex.cdlsim_instantiation.clock(name, self.init_delay, self.cycles_high, self.cycles_low)
        pass

    #f add_connectivity
    def add_connectivity(self, hwex:'HardwareDescription', connectivity:'Connectivity') -> None:
        name = self.get_name()
        connectivity.add_clock_driver(self, name)
        pass

    #f __str__
    def __str__(self) -> str:
        return "Clock '%s'"%(Wire.__str__(self))
    pass

#c TimedAssign
class TimedAssign(Wire, Instantiable):
    """
    A timed assignment, often used for a reset sequence.
    """
    firstval : int
    wait : int
    afterval : int

    #f __init__
    def __init__(self, name:str="", size:int=1, init_value:int=0, wait:Optional[int]=None, later_value:Optional[int]=None):
        Instantiable.__init__(self)
        if wait is None:
            wait = 1<<31
            pass
        if later_value is None:
            later_value = init_value
            pass
        self.firstval = init_value
        self.wait = wait
        self.afterval = later_value
        Wire.__init__(self, name=name, size=size)
        pass

    #f instantiate
    def instantiate(self, hwex:'HardwareDescription', hw:'Hardware') -> None:
        name = self.get_or_create_name()
        self.set_instance_name(name)
        hwex.cdlsim_instantiation.wire(name)
        hwex.cdlsim_instantiation.assign(name, self.firstval, self.wait, self.afterval)
        pass

    #f add_connectivity
    def add_connectivity(self, hwex:'HardwareDescription', connectivity:'Connectivity') -> None:
        connectivity.add_wiring_source_driver(self, self)
        pass

    #f str_short
    def str_short(self)->str:
        return "timed_assign[%d](%d,%d,%d)"%(self.get_size(), self.firstval, self.wait, self.afterval)
    pass

#a Wiring - mapping something to wire instances
#c WiringHierarchyElement - element for the hierarchy, and it is a Wire
class WiringHierarchyElement(HierarchyElement):
    wired_to : Wire
    def __init__(self, wired_to:Wire):
        self.wired_to = wired_to
        return
    pass

#c WiringHierarchy
class WiringHierarchy(Hierarchy):
    """
    This is a hierarchical mapping to Wires

    It is constructed by adding elements of 'hierachical_name' -> Union[Wire, Dict['subhierarchical_name',Wire]]

    Used in module instantiations
      What a port (somewhere in a WaveHierarchy eventually) maps to
      So this may be a wire or WireHierarchy, or a dictionary of str:...

    Requires a full_name_list method that returns a list of all its elements

    """
    #f __init__
    def __init__(self) -> None:
        Hierarchy.__init__(self)
        pass

    #f create_subhierarchy
    def create_subhierarchy(self, name:str) -> Hierarchy:
        return self.set_subhierarchy(name, WiringHierarchy())

    #f create_hierarchy_element
    def create_hierarchy_element(self, name:str, element_args:WiringOrDict) -> None:
        WiringHierarchy().set_wired_to(wired_to=element_args)
        pass

    #f set_wired_to
    def set_wired_to(self, wired_to:WiringOrDict) -> None:
        if type(wired_to)==dict:
            wired_to_dict = cast(Dict[str,WiringDict], wired_to)
            for (sn, sig) in wired_to_dict.items():
                self.add_wiring(wired_to=sig, name=sn)
                return
            pass
        wired_to_wire = cast(Wire, wired_to)
        if self.is_defined(): raise Exception("Doubly wired")
        self.set_endpoint(WiringHierarchyElement(wired_to_wire))
        pass

    #f add_wiring
    def add_wiring(self, wired_to:WiringOrDict, name:Optional[str]=None) -> None:
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
    def iter_wiring(self,prefix:Prefix,name:str) -> Iterable[Tuple[Prefix,str,Wire]]:
        for (pfx, n, elt) in self.hierarchy_iter(name=name, prefix=prefix):
            assert isinstance(elt,WiringHierarchyElement)
            #  elt must be a WiringHierarchyElement
            yield (pfx, n, elt.wired_to)
        pass

    #f iter_fully - called by connectivity
    def iter_fully(self, name:str) -> Iterable[Tuple[str, Wire, Prefix, WireTypeElement]]:
        for (wire_prefix, wire_name, wire) in self.iter_wiring(prefix=[], name=name):
            for (elt_prefix, elt_name, elt) in wire.iter(name=wire_name, prefix=[]):
                full_name = join_name(prefix=wire_prefix+elt_prefix, name=elt_name)
                yield (full_name, wire, elt_prefix+[elt_name], elt)
                pass
            pass
        pass

    #f full_sized_name_list
    def full_sized_name_list(self, name:str) -> List[str]:
        result = []
        for (full_name, _, _, elt) in self.iter_fully(name):
            result.append("%s[%d]"%(full_name,elt.get_size()))
            pass
        return result

    #f flatten - unused at present
    def flatten(self, name:str) -> List[Tuple[str, Wire, Prefix, WireTypeElement]]:
        result = []
        for t in self.iter_fully(name):
            result.append(t)
            pass
        return result

    #f as_string
    def as_string(self, name:str="<wiring>") -> str:
        r="{"
        for (full_name, wire, elt_prefix, elt) in self.iter_fully(name):
            r += "%s[%d]:%s:%s"%(full_name,elt.get_size(),wire.get_name(),join_name(elt_prefix,name=""))
            pass
        r+="}"
        return r
    def __str__(self) -> str:
        return self.as_string()

    #f all done
    pass

