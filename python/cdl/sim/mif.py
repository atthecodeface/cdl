#a Copyright
#
#  This file 'mif.py' copyright Gavin J Stark 2011-2020
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
Old MIF file stuff -
"""

#a Imports
from typing import Tuple, Any, Union, Dict, List, Callable, Type, Optional, Sequence, Set, cast, ClassVar

#a Mif file handling
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

