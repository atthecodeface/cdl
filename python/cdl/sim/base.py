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
#class py_engine(ModuleType):
#    class py_engine(PyEngine):
#        pass
#    def debug(self, level:int) -> None : ...
#    pass
class BaseEngine(py_engine.engine):
    pass

x=BaseEngine()

class BaseExecFile(py_engine.exec_file):
    def check_me(self):
        print("Check me!")
        pass
    pass

