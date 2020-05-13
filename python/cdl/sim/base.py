import sys, os
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

