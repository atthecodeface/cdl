#!/usr/bin/env python3
"""
Unittest harness to run test cases
"""

#a Copyright
#
#  This file 'regress' copyright Gavin J Stark 2003-2020
#
#  This program is free software; you can redistribute it and/or modify it under
#  the terms of the GNU General Public License as published by the Free Software
#  Foundation, version 2.0.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even implied warranty of MERCHANTABILITY
#  or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
#  for more details.

#a Imports
import argparse, sys, re
import sys, os, unittest
import importlib.util
import trace
from pathlib import Path
from typing import Any, Dict, List, Tuple, Set, Iterable, Optional, Type
from typing import TYPE_CHECKING
from types import ModuleType as Module

#a Class
#c Test
class Test(object):
    """
    This object represents a named cdl.sim.TestCase function
    The module_name is the name of the module in which the TestCase class resides
    cls is the TestCase
    test_name is the name of the function (starting test_)
    """
    module_name : str
    cls         : Type[unittest.TestCase]
    test_name   : str
    #f __init__
    def __init__(self, module_name:str, cls:Type[unittest.TestCase], test_name:str):
        self.module_name = module_name
        self.cls = cls
        self.test_name = test_name
        pass
    #f get_cls
    def get_cls(self) -> Type[unittest.TestCase]:
        "Get the TestCase subclass of the test"
        return self.cls
    #f delete
    def delete(self) -> None:
        "Delete this test function from the TestCase class"
        delattr(self.cls, self.test_name)
        pass
    #f All done
    pass

