#a Imports
from typing import List, Dict, Optional, Any, Iterable, Tuple, Type, Union

#a Useful functions
#f mask_of_width
def mask_of_width(width:int) -> int:
    return (1<<width)-1

#a Validation
# Default brief
class Validation(object):
    errors : List[Tuple[List[Any],str]]
    stack : List[Any]
    def __init__(self) -> None:
        self.errors = []
        self.stack = []
        pass
    def push(self, reason:Any) -> None:
        self.stack.append(reason)
        pass
    def pop(self) -> None:
        self.stack.pop()
        pass
    def add_error(self, error:str) -> None:
        self.errors.append((list(self.stack), error))
        pass
    pass

#a CsrAccess
#f CsrAccess
class CsrAccess(object):
    read  : bool
    write : bool
    pass

#f CsrAccessRW
class CsrAccessRW(CsrAccess):
    read  = True
    write = True
    pass

#f CsrAccessRO
class CsrAccessRO(CsrAccess):
    read  = True
    write = False
    pass

#f CsrAccessWO
class CsrAccessWO(CsrAccess):
    read  = False
    write = True
    pass

#a BaseObject - an object whose properties can be overriden at instantiation time
#f BaseObject
class BaseObject(object):
    _permitted_fields : Dict[str,type] = {}
    def __init__(self, **kwargs:Any):
        for (k,v) in kwargs.items():
            if k not in self._permitted_fields:
                raise Exception("Unknown field '%s' in %s"%(k,self.__class__.__name__))
            pat = self._permitted_fields[k]
            if type(v)==type:
                if not issubclass(v,pat):
                    raise Exception("Incorrect type for field '%s' - got %s, expected %s in %s"%(k,str(v),str(pat),self.__class__.__name__))
                pass
            elif not issubclass(type(v),pat):
                raise Exception("Incorrect type for field '%s' - got %s, expected %s in %s"%(k,str(type(v)),str(pat),self.__class__.__name__))
            setattr(self,"_"+k,v)
            pass
        pass
    def _ensure(self, name:str, default:Any) -> None:
        if name[0] != "_": name="_"+name
        if hasattr(self, name): return
        setattr(self,name,default)
        return
    pass

#a CsrReset - a BaseObject
#f CsrReset
class CsrReset(BaseObject):
    undefined : bool
    value : int
    _permitted_fields = {"value":int, "undefined":bool}
    #f _validate
    def _validate(self, validation:Validation, width:int) -> None:
        if self.undefined: return
        mask = mask_of_width(width)
        if (self.value & mask) != self.value:
            validation.add_error("reset value %d exceeds width of field (%d)"%(self.value, width))
            pass
        pass
    #f All done
    pass
    
#a CsrField* - BaseObjects
#f CsrFieldBase
class CsrFieldBase(BaseObject):
    #t These properties are user accessible    
    _name  : str
    _doc   : str
    _brief : str
    _width : int
    _access: CsrAccess
    _permitted_fields = {"name":str, "doc":str, "brief":str, "width":int}
    
    #f __init__
    def __init__(self, **kwargs:Any) -> None:
        BaseObject.__init__(self, **kwargs)
        if hasattr(self,"_name"): # Not true for zero!
            self._ensure("_brief",self._name)
            pass
        pass
    #f _mask
    def _mask(self) -> int: return mask_of_width(self._width)
    #f _validate - validate within a width
    def _validate(self, validation:Validation, width:int) -> None:
        # Check names are a-z0-9_
        # Check briefs are a-z0-9
        # Check briefs are from standard dictionary
        pass
    #f All done
    pass

#c CsrFieldZero - a CsrFieldBase which is read and write of zero
class CsrFieldZero(CsrFieldBase):
    """
    Any width field whose contents are read zero, written as zero
    """
    name = "zero"
    brief = "zero"
    doc = "read zero, write as zero"
    _permitted_fields = dict(CsrFieldBase._permitted_fields)
    del _permitted_fields["name"]
    del _permitted_fields["brief"]
    del _permitted_fields["doc"]
    pass

