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
from .base import BaseExecFile
from .exceptions import *
from .instantiable import Instantiable
from .wires import WireBase, Wire, Wiring, WiringDict, Clock, WireHierarchy, WiringHierarchy
from .modules import Module

from typing import Tuple, Any, Union, Dict, List, Callable, Type, Optional, Sequence, Set, cast, ClassVar

#a Connectivity
Driver = Tuple[Any,str]
class WireMapping(object):
    def __init__(self, wire:Wire)->None:
        self.wire = wire
        self.is_global_wire = False
        self.driven_by = None
        self.drives = []
        pass
    def add_source(self, instance, port_element_name, port_wire)->None:
        if self.driven_by is not None: raise Exception("argh")
        if self.is_global_wire: raise Exception("argh")
        self.driven_by = (instance, port_element_name, port_wire)
        pass
    def set_is_global_wire(self) -> None:
        if self.driven_by is not None: raise Exception("argh")
        if self.is_global_wire: raise Exception("argh")
        self.is_global_wire = True
        pass
    def add_sink(self, instance, port_element_name, port_wire)->None:
        self.drives.append((instance, port_element_name, port_wire))
        pass
    def instantiate(self, hwex:'HardwareDescription', hw:'Hardware') -> None:
        if (self.driven_by is None) and (not self.is_global_wire):
            print("undriven signal")
            return
            raise Exception("undriven signal")

        if self.driven_by is not None:
            (instance, port_element_name, port_name) = self.driven_by
            self.wire.assure_name(port_name)
            driver_name = self.wire._name
            print("create wire %s[%d]"%(driver_name, self.wire._size))
            hwex.cdlsim_instantiation.wire("%s[%d]"%(driver_name, self.wire._size))
            print("driven by %s.%s"%(instance._name, port_name))
            hwex.cdlsim_instantiation.drive(driver_name, "%s.%s"%(instance._name, port_name))
            pass
        else:
            self.wire.assure_name()
            driver_name = self.wire._name
            pass
        for (instance,port_element_name, port_name) in self.drives:
            print("drives %s.%s"%(instance._name, port_name))
            hwex.cdlsim_instantiation.drive("%s.%s"%(instance._name, port_name), driver_name)
            pass
        pass
    pass

class ClockMapping(object):
    def __init__(self, clock:Clock)->None:
        self.clock = clock
        print("New clock %s"%clock)
        self.driver = None
        self.drives = []
        pass
    def set_drive(self, global_name)->None:
        if self.driver is not None: raise Exception("argh")
        self.driver = global_name
        pass
    def add_target(self, instance, port_name)->None:
        self.drives.append((instance,port_name))
        pass
    def instantiate(self, hwex:'HardwareDescription', hw:'Hardware') -> None:
        if self.driver is None: raise Exception("blah")
        for (instance,port_name) in self.drives:
            hwex.cdlsim_instantiation.drive("%s.%s"%(instance._name, port_name), self.driver)
            pass
        pass
    pass
class Connectivity(object):
    clocks : Dict['Clock',ClockMapping]
    signals: Dict[Wire,WireMapping]
    def __init__(self) -> None:
        self.clocks = {}
        self.signals = {}
        pass
    def add_clock_driver(self, clock:Clock, global_name:str) -> None:
        if clock not in self.clocks: self.clocks[clock] = ClockMapping(clock)
        self.clocks[clock].set_drive(global_name)
        pass
    def add_clock_sink(self, instance, port_name, clock:Clock) -> None:
        if clock not in self.clocks: self.clocks[clock] = ClockMapping(clock)
        self.clocks[clock].add_target(instance, port_name)
        pass
    def add_wiring_sink(self, instance:Instantiable, port_name:str, ports:WireHierarchy, wiring:WiringHierarchy):
        if True:
            print("Port %s"%port_name)
            print("Input ports:%s"%str(ports.get_element(port_name)))
            print("Wiring %s:"%str(wiring))
            pass
        port_hierarchy : Union[None, Wire, Dict[str,Any]] = ports.get_element(port_name)
        if port_hierarchy is None: raise Exception("Bad wiring")
        port_elements = ports.flatten_element(element=port_hierarchy,name=port_name)
        wired_to_elements = wiring.flatten(port_name)
        print(str(port_elements))
        print(wired_to_elements)
        for (n,w) in wired_to_elements.items():
            if n not in port_elements: raise Exception("bad wiring")
            if w not in self.signals:
                self.signals[w] = WireMapping(w)
                pass
            self.signals[w].add_sink(instance,n,port_elements[n])
            pass
        #        hwex.report_error("module %s has wiring specified to input '%s' but the hardware module does not have that port"%(self._name, name))
        pass
    def add_wiring_source_driver(self, instance:Instantiable, wire:Wire):
        if wire not in self.signals:
            self.signals[wire] = WireMapping(wire)
            pass
        self.signals[wire].set_is_global_wire()
        pass

    def add_wiring_source(self, instance:Instantiable, port_name:str, ports:WireHierarchy, wiring:Wiring):
        if True:
            print("Port %s"%port_name)
            print("Output ports:%s"%str(ports.get_element(port_name)))
            print("Wiring %s:"%str(wiring))
            pass
        port_hierarchy : Union[None, Wire, Dict[str,Any]] = ports.get_element(port_name)
        if port_hierarchy is None: raise Exception("Bad wiring")
        port_elements = ports.flatten_element(element=port_hierarchy,name=port_name)
        wired_to_elements = wiring.flatten(port_name)
        print(str(port_elements))
        print(wired_to_elements)
        for (n,w) in wired_to_elements.items():
            if n not in port_elements: raise Exception("bad wiring")
            if w not in self.signals:
                self.signals[w] = WireMapping(w)
                pass
            self.signals[w].add_source(instance,n,port_elements[n])
            pass

        #    wired_to = self._ports.get_inputs(name)
        #    if wired_to is not None:
        #        connectivity.add_wiring_sink(self, name, wiring, wired_to)
        #        pass
        #    else:
        #        hwex.report_error("module %s has wiring specified to input '%s' but the hardware module does not have that port"%(self._name, name))
        #        pass
        # wired_to is fully flattened, dictionary is fully hierarchical
        pass
        #    wired_from = self._ports.get_output_set(name)
        #    if wired_from is not None:
        #        connectivity.add_wiring_source(self, name, wiring, wired_from)
        #        pass
        #    else:
        #        hwex.report_error("module %s has wiring specified from output '%s' but the hardware module does not have that port"%(self._name, name))
        #        pass
        #    pass
        pass
    #f check
    def check(self, hwex:'HardwareDescription', hw:'Hardware') -> None:
        pass
    #f connect_wires
    def connect_wires(self, hwex:'HardwareDescription', hw:'Hardware') -> None:
        print("Connect wires")
        for (c,cm) in self.clocks.items():
            print(c)
            cm.instantiate(hwex,hw)
            pass
        for (s,sm) in self.signals.items():
            print(s)
            sm.instantiate(hwex,hw)
            pass
        print("Done")

    #f blah
    def blah(io_list:List[Tuple[str,int]]):
        if cdl_object and hasattr(cdl_object, io[0]) and self._auto_wire_same_name:
            print("Connecting CDL signal %s" % repr(getattr(cdl_object, io[0])))
            thewire._connect_cdl_signal(getattr(cdl_object,io[0]))
            pass
        else:
            #print "No CDL signal!"
            pass
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

    pass