#c TestSuites
class TestSuites(object):
    regression_suite_pkg_name = "regression_suite"
    packages : Dict[str, Module]
    """
    This class represents ALL of the tests from all suites required to be run

    It allows a set of packages to be created which are name:List[path]
    The test suites can import name.thing, where thing is the basename of the path
    """
    #f __init__
    def __init__(self) -> None:
        self.packages = {}
        pass
    
    #f add_test_suite_in_package
    def add_test_suite_in_package(self, pkg_name:str, module_name:str)->None:
        """
        Add a test suite - a Python module that must be loaded and run - 
        within a particular package.
        The package should have been added prior, and <module_name>.py should be
        on one of the paths of that package
        """
        spec   = importlib.util.find_spec("."+module_name, package=pkg_name)
        assert spec is not None
        module = importlib.util.module_from_spec(spec)
        # loader has an exec_module, but typing does not know this
        spec.loader.exec_module(module) # type: ignore
        pass

    #f add_test_package
    def add_test_package(self, file_path:Path, pkg_name:str)->None:
        spec = importlib.util.spec_from_file_location(pkg_name, file_path.joinpath("__init__.py"))
        if spec is None:
            raise Exception("Failed to find package %s at '%s'"%(pkg_name, str(file_path)))
        package = importlib.util.module_from_spec(spec)
        assert package is not None
        self.packages[pkg_name] = package
        sys.modules[pkg_name] = package
        pkg_spec = package.__spec__
        assert pkg_spec is not None
        pkg_spec.submodule_search_locations = []
        pass
    
    #f add_path_to_package
    def add_path_to_package(self, pkg_name:str, path:Path) -> None:
        if pkg_name not in self.packages:
            self.add_test_package(file_path=path, pkg_name=pkg_name)
            pass
        spec = self.packages[pkg_name].__spec__
        assert spec is not None
        assert spec.submodule_search_locations is not None
        spec.submodule_search_locations.append(str(path))
        pass

    #f add_test_suite
    def add_test_suite(self, suite_path:Path, suite_names:List[str]) -> None:
        self.add_path_to_package(pkg_name=self.regression_suite_pkg_name, path=suite_path)
        # self.add_test_package(file_path=suite_path, pkg_name="suite") # Local package
        # suite_package.__spec__.submodule_search_locations.append(args.suite_dir)
        for sn in args.suites:
            self.add_test_suite_in_package(pkg_name=self.regression_suite_pkg_name, module_name=sn)
            pass
        pass

    #f iter_subclasses
    def iter_subclasses(self, cls:Type[object]) -> Iterable[Type[object]]:
        yield cls
        for subcls in cls.__subclasses__():
            for c in self.iter_subclasses(subcls):
                yield c
                pass
            pass
        pass

    #f iter_tests_of_class
    def iter_tests_of_class(self, cls:Type[object]) -> Iterable[Tuple[Type[object],str]]:
        for i in self.iter_subclasses(cls):
            for j in dir(i):
                if j[0:5]=="test_":
                    yield (i,j)
                    pass
                pass
            pass
        pass

    #f build_test_set
    def build_test_set(self) -> None:
        self.tests = {}
        for (cls,test_name) in self.iter_tests_of_class(unittest.TestCase):
            module_name = cls.__module__.partition(".")[2]
            assert issubclass(cls,unittest.TestCase)
            self.tests["%s.%s.%s"%(module_name,cls.__name__,test_name)] = Test(module_name,cls,test_name)
            pass
        pass

    #f get_test_sets
    def get_test_sets(self, only_tests:List[str], exclude_tests:List[str]) -> Tuple[Set[str],Set[str]]:
        """
        Return (all_tests, tests_included, tests_to_exclude_from_tests_included)
        """
        all_tests = self.tests.keys()
        test_set = set(all_tests)
        # If there is an only, start off with no tests
        if len(only_tests)>0: test_set = set()
        for ot in only_tests:
            ot_re = re.compile(ot)
            for tn in all_tests:
                if tn in test_set: continue
                if ot_re.search(tn) is not None:
                    test_set.add(tn)
                    pass
                pass
            pass
        tests_to_exclude = set()
        for et in exclude_tests:
            et_re = re.compile(et)
            for tn in test_set:
                if tn in tests_to_exclude: continue
                if et_re.search(tn) is not None:
                    tests_to_exclude.add(tn)
                    pass
                pass
            pass
        return (test_set, tests_to_exclude)
    #f prune_tests
    def prune_tests(self, test_set:Set[str], prune_if_in_set:bool=False) -> None:
        all_tests = set(self.tests.keys())
        if not prune_if_in_set: test_set=all_tests.difference(test_set)
        for tn in test_set:
            t = self.tests[tn]
            t.delete()
            pass
        pass
    #f iter_tests
    def iter_tests(self, test_set:Optional[Set[str]]=None, list_if_in_set:bool=True) -> Iterable[Tuple[str, Test]]:
        all_tests = set(self.tests.keys())
        if test_set is None: test_set=all_tests
        if not list_if_in_set: test_set = all_tests.difference(test_set)
        for tn in test_set:
            yield (tn, self.tests[tn])
            pass
        pass
    #f list_tests
    def list_tests(self, reason:str, test_set:Optional[Set[str]]=None, list_if_in_set:bool=True) -> None:
        print(reason)
        indent = "   "
        n = 1
        for tn in self.iter_tests(test_set=test_set, list_if_in_set=list_if_in_set):
            print("%s%3d: %s"%(indent, n, tn))
            n = n+1
            pass
        if (n==1):
            print("%s!!! No tests !!!"%indent)
            pass
        pass
    #f load_tests
    def load_tests(self, loader:unittest.TestLoader, tests:int, pattern:int) -> unittest.TestSuite:
        suite = unittest.TestSuite()
        test_classes_added = set()
        for (_,t) in X.iter_tests():
            c = t.get_cls()
            if c not in test_classes_added:
                suite.addTests(loader.loadTestsFromTestCase(c))
                test_classes_added.add(c)
                pass
            pass
        return suite

    #f All done
    pass
#a Top level
#b parser
parser = argparse.ArgumentParser(description='CDL python regression test suite invocation tool')
parser.add_argument('--package-dir', dest="package_dir", action='append', default=[],
                    help='Package <name>:<source directory> pairs; the same package name may appear more than once; a python module <name>.<src_basename> will be added to the globals')
