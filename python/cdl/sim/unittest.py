import unittest
from typing import Tuple, Any, Union, Dict, List, Callable, Type, Optional, Sequence, Set, cast, ClassVar
from .hardware import Hardware
class TestCase(unittest.TestCase):
    hw: Type[Hardware]
    waves_filename = "waves"
    def run_test(self, run_time:int=1000, waves:List[str]=[], hw_args:Dict[str,Any]={}) -> None:
        hw = self.hw(**hw_args)
        hw.reset()
        hw.set_run_time(run_time)
        if len(waves)>0:
            vcd = hw.waves()
            vcd.open(self.waves_filename+".vcd")
            vcd.add_hierarchy(waves)
            vcd.enable()
            pass
        hw.step(run_time)
        self.assertTrue(hw.passed())
        pass
    pass
