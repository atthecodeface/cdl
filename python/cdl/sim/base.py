import sys, os
from typing import Tuple, Any, Union, Dict, List, Callable, Type, Optional, Sequence, Set, cast, ClassVar, Iterable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass
else:
    if "CDL_BUILD_DIR" in os.environ:
        oldpath = sys.path
        sys.path = [os.environ["CDL_BUILD_DIR"]]
        try:
            import py_engine
            pass
        except ImportError:
            raise
        finally:
            sys.path = oldpath
            pass
        pass
    else:
        import py_engine
        pass
    # py_engine.debug(0)
    pass

from types import ModuleType
if TYPE_CHECKING:
    class py_engine(ModuleType):
        class engine(object): ...
        class exec_file(object): ...
        @staticmethod
        def debug(level:int) -> None : ...
        pass
    pass

class BaseEngine(py_engine.engine):
    pass

class BaseExecFile(py_engine.exec_file):
    pass

#a Useful functions
Prefix       = List[str]
def split_name(name:str, sep:str="__") -> Tuple[Optional[str],str]:
    name_split = name.split(sep, 1)
    if len(name_split)<2: return (None, name)
    return (name_split[0], name_split[1])

def join_name(prefix:Prefix, name:str, sep:str="__") -> str:
    if name!="": prefix=prefix+[name]
    return sep.join(prefix)

