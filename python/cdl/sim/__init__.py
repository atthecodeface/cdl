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
from .c_python_telnetd import c_python_telnet_server

from typing import Tuple, Any, Union, Dict, List, Callable, Type, Optional, Sequence, Set, cast, ClassVar
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

if "CDL_BUILD_DIR" in os.environ:
    oldpath = sys.path
    sys.path = [os.environ["CDL_BUILD_DIR"]]
    try:
        import py_engine
    except ImportError:
        raise
    finally:
        sys.path = oldpath
else:
    import py_engine
    pass

#a For exec_file
#c PyExecFile
class PyExecFile(object): # from sl_exec_file.cpp
    ThreadCallable = Callable[...,Any]
    def pyspawn(self,fn:ThreadCallable, args:object) -> None: ...
    def pypass(self,code:int, reason:str) -> None: ...
    def pyfail(self,code:int, reason:str) -> None: ...
    def list(self,what:str) -> None: ...  # what is libs, fns, cmds, objs, a library name, or an object name
    def pypassed(self) -> int: ...
    pass

#c SysEvent
class SysEvent(object): # from sl_ef_lib_event
    class SlEvent:
        def reset(self) -> None : ... # Reset the event
        def fire(self) -> None  : ... # fire the event
        def wait(self) -> None  : ... # if not fired, set thread to wait on the event firing
        def fired(self) -> int  : ... # return true if the event has fired since last reset
        pass
    def event(self, object_name:str) -> None : ... # Create a new 'SlEvent' attribute of this name
    pass

#c SysMemory
class SysMemory(object): # from sl_ef_lib_memory
    class SlMemory:
        def read(self, address:int) -> int : ... # Read the memory
        def write(self, address:int, data:int) -> None  : ... # Write the memory
        def load(self, filename:str, bit_offset:int) -> None  : ... # load from MIF
        def save(self, filename:str, start:int, num_words:int) -> None  : ... # save to MIF
        def compare(self, filename:str, offset:int) -> int  : ... # Compare file with memory contents
        pass
    def memory(self, object_name:str, num_words:int, word_size:int) -> None : ... # Create a new 'SlMemory' attribute of this name
    pass

#c SysRandom
class SysRandom(object): # from sl_ef_lib_random
    class SlRandom:
        def next(self) -> int : ... # Get next random number
        def seed(self, seed:str) -> None  : ... # Seed with a string
        pass
    def random_nial(self, object_name:str, iterations:int, base:int, range:int) -> None : ... # Create a new 'SlRandom' attribute of this name
    def random_cyclic(self, object_name:str, value:int, base:int, range:int, step:int) -> None : ... # Create a new 'SlRandom' attribute of this name

#c SysFifo
class SysFifo(object): # from sl_ef_lib_fifo
    class SlFifo:
        def reset(self) -> None : ...                 # reset the pointers and flags to empty
        def flags(self) -> int : ...                  # return e, f, ewm, fwm flags as 4 bits 0 thru 3
        def is_empty(self) -> int : ...               #
        def is_full(self) -> int : ...                #
        def is_nearly_full(self) -> int : ...         #
        def is_nearly_empty(self) -> int : ...        #
        def has_underflowed(self) -> int : ...        #
        def has_overflowed(self) -> int : ...         #
        def read_ptr(self) -> int : ...               # return read ptr for the FIFO
        def write_ptr(self) -> int : ...              # return write ptr for the FIFO
        def uncommitted_read_ptr(self) -> int : ...   # return uncommitted_read ptr for the FIFO
        def remove(self) -> int : ...                 # remove an element from the FIFO, error if underflow
        def peek(self) -> int : ...                   # look at the top element from the FIFO but do not change pointers, error if underflow
        def remove_no_commit(self) -> int : ...       # remove an element from the FIFO without committing the read ptr, error if underflow
        def add(self, item:int) -> None : ...         # add an element to the FIFO, error if overflow
        def commit_read(self) -> None : ...           # commit the uncommited read ptr of the FIFO after uncommitted reads
        def revert_read(self) -> None : ...           # revert the uncommited read ptr of the FIFO back to the last committed value
        def wait_for_flags(self, mask:int, value:int) -> None : ... # wait for FIFO flags AND mask to equal value
        pass
    def fifo(self, object_name:str, size:int, ne_wm:int, nf_wm:int) -> None : ... # Create a new 'SlFifo' attribute of this name


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
class PyEngSimCDLSimReg(object): # from c_se_engine__registration enhancements
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
class PyEngSimCDLSimWave(object): # from c_se_engine__waveform enhancements
    class Waves:
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
    def vcd_file(self, object_name:str) -> None : ... # Create a new 'Waves' attribute of this name
    pass
