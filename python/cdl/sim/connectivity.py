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
from .base import BaseExecFile, Prefix
from .exceptions import *
from .instantiable import Instantiable
from .types import WireType, WireTypeElement
from .wires import Wire, Clock, WiringHierarchy
from .modules import Module

from typing import Tuple, Any, Union, Dict, List, Callable, Type, Optional, Sequence, Set, cast, ClassVar
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .hardware import Hardware, HardwareDescription
    pass

#a Connectivity
#t Driver

ClockPort  = Tuple[Instantiable, str]
#c Connection
class Connection(object):
    def __init__(self, instance:Instantiable, port_element_name:str, full_name:str, port_wire:Wire, elt_prefix:Prefix, elt_type:WireTypeElement):
        self.instance=instance
        self.port_element_name = port_element_name
        self.full_name = full_name
        self.port_wire = port_wire
        self.elt_prefix = elt_prefix
        self.elt_type = elt_type
        pass
    def str_source(self) -> str:
        return "%s.%s"%(self.instance.get_instance_name(),self.port_element_name)
    pass

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

    #f set_is_global_wire
    def set_is_global_wire(self, hwex:'HardwareDescription') -> None:
        if self.driven_by is not None:
            hwex.report_error("Multiply driven signal '%s'- trying to make it a global wire as well as driven by an output pin"%(self.wire.get_or_create_name()))
            return
        if self.is_global_wire:
            hwex.report_error("Multiply driven signal '%s'- trying to make it a global wire *twice*"%(self.wire.get_or_create_name()))
            return
        self.is_global_wire = True
        pass

    #f add_source
    def add_source(self, hwex:'HardwareDescription', connection:Connection) -> None:
        if self.driven_by is not None:
            hwex.report_error("Multiply driven signal - trying to drive it from '%s' and '%s'"%(self.driven_by.str_source(), connection.str_source()))
            return
        if self.is_global_wire:
            hwex.report_error("Multiply driven signal - trying to drive it from '%s' when it is already a global signal '%s'"%(connection.str_source(), self.wire.get_or_create_name()))
            return
        self.driven_by = connection
        pass

    #f add_sink
    def add_sink(self, hwex:'HardwareDescription', connection:Connection) -> None:
        self.drives.append(connection)
        pass

    #f instantiate
    def instantiate(self, hwex:'HardwareDescription') -> None:
        if self.driven_by is not None:
            driver_name   = self.wire.get_or_create_name(self.driven_by.port_element_name)
            pass
        else:
            driver_name = self.wire.get_or_create_name()
            pass

        if (self.driven_by is None) and (not self.is_global_wire):
            hwex.report_error("Undriven signal '%s'"%(self.wire.get_or_create_name()))
            return

        if self.driven_by is not None:
            connection    = self.driven_by
            instance_name = connection.instance.get_instance_name()
            port_name     = connection.port_element_name
            size          = self.wire.get_size()
            driver_sized = "%s[%d]"%(driver_name, size)
            if size==1: driver_sized = driver_name
            # print("create wire %s"%(driver_sized))
            # print("driven by %s.%s"%(instance_name, port_name))
            hwex.cdlsim_instantiation.wire(driver_sized)
            hwex.cdlsim_instantiation.drive(driver_name, "%s.%s"%(instance_name, port_name))
            pass

        for connection in self.drives:
            instance_name = connection.instance.get_instance_name()
            port_name     = connection.port_element_name
            # print("drives %s.%s"%(instance_name, port_name))
            hwex.cdlsim_instantiation.drive("%s.%s"%(instance_name, port_name), driver_name)
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
    clocks : Dict[Clock,ClockMapping]
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

    #f map_port
    def map_port(self, instance:Instantiable, port_name:str, ports:WireType, wiring:WiringHierarchy, reason:str, mapping_fn:Callable[[WireMapping,'HardwareDescription',Connection],None]) -> None:

        if False:
            print("Port %s"%port_name)
            print("Input ports:%s"%str(ports.get_element(port_name)))
            print("Wiring: '%s'"%str(wiring))
            pass
        port_hierarchy : Optional[WireType] = ports.get_element(port_name)
        if port_hierarchy is None:
            self.hwex.report_error("Could not find input port '%s' on instance '%s'"%(port_name, instance.get_instance_name()))
            return
        port_elements     = dict(port_hierarchy.flatten_element(name=port_name))
        for (full_name, wire, prefix, endpoint_type) in wiring.iter_fully(port_name):
            if full_name not in port_elements:
                self.hwex.report_error("Element '%s' not part of input port '%s' on instance '%s'"%(full_name, port_name, instance.get_instance_name()))
                pass
            else:
                if wire not in self.signals: self.signals[wire] = WireMapping(wire)
                connection = Connection(instance, port_name, full_name, wire, prefix, endpoint_type)
                mapping_fn(self.signals[wire], self.hwex, connection)
                pass
            pass
        pass

    #f add_wiring_source_driver
    def add_wiring_source_driver(self, instance:Instantiable, wire:Wire) -> None:
        """
        Invoked by TimedAssign
        """
        if wire not in self.signals: self.signals[wire] = WireMapping(wire)
        self.signals[wire].set_is_global_wire(self.hwex)
        pass

    #f add_wiring_sink
    def add_wiring_sink(self, instance:Instantiable, port_name:str, ports:WireType, wiring:WiringHierarchy) -> None:
        self.map_port(instance, port_name, ports, wiring, "input port", WireMapping.add_sink)
    #f add_wiring_source_driver
    def add_wiring_source(self, instance:Instantiable, port_name:str, ports:WireType, wiring:WiringHierarchy) -> None:
        self.map_port(instance, port_name, ports, wiring, "output port", WireMapping.add_source)
    #f check
    def check(self) -> None:
        pass
    #f connect_wires
    def connect_wires(self) -> None:
        # print("Connect wires")
        for (c,cm) in self.clocks.items():
            # print(c)
            cm.instantiate(self.hwex, self.hw)
            pass
        for (s,sm) in self.signals.items():
            # print(s)
            sm.instantiate(self.hwex)
            pass
        #print("Done")
        pass
    pass