parser.add_argument('--suite-dir', dest="suite_dir", default=".",
                    help='Directory within which the test suite python files reside')
parser.add_argument('suites', nargs='+', 
                    help='test suites to run; must be in <suite_dir>')
parser.add_argument('--list', action="store_true", default=False,
                    help='List tests')
parser.add_argument('--cdl-python', default=None,
                    help='Path to cdl/sim/... python; if not provided, CDL_ROOT environment will be used; is added to PYTHONPATH')
parser.add_argument('--pyengine-dir', default=None,
                    help='Path to pyengine.so; will be added to the PYTHONPATH if provided')
parser.add_argument('--only-tests', action="append", default=[],
                    help='Add a regular expression to search against module.class.test names to only execute')
parser.add_argument('--exclude-tests', action="append", default=[],
                    help='Add a regular expression to search against module.class.test names to exclude after matching with *only*')
parser.add_argument('--trace', action="store_true", default=False,
                    help='Enable python trace')
parser.add_argument('--waves', action="append", default=[],
                    help='Waves to capture - passed to cdl.sim.unittest.TestCase.run_test waves')
parser.add_argument('--run-time', type=int, default=None,
                    help='Run time - passed to cdl.sim.unittest.TestCase.run_test run_time')
parser.add_argument('--hw-args', action="append", default=[],
                    help='Hardware args of the form name:value - passed to cdl.sim.unittest.TestCase.run_test run_time')
args = parser.parse_args()

if args.pyengine_dir is not None:
    sys.path.insert(0, args.pyengine_dir)
    pass

if args.cdl_python is not None:
    sys.path.insert(0, args.cdl_python)
    pass
else:
    if "CDL_ROOT" in os.environ:
        sys.path.insert(0, "%s/lib/cdl/python"%os.environ["CDL_ROOT"])
        pass
    pass
if TYPE_CHECKING:
    from cdl.sim.unittest import TestCase as CdlTestCase
    pass
else:
    from cdl.sim import TestCase as CdlTestCase
    pass

if args.run_time is not None:
    CdlTestCase._set_invocation_run_time(args.run_time)
    pass
if args.waves is not None:
    CdlTestCase._set_invocation_waves(args.waves)
    pass
if args.hw_args is not None:
    for nv in args.hw_args:
        (n,v) = nv.split(":")
        v_int = None
        try:
            v_int = int(v)
            pass
        except:
            pass
        if v_int is not None:
            CdlTestCase._set_invocation_hw_arg(n,v_int)
            pass
        else:
            CdlTestCase._set_invocation_hw_arg(n,v)
            pass
        pass
    pass

#b Build TestSuites
X = TestSuites()
for p in args.package_dir:
    (pkg_name, pkg_dir) = p.split(":")
    X.add_path_to_package(pkg_name, Path(pkg_dir))
    pass

X.add_test_suite(suite_path=Path(args.suite_dir), suite_names=args.suites)
X.build_test_set()
if args.list:
    X.list_tests("Before inclusion/exclusion")
    pass
(included_tests, exclude_tests) = X.get_test_sets(args.only_tests, args.exclude_tests)
X.prune_tests(test_set=included_tests.difference(exclude_tests), prune_if_in_set=False)
X.build_test_set()
if args.list:
    X.list_tests("After inclusion/exclusion")
    pass

#b Execute
load_tests = X.load_tests
if __name__ == "__main__":
    if args.trace:
        tracer = trace.Trace(ignoredirs=[sys.prefix, sys.exec_prefix], trace=1, count=1)
        tracer.run('unittest.main(argv=["cdl_regress"])')
        r = tracer.results()
        r.write_results(show_missing=True, coverdir=".")
        pass
    else:
        unittest.main(argv=["cdl_regress"])
    pass
