from typing import Tuple, Any, Union, Dict, List, Callable, Type, Optional, Sequence, Set, cast, ClassVar, Iterable
from typing import TYPE_CHECKING

from .base import Prefix, join_name, split_name
from .hierarchy import Hierarchy, HierarchyElement

WireTypeDictOrInt = Union[int,Dict[str,Any]] # Recursive
def expand_wire_type_dict_or_int(wtdoi:WireTypeDictOrInt, prefix:Prefix=[]) -> Iterable[Tuple[Prefix,int]]:
    if type(wtdoi)==int:
        yield (prefix, wtdoi) # type: ignore
        pass
    else:
        for (sub_n,sub_wtdoi) in wtdoi:  # type: ignore
            for (p,n) in expand_wire_type_dict_or_int(cast(WireTypeDictOrInt, sub_wtdoi), prefix+[sub_n]):
                yield (p,n)
                pass
            pass
        pass
    pass

#a Wire types
#c WireTypeElement - an endpoint in a Wiring hierarchy
class WireTypeElement(HierarchyElement):
    """
    The object that represents a wire[size] in a wire type
    This is akin to a bit[n] - and as such it does not have a name
    """
    _size : int

    #f __init__
    def __init__(self, size:int=1):
        self._size = size
        pass

    #f __str__
    def __str__(self) -> str:
        return "bit[%d]"%(self._size)

    #f get_size
    def get_size(self) -> int:
        return self._size

    #f All done
    pass

#c WireType
class WireType(Hierarchy):
    """
    This class describes a struct wire type or element; it is a hierarchy of itself or WireTypeElements
    Each element has a name given by its parent.

    As a Hierarchy subclass, an instance may be an 'endpoint' which will be a WireTypeElement.
    If this is the case, then the *parent* of that instance will have the name of the element
    """
    #f __init__
    def __init__(self, size:Optional[int]=None, struct:Optional[WireTypeDictOrInt]=None) -> None:
        """
        Create - if given a size, then this is explicitly a bit[n]
        """
        Hierarchy.__init__(self)
        if size is not None:
            self.set_endpoint(WireTypeElement(size=size))
            pass
        elif struct is not None:
            for (prefix, size) in expand_wire_type_dict_or_int(struct):
                if len(prefix)==0:
                    self.set_endpoint(WireTypeElement(size=size))
                    pass
                else:
                    self.add_element(join_name(prefix=prefix,name=""), size)
                    pass
                pass
            pass
        pass

    #f create_subhierarchy
    def create_subhierarchy(self, name:str) -> Hierarchy:
        return self.set_subhierarchy(name, WireType())

    #f create_hierarchy_element
    def create_hierarchy_element(self, name:str, element_args:Any) -> None:
        (size) = element_args
        elt = WireTypeElement(size=size)
        self.create_subhierarchy(name).set_endpoint(elt)
        return

    #f get_endpoint
    def get_endpoint(self) -> WireTypeElement:
        assert self.is_endpoint
        return cast(WireTypeElement, self.endpoint)

    #f get_size - get bit width, only valid if an endpoint
    def get_size(self) -> int:
        return self.get_endpoint().get_size()

    #f get_element
    def get_element(self, name:str) -> Optional['WireType']:
        x = Hierarchy.get_element(self, name)
        return cast(Optional['WireType'], x)

    #f add_element
    def add_element(self, hierarchical_name:str, size:int) -> None:
        """
        Add a wire of the bit size with full hierarchical name in to the dictionary hierarchy
        """
        return self.hierarchy_add_element(name=hierarchical_name, element_args=(size))

    #f iter_element
    def iter_element(self, name:str, prefix:Prefix=[]) -> Iterable[Tuple[Prefix,str,WireTypeElement]]:
        for (pfx, n, elt) in self.hierarchy_iter(name=name, prefix=prefix):
            wire = cast(WireTypeElement, elt)
            yield (pfx, n, wire)
            pass
        pass

    #f get_wiring - is this used?
    def get_wiring(self, name:str) -> Optional['WireType']:
        opt_h = self.hierarchy_get_element(name)
        return cast(Optional[WireType],opt_h)

    #f flatten_element
    def flatten_element(self, name:str, prefix:Prefix=[]) -> List[Tuple[str,'WireTypeElement']]:
        result = []
        for (p,k,w) in self.iter_element(name=name, prefix=prefix):
            result.append((join_name(prefix=p, name=k), w))
            pass
        return result

    #f as_string
    def as_string(self, name:str="<wire_struct>") -> str:
        r = ""
        for (pfx,n,w) in self.iter_element(name=name):
            r+=" %s[%d]"%(join_name(pfx,n,"."),w.get_size())
            pass
        return r

    #f __str__
    def __str__(self) -> str:
        return self.as_string()

    #f All done
    pass


