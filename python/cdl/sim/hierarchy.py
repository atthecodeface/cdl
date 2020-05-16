#!/usr/bin/env python

#a Copyright
#
#  This file 'hierarchy.py' copyright Gavin J Stark 2020
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
from .types     import *
from .base import split_name, join_name
from typing import Tuple, Any, Union, Dict, List, Callable, Type, Optional, Sequence, Set, cast, ClassVar, Iterable

#a Hierarchy
#c Hierarchy
class HierarchyElement(object):
    pass

class Hierarchy(object):
    """
    Fully flattened hierarchy
    This is effectively a Union of [HierarchyElement, Dict[str,Hierarchy]]
    """
    _is_endpoint : bool
    endpoint     : HierarchyElement
    elements     : Dict[str,'Hierarchy']

    #f __init__
    def __init__(self) -> None:
        self.elements = {}
        pass

    #f get_element
    def get_element(self, name:str) -> Optional['Hierarchy']:
        if not self.is_dict(): return None
        if name not in self.elements: return None
        return self.elements[name]

    #f is_endpoint
    def is_endpoint(self) -> bool:
        "Return True if a fleshed-out hierarchy that is an endpoint"
        if not hasattr(self,"_is_endpoint"): return False
        return self._is_endpoint

    #f is_dict
    def is_dict(self) -> bool:
        "Return True if a fleshed-out hierarchy that is a dictionary"
        if not hasattr(self,"_is_endpoint"): return False
        return not self._is_endpoint

    #f is_defined
    def is_defined(self) -> bool:
        "Return True if fleshed-out hierarchy"
        return hasattr(self,"_is_endpoint")

    #f set_endpoint
    def set_endpoint(self, elt:HierarchyElement) -> None:
        assert not self.is_defined()
        self._is_endpoint = True
        self.endpoint = elt
        pass

    #f set_subhierarchy
    def set_subhierarchy(self, name:str, h:'Hierarchy') -> 'Hierarchy':
        assert not self.is_endpoint()
        self._is_endpoint = False
        self.elements[name] = h
        return h

    #f create_subhierarchy
    def create_subhierarchy(self, name:str) -> 'Hierarchy': ...

    #f create_hierarchy_element
    def create_hierarchy_element(self, name:str, element_args:Any) -> None: ...

    #f hierarchy_add_element
    def hierarchy_add_element(self, name:str, element_args:Any) -> None:
        """
        Add an element
        """
        (root, rest) = split_name(name)
        if root is None: # Leaf element
            if name in self.elements:
                raise Exception("Bug in adding '%s' as part of '%s' - duplicate wire or wire which is also a bundle"%(rest, name))
            return self.create_hierarchy_element(name, element_args)
        else: # Find or create hierarchy and add remainder to that
            if root not in self.elements: self.create_subhierarchy(root)
            if self.elements[root].is_endpoint():
                raise Exception("Bug in adding '%s' as part of '%s' - already a wire, now also a bundle"%(rest, name))
            return self.elements[root].hierarchy_add_element(name=rest, element_args=element_args)
        pass

    #f hierarchy_iter
    def hierarchy_iter(self, name:Optional[str]=None, prefix:Prefix=[]) -> Iterable[Tuple[Prefix,str,HierarchyElement]]:
        if not self.is_defined(): return
        subprefix = prefix
        if name is not None: subprefix=prefix+[name]
        if self._is_endpoint:
            yield (subprefix, "", self.endpoint)
            pass
        else:
            for (n,e) in self.elements.items():
                for x in e.hierarchy_iter(name=n, prefix=subprefix): yield x
                pass
            pass
        pass

    #f hierarchy_list
    def hierarchy_list(self, name:Optional[str]=None, prefix:Prefix=[]) -> Iterable[Tuple[Prefix,str,HierarchyElement]]:
        return list(self.hierarchy_iter(name, prefix))

    #f get_hierarchical_element - is this used?
    def get_hierarchical_element(self, remaining_name:str) -> Optional['Hierarchy']:
        (root, rest) = split_name(remaining_name)
        if root is None:
            if rest in self.elements: return self.elements[rest]
            return None
        if root not in self.elements: return None
        return self.elements[root].get_hierarchical_element(remaining_name=rest)

    #f All done
    pass