class PyEngSimCDLSimSim(object): # from c_se_engine__simulation enhancements
    def global_monitor_event(self, global_signal:str, event_name:str) -> None : ... # Tie global signal to an event
    def bfm_wait(self, cycles:int) -> None : ... # Wait for cycles bfm clock ticks
    def bfm_cycle(self)    -> int : ... # Get current BFM clock cycle
    def global_cycle(self) -> int : ... # Get current global simulation cycle
    def global_signal(self, global_signal:str) -> int : ... # Get value of global signal
    def global_signal_value(self, global_signal:str) -> str : ... # Get string value of global signal
    pass

class PyEngSim(object): # inside py_engine, type of an instantiated thing
    class Signal(object):
        def value(self) -> int: ... # Get value of (input) signal
        def drive(self, value:int) -> None: ... # Drive value after posedge of clock completes
        def reset(self, value:int) -> None: ... # Drive value now (DEPRECATED)
        def wait_for_value(self, value:int, timeout:int) -> None: ... # Wait up to timeout bfm ticks for signal to be at value
        def wait_for_change(self, timeout:int) -> None: ... # Wait up to timeout bfm ticks for signal to change from current value
    cdlsim_sim  : PyEngSimCDLSimSim
    cdlsim_reg  : PyEngSimCDLSimReg
    cdlsim_wave : PyEngSimCDLSimWave
    py          : PyExecFile
    sys_event   : SysEvent
    sys_fifo    : SysFifo
    sys_memory  : SysMemory
    sys_random  : SysRandom
    _temporary_object : Any
    pass
class PyEngine(object): # An engine object within the engine library - in se_py_engine.cpp
    def setenv(self, keyword:str, value:str) -> None : ... # Set an environment variable
    def read_hw_file(self, filename:str) -> None : ... # Read hardware from file
    def describe_hw(self, describer:str) -> None : ... # Describe the hardware - instead of using an hwex file
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
    def set_array_state(self, module:str, id:int, value:int, mask:Optional[int]=None, index:Optional[int]=None, state:Optional[str]=None) -> None : ... #
    """Set state in simulation engine.
      @module:     module name
      @state:      state name or enumerated id
      @value:      value(s) to set
      @mask:       mask(s) for value(s) (or None)
      @what:       what part of state to set (if memory/vector)

      Set state contents of simulation engine.  The 'mask' bits
      indicate which bits of the state value to set.  If 'mask' is
      None then all bits in the state is set.

      When 'state' indicates a memory 'value' and 'mask' can be
      lists of values.  If 'mask' is a single value then it is
      applied to all entries in the 'value' list.

      The 'what' parameter can be used to indicate which parts of
      the memory state to modify.  A single int indicates a memory
      word with a specific index.  A slice object indicates multiple
      memory entries.

      Throw ValueError if 'module' or 'state' can not be found.},
    """
    #{"checkpoint_init",           (PyCFunction)py_engine_method_checkpoint_init,         METH_VARARGS|METH_KEYWORDS, "Initialize checkpointing"},
    #{"checkpoint_add",            (PyCFunction)py_engine_method_checkpoint_add,          METH_VARARGS|METH_KEYWORDS,  "Add a checkpoint"},
    #{"checkpoint_info",           (PyCFunction)py_engine_method_checkpoint_info,         METH_VARARGS|METH_KEYWORDS, "Get information about a checkpoint"},
    #{"checkpoint_restore",        (PyCFunction)py_engine_method_checkpoint_restore,      METH_VARARGS|METH_KEYWORDS, "Restore a checkpoint"},
    pass

class PyEngineLibrary(object): # The engine library - in se_py_engine.cpp
    @staticmethod
    def new() -> PyEngine : ...
    @staticmethod
    def debug(level:int) -> None : ...
    class exec_file(object):
        pass
    pass
# class py_engine(PyEngineLibrary): ...

