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

import sys, os
from typing import Tuple, Any, Union, Dict, List, Callable, Type, Optional, Sequence, Set, cast, ClassVar
from typing_extensions import Protocol

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

