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
from .waves     import Waves
from .exceptions import *

from typing import Tuple, Any, Union, Dict, List, Callable, Type, Optional, Sequence, Set, cast, ClassVar
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .wires import Wire
    pass
else:
    Wire=Type

#a Bit vector class
#c Value
class Value(object):
    pass

#c bv - sized int
class bv(Value):
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
class bvbundle(Value):
    """
    A bundle of bit vectors (or of more bvbundles)
    """
    _dict : Dict[str,str]
    def __init__(self, indict:Optional[Dict[str,Union[Wire]]]=None, **kw:Any) -> None:
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

