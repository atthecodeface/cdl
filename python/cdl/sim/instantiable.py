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

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .hardware     import HardwareDescription, Hardware
    from .connectivity import Connectivity
    pass

class Instantiable(object):
    #f instantiate
    def instantiate(self, hwex:'HardwareDescription', hw:'Hardware') -> None:
        pass
    #f add_connectivity
    def add_connectivity(self, hwex:'HardwareDescription', connectivity:'Connectivity') -> None:
        pass
    #f All done
    pass
