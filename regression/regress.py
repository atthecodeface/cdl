#!/usr/bin/env python3
"""
Unittest harness to run test cases from lib directory
"""

#a Copyright
#
#  This file 'regress' copyright Gavin J Stark 2003, 2004
#
#  This program is free software; you can redistribute it and/or modify it under
#  the terms of the GNU General Public License as published by the Free Software
#  Foundation, version 2.0.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even implied warranty of MERCHANTABILITY
#  or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
#  for more details.

import sys, os, unittest

#a Variables
import os, unittest
import importlib
import sys
import trace
from typing import Any

def add_test_suite(module_name:str)->None:
    # typing will assume m is an empty module and so will abort on m.test_suite
    m : Any = importlib.import_module(module_name, package=__package__)
    if not hasattr(m,"test_suite"):
        raise Exception("Failed to import test_suite from %s - it did not have at test_suite attribute"%module_name)
    for t in m.test_suite :
        globals()["%s__%s"%(module_name,t.__name__)]=t
        pass
    pass

#test_dirs = [ "simple", "vector", "instantiation", "memory", "event", "bugs", "clock_gate", "pycdl" ]
#test_dirs = [ "simple", "vector", "instantiation", "memory"]

add_test_suite(".tests.vector")
add_test_suite(".tests.simple")
add_test_suite(".tests.memory")
add_test_suite(".tests.clock_gate")
add_test_suite(".tests.log")
add_test_suite(".tests.verilog")
add_test_suite(".tests.instantiation")

tracer = trace.Trace(ignoredirs=[sys.prefix, sys.exec_prefix], trace=1, count=1)

if __name__ == "__main__":
    if False:
        tracer.run('unittest.main()')
        r = tracer.results()
        r.write_results(show_missing=True, coverdir=".")
        pass
    else:
        unittest.main()
    pass

raise Exception("Done")
