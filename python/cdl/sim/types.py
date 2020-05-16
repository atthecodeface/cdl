from typing import Tuple, Any, Union, Dict, List, Callable, Type, Optional, Sequence, Set, cast, ClassVar, Iterable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .wires import Wire, WireHierarchy
#    from .wires import Clock
#    from .hardware import Hardware, HardwareDescription
#    from .connectivity import Connectivity
    pass

Prefix       = List[str]
Wiring       = Union['Wire','WireHierarchy']
WiringDict   = Dict[str,Any] # Recursive
WiringOrDict = Union[Wiring,WiringDict]
ClockDict    = Dict[str,'Clock']

