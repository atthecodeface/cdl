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
from .types import *
from .wires import WireBase, Wire, Clock, WireHierarchy, WiringHierarchy
from .modules import Module

from typing import Tuple, Any, Union, Dict, List, Callable, Type, Optional, Sequence, Set, cast, ClassVar
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .hardware import Hardware, HardwareDescription
    pass

#a Connectivity
#t Driver
Connection = Tuple[Instantiable,str,Wire]
ClockPort  = Tuple[Instantiable, str]

#c WireMapping
class WireMapping(object):
    wire            : Wire
    is_global_wire  : bool
    driven_by       : Optional[Connection]
    drives          : List[Connection]
    #f __init__
    def __init__(self, wire:Wire)->None:
        self.wire = wire
        self.is_global_wire = False
        self.driven_by = None
        self.drives = []
        pass

    #f add_source
    def add_source(self, instance:Instantiable, port_element_name:str, port_wire:Wire)->None:
        if self.driven_by is not None: raise Exception("argh")
        if self.is_global_wire: raise Exception("argh")
        self.driven_by = (instance, port_element_name, port_wire)
        pass

    #f set_is_global_wire
    def set_is_global_wire(self) -> None:
        if self.driven_by is not None: raise Exception("argh")
        if self.is_global_wire: raise Exception("argh")
        self.is_global_wire = True
        pass

    #f add_sink
    def add_sink(self, instance:Instantiable, port_element_name:str, port_wire:Wire)->None:
        self.drives.append((instance, port_element_name, port_wire))
        pass

    #f instantiate
    def instantiate(self, hwex:'HardwareDescription', hw:'Hardware') -> None:
        if (self.driven_by is None) and (not self.is_global_wire):
            print("undriven signal")
            return
            raise Exception("undriven signal")

        if self.driven_by is not None:
            (instance, port_element_name, port_wire) = self.driven_by
            port_name = port_wire.get_name()
            driver_name = self.wire.get_or_create_name(port_element_name)
            size = self.wire.get_size()
            print("create wire %s[%d]"%(driver_name, size))
            print("driven by %s.%s"%(instance.get_instance_name(), port_name))
            hwex.cdlsim_instantiation.wire("%s[%d]"%(driver_name, size))
            hwex.cdlsim_instantiation.drive(driver_name, "%s.%s"%(instance.get_instance_name(), port_name))
            pass
        else:
            driver_name = self.wire.get_or_create_name()
            pass
        for (instance,port_element_name, port_wire) in self.drives:
            port_name = port_wire.get_name()
            print("drives %s.%s"%(instance.get_instance_name(), port_name))
            hwex.cdlsim_instantiation.drive("%s.%s"%(instance.get_instance_name(), port_name), driver_name)
            pass
        pass
    pass

#c ClockMapping
class ClockMapping(object):
    clock           : Clock
    driver          : Optional[str]
    drives          : List[ClockPort]
    #f __init__
    def __init__(self, clock:Clock)->None:
        self.clock = clock
        self.driver = None
        self.drives = []
        pass

    #f set_drive
    def set_drive(self, global_name:str)->None:
        if self.driver is not None: raise Exception("argh")
        self.driver = global_name
        pass

    #f add_target
    def add_target(self, instance:Instantiable, port_name:str)->None:
        self.drives.append((instance,port_name))
        pass

    #f instantiate
    def instantiate(self, hwex:'HardwareDescription', hw:'Hardware') -> None:
        if self.driver is None: raise Exception("blah")
        for (instance,port_name) in self.drives:
            hwex.cdlsim_instantiation.drive("%s.%s"%(instance.get_instance_name(), port_name), self.driver)
            pass
        pass
    pass

#c Connectivity
class Connectivity(object):
    clocks : Dict['Clock',ClockMapping]
    signals: Dict[Wire,WireMapping]

    #f __init__
    def __init__(self, hwex:'HardwareDescription', hw:'Hardware') -> None:
        self.clocks = {}
        self.signals = {}
        self.hwex = hwex
        self.hw = hw
        pass

    #f add_clock_driver
    def add_clock_driver(self, clock:Clock, global_name:str) -> None:
        if clock not in self.clocks: self.clocks[clock] = ClockMapping(clock)
        self.clocks[clock].set_drive(global_name)
        pass
    #f add_clock_sink
    def add_clock_sink(self, instance:Instantiable, port_name:str, clock:Clock) -> None:
        if clock not in self.clocks: self.clocks[clock] = ClockMapping(clock)
        self.clocks[clock].add_target(instance, port_name)
        pass
    #f add_wiring_sink
    def add_wiring_sink(self, instance:Instantiable, port_name:str, ports:WireHierarchy, wiring:WiringHierarchy) -> None:
        if True:
            print("Port %s"%port_name)
            print("Input ports:%s"%str(ports.get_element(port_name)))
            print("Wiring: '%s'"%str(wiring))
            pass
        port_hierarchy : Optional[WireHierarchy] = ports.get_element(port_name)
        if port_hierarchy is None:
            self.hwex.report_error("Could not find input port '%s' on instance '%s'"%(port_name, instance.get_instance_name()))
            return
        port_elements = port_hierarchy.flatten_element(name=port_name)
        wired_to_elements = wiring.flatten(port_name)
        for (n,w) in wired_to_elements.items():
            if n not in port_elements:
                self.hwex.report_error("Element '%s' not part of input port '%s' on instance '%s'"%(n, port_name, instance.get_instance_name()))
                pass
            else:
                if w not in self.signals: self.signals[w] = WireMapping(w)
                self.signals[w].add_sink(instance,n,port_elements[n])
                pass
            pass
        pass
    #f add_wiring_source_driver
    def add_wiring_source_driver(self, instance:Instantiable, wire:Wire) -> None:
        """
        Invoked by TimedAssign
        """
        if wire not in self.signals: self.signals[wire] = WireMapping(wire)
        self.signals[wire].set_is_global_wire()
        pass

    #f add_wiring_source_driver
    def add_wiring_source(self, instance:Instantiable, port_name:str, ports:WireHierarchy, wiring:WiringHierarchy) -> None:
        if True:
            print("Port %s"%port_name)
            print("Output ports:%s"%str(ports.get_element(port_name)))
            print("Wiring: '%s'"%str(wiring))
            pass
        port_hierarchy : Optional[WireHierarchy] = ports.get_element(port_name)
        if port_hierarchy is None:
            self.hwex.report_error("Could not find output port '%s' on instance '%s'"%(port_name, instance.get_instance_name()))
            return
        port_elements = port_hierarchy.flatten_element(name=port_name)
        wired_to_elements = wiring.flatten(port_name)
        print(str(port_elements))
        print(wired_to_elements)
        for (n,w) in wired_to_elements.items():
            if n not in port_elements:
                self.hwex.report_error("Element '%s' not part of output port '%s' on instance '%s'"%(n, port_name, instance.get_instance_name()))
                pass
            else:
                if w not in self.signals: self.signals[w] = WireMapping(w)
                self.signals[w].add_source(instance,n,port_elements[n])
                pass
            pass
        pass
    #f check
    def check(self) -> None:
        pass
    #f connect_wires
    def connect_wires(self) -> None:
        print("Connect wires")
        for (c,cm) in self.clocks.items():
            print(c)
            cm.instantiate(self.hwex, self.hw)
            pass
        for (s,sm) in self.signals.items():
            print(s)
            sm.instantiate(self.hwex, self.hw)
            pass
        print("Done")