#c _nameable - a class with a _name, given to it by a _namegiver
class _nameable(object):
    """
    An object that should get named when assigned to a namegiver object.
    """
    _name : str # Once given...
    def __repr__(self)->str: return self._name
    pass

#c _nameable - a class that gives names to _nameables/List[_nameable]/Dict[str,_nameable]
class _namegiver(object):
    """
    An object that gives nameable objects a name.
    """
    def _give_name(self, name:str, value:Union[Nameable,List[Nameable],Dict[str,Nameable]]) -> None:
        if isinstance(value, _nameable) and (not hasattr(value, "_name") or value._name is None):
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

#a Exceptions
class PyCDLError(Exception):
    """
    Base class for all errors.
    """
    pass

class WireError(PyCDLError):
    """
    Thrown on a wiring mismatch.
    """
    def __init__(self, msg:str="Wiring error!"):
        self._msg = msg
        pass

    def __str__(self)->str:
        return "WireError: " + self._msg
    pass

#a Bit vector class
#c bv
class bv(object):
    """
    A bit-vector. Has a size and a value.
    """
    Val = Union[int, 'bv']
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

    def value(self) -> Val:
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

#c wire - nameable that is driven_by something and drives something
class wire(_nameable):
    """
    The object that represents a wire.
    """
    # _cdl_signal : PyEngSim.Global # Global wire created in hardware when the hardware is built - passed in at _connect_cdl_signal
    _instantiated_name : str # Given to the wire in the hardware when the hardware is built
    def __init__(self, size:int=1, name:str=None):
        self._drives = []
        self._driven_by = None
        self._size = size
        self._cdl_signal = None
        self._name = name
        self._reset_value = None

    def _name_list(self, inname:str) -> List[str]:
        return ["%s[%d]" % (inname, self._size)]

    def _check_connectivity(self, other:'wire') -> None:
        if self._size and other._size and self._size != other._size:
            raise WireError("Size mismatch: %s has %d, %s has %d" % (repr(self), self._size, repr(other), other._size))
        pass

    def _is_driven_by(self, other:'wire') -> None:
        if self._driven_by:
            raise WireError("Double-driven signal at %s" % repr(self))
        self._check_connectivity(other)
        self._driven_by = other
        other._drives.append(self)
        pass

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

    def _connectivity_upwards(self, index:int) -> None:
        if self._driven_by:
            print("%sDriven by %s" % (" "*index, repr(self._driven_by)))
            return self._driven_by._connectivity_upwards(index+2)
        else:
            print("%sROOT AT %s" % (" "*index, repr(self)))
            return self

    def _connectivity_downwards(self, index:int)->None:
        print("%sAt %s, CDL signal %s" % (" "*index, repr(self), repr(self._cdl_signal)))
        for i in self._drives:
            print("%sDrives %s" % (" "*index, repr(i)))
            i._connectivity_downwards(index+2)
            pass
        pass

    def print_connectivity(self) -> None:
        print("Finding connectivity tree for %s:" % repr(self))
        root = self._connectivity_upwards(0)
        print()
        root._connectivity_downwards(0)
        pass

    def size(self) -> int:
        return self._size

    def value(self) -> bv:
        if self._cdl_signal:
            return bv(self._cdl_signal.value(), self._size)
        else:
            raise WireError("No underlying value for signal %s" % repr(self))

    def drive(self, value:Union[bv,int]) -> None:
        if isinstance(value, bv):
            value = int(value)
        if self._cdl_signal:
            self._cdl_signal.drive(value)
        else:
            raise WireError("No underlying signal to drive for %s" % repr(self))

    def _reset(self, value:int) -> None:
        if self._cdl_signal:
            self._cdl_signal.reset(value)
        else:
            raise WireError("No underlying signal to drive for %s" % repr(self))

    def reset(self, value:int) -> None:
        if self._cdl_signal:
            self._cdl_signal.reset(value)
        self._reset_value = value
        pass

    def wait_for_value(self, val:int, timeout:int=-1) -> None:
        if self._cdl_signal:
            self._cdl_signal.wait_for_value(val, timeout)
        else:
            raise WireError("No underlying value for signal %s" % repr(self))

    def wait_for_change(self, timeout:int=-1) -> None:
        if self._cdl_signal:
            self._cdl_signal.wait_for_change(timeout)
        else:
            raise WireError("No underlying value for signal %s" % repr(self))
        pass
    pass