#c CsrFieldResvd - a CsrFieldBase that should not be written non-zero
class CsrFieldResvd(CsrFieldBase):
    name = "reserved"
    brief = "resvd"
    doc = "read undefined, write as zero"
    _permitted_fields = dict(CsrFieldBase._permitted_fields)
    del _permitted_fields["name"]
    del _permitted_fields["brief"]
    del _permitted_fields["doc"]
    pass

#c CsrFieldUser - a CsrFieldBase that has a reset value
class CsrFieldUser(CsrFieldBase):
    _reset : CsrReset
    _permitted_fields = dict(CsrFieldBase._permitted_fields)
    _permitted_fields["reset"] = CsrReset
    #f _validate
    def _validate(self, validation:Validation, width:int) -> None:
        CsrFieldBase._validate(self, validation, width)
        validation.push(self)
        self._reset._validate(validation, self._width)
        validation.pop()
        pass

#c CsrField - a CsrFieldUser
class CsrField(CsrFieldUser):
    pass

#c CsrFieldEnum - a CsrField
class CsrFieldEnum(CsrField):
    values : Dict[int, Tuple[str,str]]
    _permitted_fields = dict(CsrField._permitted_fields)
    _permitted_fields["values"] = dict
    pass

#c CsrFieldVariants - a CsrField
class CsrFieldVariants(CsrField):
    variants: Dict[str,CsrField]
    _permitted_fields = dict(CsrField._permitted_fields)
    _permitted_fields["variants"] = dict
    pass

#c CsrFieldIter - a CsrField
class CsrFieldIter:
    #t Instance property types
    fields: Dict[int,CsrField] # non-overlapping fields
    #f _iter_fields
    def _iter_fields(self) -> Iterable[Tuple[int,CsrField]]:
        for f in self.fields.items(): yield f
        pass
    #f _validate
    def _validate(self, validation:Validation, width:int) -> None:
        mask = 0
        reg_mask = mask_of_width(width)
        for b,f in self._iter_fields():
            m = f._mask()
            if (m & mask)!=0:
                validation.add_error("Field %s (bits [%d;%d]) overlaps with other fields"%(f._name,f._width,b))
                pass
            if (m & reg_mask)!=m:
                validation.add_error("Field %s (bits [%d;%d]) extends beyond range permitted"%(f._name,f._width,b))
                pass
            mask |= m
            pass
        for b,f in self._iter_fields():
            f._validate(validation, width-b)
            pass
        pass
    pass
    
#c CsrFieldGroup - a CsrField AND CsrFieldIter
class CsrFieldGroup(CsrField, CsrFieldIter):
    _fields : Dict[int, CsrField ] = {}
    _permitted_fields = dict(CsrField._permitted_fields)
    _permitted_fields["fields"] = dict
    #f __init__
    def __init__(self, fields:Dict[int,CsrField]={}, **kwargs:Any):
        self._fields = dict(self._fields)
        self._fields.update(fields)
        CsrField.__init__(self, **kwargs)
        pass
    pass

#a Csr - BaseObject and CsrFieldIter
class Csr(BaseObject, CsrFieldIter):
    _fields : Dict[int, CsrField] = {}
    _width : int
    _address : int # Filled in at instantiation
    _select  : int # Filled in at instantiation
    _permitted_fields = {"fields":dict, "address":int, "select":int}
    def __init__(self, width:Optional[int]=None, fields:Dict[int,CsrField]={}, **kwargs:Any):
        if width is not None: self._width = width
        assert hasattr(self,"_width")
        self._fields = dict(self._fields)
        self._fields.update(fields)
        BaseObject.__init__(self, **kwargs)
        pass
    def _validate(self, validation:Validation, width:int) -> None:
        validation.push(self)
        CsrFieldIter._validate(self, validation, width=self._width)
        validation.pop()
        pass
    def Address(self) -> int: return self._address
    def Select(self) -> int: return self._select
    pass

