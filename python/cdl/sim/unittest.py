import unittest
from typing import Tuple, Any, Union, Dict, List, Callable, Type, Optional, Sequence, Set, cast, ClassVar
from .hardware import Hardware
class TestCase(unittest.TestCase):
    hw: Type[Hardware]
    waves_filename = "waves"
    _invocation_waves    : ClassVar[List[str]] = []
    _invocation_run_time : ClassVar[int]
    _invocation_hw_args  : ClassVar[Dict[str,Any]] = {}
    @classmethod
    def _set_invocation_waves(cls, waves:List[str]) -> None:
        cls._invocation_waves = waves
        pass
    @classmethod
    def _set_invocation_run_time(cls, run_time:int) -> None:
        cls._invocation_run_time = run_time
        pass
    @classmethod
    def _set_invocation_hw_arg(cls, k:str, v:Any) -> None:
        cls._invocation_hw_args[k] = v
        pass
    def run_test(self, run_time:int=1000, waves:List[str]=[], hw_args:Dict[str,Any]={}) -> None:
        waves += self._invocation_waves
        if hasattr(self, "_invocation_run_time"): run_time = self._invocation_run_time
        hw_args = dict(hw_args)
        hw_args.update(self._invocation_hw_args)
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