#c clock - special type of wire that corresponds to a CDL simulation clock
class clock(wire):
    def __init__(self, init_delay:int=0, cycles_high:int=1, cycles_low:int=1, name:str=None):
        self._init_delay = init_delay
        self._cycles_high = cycles_high
        self._cycles_low = cycles_low
        wire.__init__(self, 1, name)
        pass
    pass

#c wirebundle - nameable that represents a bundle of wires through a dictionary
class wirebundle(_nameable):
    """
    The object that represents a bundle of wires.
    """
    _dict: Dict[str,Union[wire, 'wirebundle']]
    def __init__(self, bundletype=None, name=None, **kw):
        if bundletype:
            # Build the bundle from a dict.
            self._dict = {}
            for i in bundletype:
                if isinstance(bundletype[i], int):
                    self._dict[i] = wire(bundletype[i], name=i)
                else:
                    self._dict[i] = wirebundle(bundletype=bundletype[i], name=i)
        else:
            self._dict = kw
        self._drives = []
        self._driven_by = None
        self._reset_value = None
        self._name = name

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
            del unusedkeys[i]
            self._dict[i].check_connectivity(other._dict[i])
            pass
        if len(unusedkeys) > 0:
            raise WireError("Wire bundle mismatch in %s, leftover signals" % repr(self))
        pass

    def _populate_dict(self, other:'wirebundle') -> None:
        # Yay! Now we know what signals we have! If we hooked up signals
        # anonymously, we now need to put together our bundle and check it.
        for i in other._dict:
            if isinstance(other._dict[i], wirebundle):
                self._dict[i] = wirebundle()
                self._dict[i]._populate_dict(other._dict[i])
            elif isinstance(other._dict[i], wire):
                self._dict[i] = wire(other._dict[i].size())
            else:
                raise WireError("Unknown wire type %s" % repr(other.__class__))
        # If we've already hooked this thing up, we need to propagate our
        # knowledge of what's in there.
        if self._driven_by:
            self._update_connectivity(self._driven_by)
            pass
        for i in self._drives:
            i._update_connectivity(self)
            pass
        pass

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

    def _is_driven_by(self, other:'wirebundle') -> None:
        if self._driven_by:
            raise WireError("Double-driven signal at %s" % repr(self))
        self._update_connectivity(other)
        for i in self._dict:
            self._dict[i]._is_driven_by(other._dict[i])
        self._driven_by = other
        other._drives.append(self)
        pass

    def _add_wire(self, wirename:str, size:int, name:str) -> None:
        # First see if we need to recurse.
        wirelist = wirename.split("__", 1)
        if len(wirelist) > 1:
            # We need to go down to another level of bundles.
            if wirelist[0] not in self._dict:
                self._dict[wirelist[0]] = wirebundle()
            return self._dict[wirelist[0]]._add_wire(wirelist[1], size, name)
        else:
            if wirelist[0] in self._dict:
                raise WireError("Double add of wire %s to bundle" % wirelist[0])
            self._dict[wirelist[0]] = wire(size, name)
            return self._dict[wirelist[0]]
        pass

    def value(self) -> bvbundle:
        # We want the value. Fair enough. Go dig and get it.
        outdict = {}
        for i in self._dict:
            outdict[i] = self._dict[i].value()
        return bvbundle(outdict)

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
                else:
                    retdict[io[0]] = wire(io[1], io[0])
                    thewire = retdict[io[0]]
                #print len(io),io
                #print "'%s'"%io[0], cdl_object
                #print "Creating port wire: %s size %d, result %s" % (io[0], io[1], repr(thewire))
                if cdl_object and hasattr(cdl_object, io[0]) and self._auto_wire_same_name:
                    #print "Connecting CDL signal %s" % repr(getattr(cdl_object, io[0]))
                    thewire._connect_cdl_signal(getattr(cdl_object,io[0]))
                    pass
                else:
                    #print "No CDL signal!"
                    pass

            retlist.append(retdict)
        return retlist

