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

PySimulation - base class of any exec_file in a simulation module, such as a test harness
             - many test modules support a PyObject as an option, and they are all derived from this class

PyEngine - the class of a simulation engine exposed by the py_engine library

PyEngineLibrary - the clas of the py_engine library itself

"""
from typing import Tuple, Any, Union, Dict, List, Callable, Type, Optional, Sequence, Set, cast, ClassVar
from .base import BaseEngine
from .exec_file import ExecFile
from typing import TYPE_CHECKING

#a Waveforms
class VcdFile:
    if TYPE_CHECKING:
        def open(self, filename:str) -> int: ...
        def add(self, name:str, *names:Any) -> int: ...
        def add_hierarchy(self, name:str, *names:Any) -> int: ...
        def enable(self) -> None: ...
        def close(self) -> None: ...
        def reset(self) -> None: ...
        def pause(self) -> None: ...
        def restart(self) -> None: ...
        def file_size(self) -> int: ...
        pass

#a Simulation engine module exec file enhancements
#c PyEngSimCDLSimReg - from c_se_engine__registration enhancements
class PyEngSimCDLSimReg(object):
  if TYPE_CHECKING:
    class SlMessage:
        def send_int(self, module:str, reason:int, *data:Any) -> int : ... # send ints
        def send_value(self, module:str, reason:int, *data:Any) -> int : ... # send int64s
        def get_value(self, n:int) -> int: ... # gets n'th int in the message
        def get_string(self, n:int) -> str: ... # gets n'th string in the message
        def response(self, n:int) -> int: ...  # get response value from last message
        def text(self, n:int) -> str: ... # get message text
        pass
    def sim_message(self, object_name:str) -> None : ... # Create a new 'SlMessage' attribute of this name
    pass

#c PyEngSimCDLSimWave - from c_se_engine__waveform enhancements
class PyEngSimCDLSimWave(object):
    if TYPE_CHECKING:
        def vcd_file(self, object_name:str) -> VcdFile : ... # Create a new 'Waves' attribute of this name
        pass
    pass

#c PyEngSimCDLSimSim - from c_se_engine__simulation enhancements
class PyEngSimCDLSimSim(object):
  if TYPE_CHECKING:
    def global_monitor_event(self, global_signal:str, event_name:str) -> None : ... # Tie global signal to an event
    def bfm_wait(self, cycles:int) -> None : ... # Wait for cycles bfm clock ticks
    def bfm_cycle(self)    -> int : ... # Get current BFM clock cycle
    def global_cycle(self) -> int : ... # Get current global simulation cycle
    def global_signal(self, global_signal:str) -> int : ... # Get value of global signal
    def global_signal_value(self, global_signal:str) -> str : ... # Get string value of global signal
    pass

#c PyEngSimCDLSimInstantiation - from c_se_engine__instantiation enhancements
class PyEngSimCDLSimInstantiation(object):
    if TYPE_CHECKING:
        def module(self, module_type:str, instance_name:str ) -> None : ...
        def module_force_option_int(self, full_module_path:str, option:str, value:int ) -> None : ...
        def module_force_option_string(self, full_module_path:str, option:str, value:str) -> None : ...
        def module_force_option_object(self, full_module_path:str, option:str, value:object) -> None : ...
        def option_int(self, name:str, value:int) -> None : ...
        def option_string(self, name:str, value:str) -> None : ...
        def option_object(self, name:str, value:object) -> None : ...
        def wire(self, name:str, *args:Any ) -> None : ... # up to 15 names
        def assign(self, output_name:str, value:int, until:Optional[int], after_value:Optional[int]) -> None : ...
        def cmp(self, output_wire_name:str, value_bus_name:str, value:int) -> None : ...
        def mux(self, output_name:str, select_bus_name:str, *args:Any) -> None : ... # args is up to 8 signal names to select
        def decode(self, output_wire_name:str, input_bus_name:str, enable_name:Optional[str]) -> None : ...
        def extract(self, output_wire_name:str, *args:Any) -> None : ... #,        4, "extract", "ssii", "extract <output> <input> <start bit> <number bits>"},
        def bundle(self, output_wire_name:str, *args:Any) -> None : ... #,         2, "bundle", "sssssssssssssss", "extract <output> <inputs>*"},
        def logic(self, gate_type:str, output_wire_name:str, ) -> None : ... #,          3, "logic", "sssssssssssssss", "logic <type> <output> <inputs>* - up to 12"},
        def clock(self, clock_name:str, delay_to_high:int, clocks_high:int, clocks_low:int) -> None : ...
        def clock_divide(self, output_clock_name:str, source_clock_name:str, delay_to_high:int, clock_ticks_high:int, clock_ticks_low:int) -> None : ...
        def clock_phase(self, output_name:str, source_clock:str, delay_to_start:int, clock_ticks_pattern:int, pattern_string:str) -> None : ...
        def drive(self, driven:str, drive_with:str) -> None : ...
        pass
    pass

#a Simulation exec_file
#c PyBfmExecFile - from c_se_engine, and bfm_add_exec_file_enhancements
class PyBfmExecFile(ExecFile):
    """
    simulation_add_exec_file_enhancements( file_data, engine_handle, clock, posedge );
    waveform_add_exec_file_enhancements( file_data );
    coverage_add_exec_file_enhancements( file_data );
    log_add_exec_file_enhancements( file_data, engine_handle );
    register_add_exec_file_enhancements( file_data, engine_handle );
    checkpoint_add_exec_file_enhancements( file_data, engine_handle );
    """
    class Input(object):
        def value(self) -> int: ... # Get value of (input) signal
        pass
    class Output(object):
        def drive(self, value:int) -> None: ... # Drive value after posedge of clock completes
        def reset(self, value:int) -> None: ... # Drive value now (DEPRECATED)
        def wait_for_value(self, value:int, timeout:int) -> None: ... # Wait up to timeout bfm ticks for signal to be at value
        def wait_for_change(self, timeout:int) -> None: ... # Wait up to timeout bfm ticks for signal to change from current value
        pass
    if TYPE_CHECKING:
        cdlsim_sim  : PyEngSimCDLSimSim
        cdlsim_reg  : PyEngSimCDLSimReg
        cdlsim_wave : PyEngSimCDLSimWave
        pass
    _waves : VcdFile
    def create_waves(self) -> VcdFile:
        self.cdlsim_wave.vcd_file("_waves")
        x = self._waves
        del(self._waves)
        return x
    pass

#c SimulationExecFile
class SimulationExecFile(PyBfmExecFile):
    pass

#a PyEngine and PyEngineLibrary
#c HardwareExecFile - for hardware description
class HardwareExecFile(PyBfmExecFile): # from c_se_engine__instantiation enhancements
    """
    Note that waves must be created currently by this method
    """
    if TYPE_CHECKING:
        cdlsim_instantiation : PyEngSimCDLSimInstantiation
        pass
    pass

#c PyEngine -  An engine object within the engine library - in eh_c_py_engine.cpp (standard python, not exec file)
class PyEngine(BaseEngine):
    if TYPE_CHECKING:
        def setenv(self, keyword:str, value:str) -> None : ... # Set an environment variable
        def read_hw_file(self, filename:str) -> None : ... # Read hardware from file
        def describe_hw(self, describer:HardwareExecFile) -> None : ... # Describe the hardware - instead of using an hwex file
        def read_gui_file(self, filename:str) -> None : ... # Read a GUI file description (not used any more)
        def reset_errors(self) -> None : ... # Reset the errors
        def get_error_level(self) -> int : ... # Get the current highest error level
        def get_error(self, error:int) -> str : ... # Get the nth error
        def cycle(self) -> int : ... # Get current simulation cycle number (as seen in a module with global_cycle())
        def reset(self) -> None : ... # Reset the simulation
        def step(self, cycles:int) -> None : ... # Step for cycles

        def write_profile(self, filename:str) -> None : ... # Write out simulation profile
        def thread_pool_init(self) -> None : ... # Initialize the thread pool for multithreaded simulations
        def thread_pool_add(self, name:str) -> None : ... # Add a named thread to the pool
        def thread_pool_map_module(self, thread_name:str, module_name:str) -> None : ... # Assign a module to a thread
        def thread_pool_delete(self) -> None : ... # Delete the thread pool

        def list_instances(self) -> List[str] : ...
        def get_module_ios(self, module:str) -> List[List[Tuple[str,int]]] : ... # Get list of list of signal name/width for clocks, inputs and outputs
        def find_state(self, name:str) -> Optional[List[Any]] : ... # Get details on state - None, [int type, str], or [int type,str,int id,str]
        def get_state_info(self, module:str, id:int) -> Optional[Tuple[int,str,str,str,int,int]] : ... # Get type, module, prefix, state_name, size[0], size[1]
        def get_state(self, module:str, state:Union[str,int], what:Union[None,int,slice]=None) -> Union[int, List[int]] : ... # Get contents of state (either name or enumerated id)
        def get_state_value_string(self, module:str, id:int) -> Optional[str] : ... # Get string of value
        def get_state_memory(self, module:str, id:int, start:int, length:int) -> Optional[List[int]] : ...
        def set_state(self, module:str, state:object, value:object, mask:Optional[int]=None, what:Optional[object]=None) -> None : ... # Set state - args is mask, what
        def set_array_state(self, module:str, id:int, value:int, mask:Optional[int]=None, index:Optional[int]=None, state:Optional[str]=None) -> None : ...
        #{"checkpoint_init",           (PyCFunction)py_engine_method_checkpoint_init,         METH_VARARGS|METH_KEYWORDS, "Initialize checkpointing"},
        #{"checkpoint_add",            (PyCFunction)py_engine_method_checkpoint_add,          METH_VARARGS|METH_KEYWORDS,  "Add a checkpoint"},
        #{"checkpoint_info",           (PyCFunction)py_engine_method_checkpoint_info,         METH_VARARGS|METH_KEYWORDS, "Get information about a checkpoint"},
        #{"checkpoint_restore",        (PyCFunction)py_engine_method_checkpoint_restore,      METH_VARARGS|METH_KEYWORDS, "Restore a checkpoint"},
        pass
    pass

#c PyEngineLibrary class - py_engine module effectively has this class
#f Engine
class Engine(PyEngine): # so we can extend it
    _waves  : VcdFile
    def create_vcd_file(self, x:Any) -> None:
        if not hasattr(self, "_waves"):
            self._waves = x.create_waves()
            pass
        pass
    def vcd_file(self) -> VcdFile:
        assert hasattr(self, "_waves")
        return self._waves
    def __init__(self) -> None:
        PyEngine.__init__(self)
        pass

    pass

