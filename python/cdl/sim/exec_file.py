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
"""
from .base import BaseExecFile
from typing import Tuple, Any, Union, Dict, List, Callable, Type, Optional, Sequence, Set, cast, ClassVar
from typing_extensions import Protocol
from typing import TYPE_CHECKING

#a For exec_file
#c PyExecFile
ExecFileThreadFn = Callable[...,Any]
class PyExecFile(object): # from sl_exec_file.cpp
    def pyspawn(self,fn:ExecFileThreadFn, args:object) -> None: ...
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

#a Exec file extensions
#c ExecFile
class ExecFile(BaseExecFile):
    """
    An exec file is an object passed to sl_exec_file to be executed.

    The object passed is an instance of this class

    The object is then executed by sl_exec_file:

    * exec_init is invoked when the exec file thread for the object is spawned

    * exec_reset is invoked whenever the exec file thread is reset
      This occurs after exec_init, and it may occur many times depending on the entity running the exec file
      For an object in a simulation harness, for example, this occurs when the simulation is reset (cycles set to 0)

    * exec_run is invoked after at least one exec_reset, and is the main thread of execution
      If exec_run returns then the exec file thread for the object finishes

    In a simulation using python exec file objects it is only reasonable to expect:

    * exec_init ONCE
    * exec_reset a number of times
    * exec_run ONCE, returning

    If a simulation were to reset after invoking exec_run without the thread completing,
    it would probably break things.

    """
    if TYPE_CHECKING:
        py          : PyExecFile
        sys_event   : SysEvent
        sys_fifo    : SysFifo
        sys_memory  : SysMemory
        sys_random  : SysRandom
        pass
    _temporary_object : Any
    def __init__(self) -> None:
        """
        This method is invoked when the object is instanced - this is prior to it being spawned
        """
        # self._th = th
        BaseExecFile.__init__(self)
        pass
    def exec_init(self) -> None:
        """
        This method is invoked by sl_exec_file *ONCE* when the thread running this class is spawned
        """
        pass
    def exec_reset(self) -> None:
        """
        This method is invoked by sl_exec_file *whenever* the exec file is reset
        """
        pass
    def exec_run(self) -> None:
        """
        This method is the execution path for the exec file; in a simulation harness it might
        be that this method invokes appropriate wait operations.

        When this method returns the thread dies
        """
        raise Exception("exec_run should be subclassed in execution files")