#c th
class th(_instantiable):
    """
    The object that represents a test harness.
    """
    _thfile : PyEngSim # Set when hw is instantiated
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

    def __init__(self, clocks:ClockDict, inputs:InputDict, outputs:OutputDict):
        self._clocks = self._flatten_names(clocks)
        self._inputs = self._flatten_names(inputs)
        self._outputs = self._flatten_names(outputs)
        self._eventanonid = 1

    def sim_message(self) -> PyEngSimCDLSimReg.SlMessage:
        self._thfile.cdlsim_reg.sim_message( "_temporary_object" )
        x = cast(PyEngSimCDLSimReg.SlMessage,self._thfile._temporary_object)
        del self._thfile._temporary_object
        return x

    def sim_memory(self, num_words:int, width:int) -> SysMemory.SlMemory:
        self._thfile.sys_memory.memory( "_temporary_object", num_words, width )
        x = cast(SysMemory.SlMemory,self._thfile._temporary_object)
        del self._thfile._temporary_object
        return x

    def bfm_wait(self, cycles:int) -> None:
        self._thfile.cdlsim_sim.bfm_wait(cycles)
        pass

    def spawn(self, boundfn:PyExecFile.ThreadCallable, *args:Any) -> None:
        self._thfile.py.pyspawn(boundfn, args)
        pass

    def global_cycle(self) -> int:
        return self._thfile.cdlsim_sim.global_cycle()

    def passtest(self, code:int, message:str) -> None:
        return self._thfile.py.pypass(code, message)

    def failtest(self, code:int, message:str) -> None:
        return self._thfile.py.pyfail(code, message)

    def passed(self) -> int:
        return self._thfile.py.pypassed()

    class _event(object):
        """
        The object that controls events, inside a test harness.
        """
        def __init__(self, th):
            th._thfile.sys_event.event("__anonevent%3d" % th._eventanonid)
            self._cdl_obj = getattr(th._thfile, "__anonevent%3d" % th._eventanonid)
            self._th = th
            th._eventanonid += 1
            pass

        def reset(self)->None:
            self._cdl_obj.reset()
            pass

        def fire(self)->None:
            self._cdl_obj.fire()
            pass

        def wait(self)->None:
            self._cdl_obj.wait()
            pass
        pass

    def event(self) -> SysEvent.SlEvent:
        return th._event(self)
    pass


#c _internal_th
class _internal_th(th):
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
        th.__init__(self, clocks={}, inputs={}, outputs={})
        pass
    def run(self)->None:
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

#c _thfile
class _thfile(py_engine.exec_file):
    def __init__(self, th:th):
        self._th = th
        py_engine.exec_file.__init__(self)
        pass

    def create_waves(self) -> PyEngSimCDLSimWave.Waves:
        self.cdlsim_wave.vcd_file("_waves")
        x = self._waves
        del(self._waves)
        return x

    def exec_init(self) -> None:
        pass
    def exec_reset(self) -> None:
        pass
    def exec_run(self) -> None:
        try:
            self._th.run()
        except:
            self._th.failtest(0, "Exception raised in run method!"+traceback.format_exc())
            raise