#a Maps
#c Map
class Map(BaseObject):
    _map           : List['MapEntry'] = []
    _width         : int # width of data on bus
    _select        : int # value for 'select' bus entry (if any, 0 otherwise)
    _address       : int # base value for 'address' bus entry (if any, 0 otherwise)
    _shift         : int # amount to shift left internal register numbers by to add to address
    _address_size  : int # NOT log 2 - actual size of address space allocated by parent (0-> dont check)
    _permitted_fields = {"width":int, "select":int, "address":int, "shift":int, "address_size":int}
    _map_entries   : Dict[str,Union[Csr,'MapEntry']] # Entries that have been instantiated by being requested
    def __init__(self, parent:Optional['Map']=None, **kwargs:Any):
        """
        When the map is instantiated:

        _address is within the *root* of the address map tree where it resides
        _shift is that required by the *root* of the address map tree (i.e. if root is byte address it may well be 2 even if intervening maps are 0)
        """
        BaseObject.__init__(self, **kwargs)
        if parent is not None:
            self._ensure("width",parent._width)
            self._ensure("select",parent._select)
            pass
        else:
            self._ensure("width",32)
            self._ensure("select",0)
            pass
        self._ensure("address",0)
        self._ensure("shift",0)
        self._ensure("address_size",0)
        self._map_entries = {}
        pass
    def _get_address(self, offset:int) -> int:
        return self._address + (offset << self._shift)
    def _get_shift(self, shift:int) -> int:
        return self._shift + shift
    def _get_select(self) -> int:
        return self._select
    def _get_width(self) -> int:
        return self._width
    def Get(self, name:str) -> Optional[Any]:
        if name in self._map_entries: return self._map_entries[name]
        for m in self._map:
            if (name==m._name) or (name==m._brief):
                inst = m._instantiate(self)
                self._map_entries[m._name] = inst                
                self._map_entries[m._brief] = inst          
                return inst
            pass
        return None
    def __getattribute__(self, name:str) -> Any:
        if name[0]>'z': return BaseObject.__getattribute__(self, name)
        if name[0]<'a': return BaseObject.__getattribute__(self, name)
        inst = self.Get(name)
        if inst is not None: return inst
        return BaseObject.__getattribute__(self, name)
    pass

#c MapEntry
class MapEntry(BaseObject):
    _name  : str
    _brief : str
    _doc   : str
    def _instantiate(self, map:Map) -> Union['MapEntry',Csr]: ...
    pass

#c MapCsr - a MapEntry with a CSR inside
class MapCsr(MapEntry):
    _reg : int
    _csr : Type[Csr]
    _permitted_fields = {"reg":int, "name":str, "brief":str, "doc":str, "csr":Csr}
    def _instantiate(self, map:Map) -> Union[MapEntry,Csr]:
        address = map._get_address(self._reg)
        select  = map._get_select()
        width   = map._get_width()
        return self._csr(width=width, select=select, address=address)
    pass

#c MapMap - a MapEntry with another map inside
class MapMap(MapEntry):
    _width         : int # width of data on bus (must be less than or equal to parent)
    _select        : int # value for 'select' bus entry (if any, 0 otherwise)
    _offset        : int # base value for 'address' bus entry (if any, 0 otherwise)
    _shift         : int # amount to shift left internal register numbers by to add to address
    _size          : int # NOT log 2 - actual size of address space allocated by parent (0-> dont check
    _map           : Type['MapEntry']
    _permitted_fields = {"name":str, "brief":str, "doc":str, "width":int, "select":int, "offset":int, "shift":int, "size":int, "map":Map}
    def __init__(self, parent:Optional['Map']=None, **kwargs:Any):
        BaseObject.__init__(self, **kwargs)
        if parent is not None:
            self._ensure("width",parent._width)
            self._ensure("select",parent._select)
            pass
        else:
            self._ensure("width",32)
            self._ensure("select",0)
            pass
        self._ensure("offset",0)
        self._ensure("shift",0)
        self._ensure("size",0)
        self._ensure("brief",self._name)
        pass
    def _instantiate(self, map:Map) -> MapEntry:
        address = map._get_address(self._offset)
        shift   = map._get_shift(self._shift)
        return self._map(parent=map, width=self._width, select=self._select, address=address, shift=shift)
    pass

#a CsrValue
class CsrValue(object):
    _csr_type: Csr
    _value   : int
    def __init__(self, value:int=0, csr_type:Optional[Csr]=None):
        if csr_type is not None: self._csr_type=csr_type
        assert hasattr(self,"_csr_type")
        self._value = value
        pass
    def Value(self) -> int: return self._value
    
