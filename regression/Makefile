#a Copyright
#  
#  This file 'Makefile' copyright Gavin J Stark 2003-2020
#  
#  This program is free software; you can redistribute it and/or modify it under
#  the terms of the GNU General Public License as published by the Free Software
#  Foundation, version 2.0.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even implied warranty of MERCHANTABILITY
#  or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
#  for more details.

#a Global variables
CDL_ROOT     = $(abspath $(CURDIR)/../build_cdl/install)

help:
	@echo "'make all' will build the batch simulator and python shared library"
	@echo ""
	@echo "Use 'make regress_python' to run a python library regression"
	@echo "Use 'make regress_batch' to run a batch simulation regression"

all:
	(cd build; ${MAKE} CDL_ROOT=${CDL_ROOT})

clean:
	(cd build; ${MAKE} CDL_ROOT=${CDL_ROOT} clean)

regress_python:
	CDL_ROOT=${CDL_ROOT} ./regress.py

regress_batch:
	CDL_ROOT=${CDL_ROOT} ./regress

verilog:
	(cd build; make verilog)