#c _hwexfile
class _hwexfile(py_engine.exec_file):
    _hw : 'hw'
    def __init__(self, hw:'hw'):
        self._hw = hw
        self._running = False
        self._instantiated_wires = set()
        self._instantiation_anonid = 0
        py_engine.exec_file.__init__(self)
        pass

    def _connect_wire(self, name:str, wireinst:wire, connectedwires:Set[wire], inputs:int, ports:Dict[str,wire], assign:int, firstval:int, wait:int, afterval:int):
        wire_basename = name.split('.')[-1].split('__')[-1]
        if wire_basename not in ports:
            raise WireError("Connecting to undefined port '%s' (from name '%s')" % (wire_basename,name))
        port = ports[wire_basename]
        if not hasattr(port, "_size"):
            raise WireError("Port does not have a _size attribute, please check port %s, connection to wire %s." % (wire_basename, wireinst._name))
        elif wireinst._size != port._size:
            raise WireError("Port size mismatch for port %s, wire is size %d got a port size of %d" % (wire_basename, wireinst._size, port._size))
                # size mismatch!
        if wireinst not in connectedwires:
            wireinst._instantiated_name = wireinst._name
            if wireinst._instantiated_name in self._instantiated_wires:
                wireinst._instantiated_name += "_INST%03d" % self._instantiation_anonid
                self._instantiation_anonid += 1
            self._instantiated_wires.add(wireinst._instantiated_name)
            if isinstance(wireinst, clock):
                self.cdlsim_instantiation.clock(wireinst._name, wireinst._init_delay, wireinst._cycles_high, wireinst._cycles_low)
                #print "CLOCK %s" % wireinst._name
            else:
                self.cdlsim_instantiation.wire("%s[%d]" % (wireinst._instantiated_name, wireinst._size))
                #print "WIRE %s" % wireinst._instantiated_name
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
        for i in wiredict:
            if isinstance(wiredict[i], wire):
                self._connect_wire(name+i, wiredict[i], connectedwires, inputs, ports, assign, firstval, wait, afterval)
            elif isinstance(wiredict[i], wirebundle):
                if i not in ports or not isinstance(ports[i], wirebundle):
                    raise WireError("Connecting wire bundle %s to unknown port!" % i)
                self._connect_wires(name+i+"__", wiredict[i]._dict, connectedwires, inputs, ports[i]._dict, assign, firstval, wait, afterval)
            else:
                raise WireError("Connecting unknown wire type %s" % repr(wiredict[i].__class__))

    def _set_up_reset_values(self)->None:
        # And set up the reset values.
        if not hasattr(self, "_connectedwires"):
            return
        for i in self._connectedwires:
            if i._reset_value:
                i._reset(i._reset_value)


    def exec_init(self)->None:
        pass
    def exec_reset(self)->None:
        self._set_up_reset_values()
    def exec_run(self)->None:
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
            elif isinstance(i, th):
                i._thfile = _thfile(i)
                self.cdlsim_instantiation.option_string("clock", " ".join(list(i._clocks.keys())))
                self.cdlsim_instantiation.option_string("inputs", " ".join([" ".join(i._inputs[x]._name_list(x)) for x in i._inputs]))
                #print "INPUTS %s" % " ".join([" ".join(i._inputs[x]._name_list(x)) for x in i._inputs])
                self.cdlsim_instantiation.option_string("outputs", " ".join([" ".join(i._outputs[x]._name_list(x)) for x in i._outputs]))
                #print "OUTPUTS %s" % " ".join([" ".join(i._outputs[x]._name_list(x)) for x in i._outputs])
                self.cdlsim_instantiation.option_object("object", i._thfile)
                #print "MODULE se_test_harness %s" % i._name
                self.cdlsim_instantiation.module("se_test_harness", i._name)
                i._ports = i._ports_from_ios(self._hw._engine.get_module_ios(i._name), i._thfile)
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
        if hasattr(self._hw, "_wavesinst"):
            self._hw._wavesinst._connect_waves()

        # Say we're in business.
        self._running = True


#c Waves
class Waves(object):
    waves : PyEngSimCDLSimWave.Waves
    """
    The object that controls waves, inside a hardware object. It's
    singletonized per hardware object
    """
    def __init__(self, waves:PyEngSimCDLSimWave.Waves) -> None:
        self._waves = waves
        self._waves_enabled = 0
        pass

    def reset(self)->None:
        self._waves.reset()
        pass

    def open(self, filename:str) -> None:
        self._waves.open(filename)
        pass

    def close(self)->None:
        self._waves.close()
        pass

    def enable(self)->None:
        if not self._waves_enabled:
            self._waves_enabled = 1
            self._waves.enable()
        else:
            self._waves.restart()

    def disable(self)->None:
        self._waves.pause()
        pass

    def file_size(self)->int:
        return self._waves.file_size()

    def _add(self, hierlist:List[Any]):
        for x in hierlist:
            if isinstance(x, list):
                self._add(x)
                pass
            elif isinstance(x, dict):
                self._add([x[i] for i in list(x.keys())])
                pass
            else:
                self._waves.add(x._name)
                pass
            pass
        pass

    def add(self, *hier:Any) -> None:
        assert hasattr(self, "_waves")
        self._add(hier)
        pass

    def _add_hierarchy(self, hierlist:List[Any]) -> None:
        for x in hierlist:
            if isinstance(x, list):
                self._add_hierarchy(x)
                pass
            elif isinstance(x, dict):
                self._add_hierarchy([x[i] for i in list(x.keys())])
                pass
            else:
                self._waves.add_hierarchy(x._name)
                pass
            pass
        pass
    def add_hierarchy(self, *hier:Any) -> None:
        assert hasattr(self, "_waves")
        self._add_hierarchy(hier)
        pass
    pass

#c hw
class hw(_clockable):
    """
    The object that represents a piece of hardware.
    """
    _engine : ClassVar[PyEngine] # Created when the object is instantiated
    _waves  : ClassVar[PyEngSimCDLSimWave.Waves]
    @classmethod
    def prepare_for_waves(cls, hw) -> _wave_hook:
        assert not hasattr(cls, "_waves")
        hw._wave_hook = _wave_hook()
        return hw._wave_hook

    @classmethod
    def create_waves(cls, hw) -> None:
        if hasattr(cls, "_waves"): return
        cls._waves = hw._wave_hook._thfile.create_waves()
        return

    hw_class_data = {"engine":None,"id":0}
    _wavesinst     : Waves
    def __init__(self, thread_mapping=None, children=None, *children_list):
        # Hack arguments
        if (children is None) or (type(children)!=list):
            if children is not None:
                children = [thread_mapping, children]
                thread_mapping = None
            elif thread_mapping is not None:
                children.append(thread_mapping)
                thread_mapping = None
            children.extend(children_list)

        if self.hw_class_data["engine"]==None:
            self.hw_class_data["engine"] = py_engine.py_engine()
        self.hw_class_data["id"] = self.hw_class_data["id"]+1
        self._id = self.hw_class_data["id"]

        children_unpacked = []
        for child in children:
            if (isinstance(child,list)):
                children_unpacked.extend(child)
            else:
                children_unpacked.append(child)
        children_unpacked = tuple(children_unpacked)
        if not hasattr(self, "_waves"):
            children_unpacked += (self.prepare_for_waves(self),)
            pass
        _clockable.__init__(self, children_unpacked)
        self._engine = self.hw_class_data["engine"]

        if thread_mapping is not None:
            self._engine.thread_pool_init()
            for x in list(thread_mapping.keys()):
                self._engine.thread_pool_add(x)
            for x in list(thread_mapping.keys()):
                for module_name in thread_mapping[x]:
                    r = self._engine.thread_pool_map_module(x,module_name)
                    print("Map returned",r)

        self.display_all_errors()
        self._hwex = _hwexfile(self)
        self._engine.describe_hw(self._hwex)
        self.display_all_errors()
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
        self.create_waves(self)
        #if hw._hwex and hw._hwex._running:
        #    pass
        if not hasattr(self, "_wavesinst"):
            self._wavesinst = Waves(self._waves)
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

    def run_console( self, port:int=8745, locals:Dict[str,str]={} ) -> None:
        console_server = c_python_telnet_server( port=port, locals=locals )
        console_server.serve()
        pass
    pass

#c load_mif
def load_mif(filename:str, length:int=0, width:int=64, acknowledge_deprecated:bool=False) -> List[int]:
    """
    Open a file and read in hex values into an array. Provided mostly for
    compatibility with legacy CDL.
    """
    print("Deprecated load_mif called")
    if not acknowledge_deprecated: raise Exception("Deprecated load_mif called")
    fd = open(filename, "r")
    retarray = []
    for line in fd:
        if '#' in line or '//' in line:
            # If there's a comment, kill it off.
            line = line.split('#')[0]
            line = line.split('//')[0]
        if len(line) == 0:
            continue
        vals = line.split(" ")
        for val in vals:
            val = val.strip()
            if len(val) == 0:
                continue
            retarray.append(int(val, 16))
    # Finally, zero-pad the list.
    if len(retarray) < length:
        retarray.extend([0 for x in range(length-len(retarray))])
    fd.close()
    return retarray

#c save_mif
def save_mif(array:Sequence[int], filename:str, length:int=0, width:int=64, acknowledge_deprecated:bool=False) -> None:
    """
    Write hex values from an array into a file. Provided mostly for
    compatibility with legacy CDL.
    """
    print("Deprecated save_mif called")
    if not acknowledge_deprecated: raise Exception("Deprecated save_mif called")
    fd = open(filename, "w")
    wd4 : int = width // 4
    for val in array:
        print("%0*.*x" % (wd4, wd4, val), file=fd)
    # Finally, zero-pad the list.
    if len(array) < length:
        for i in range(length-len(array)):
            print("%0*.*x" % (wd4, wd4, 0), file=fd)
    fd.close()

