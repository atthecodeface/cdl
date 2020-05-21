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
REGRESSION_MAKEFILE_DIR = $(dir $(abspath $(firstword $(MAKEFILE_LIST))))

# CDL_ROOT should have bin/cdl, lib/cdl, libexec/cdl, lib/cdl/python/cdl
# Expect for local build we have done
# (cd ${REGRESSION_MAKEFILE_DIR}/.. && ./configure --prefix=${REGRESSION_MAKEFILE_DIR}/../install)
# make MODELS_MAKE= CDL_ROOT=${REGRESSION_MAKEFILE_DIR}/../install SRC_ROOT=${REGRESSION_MAKEFILE_DIR} regress_python
CDL_ROOT     ?= ${REGRESSION_MAKEFILE_DIR}/../install

-include ${CDL_ROOT}/lib/cdl/cdl_templates.mk
SRC_ROOT   = $(abspath ${CURDIR})
OTHER_SRCS =
BUILD_ROOT ?= $(abspath ${CURDIR})/build

all: sim

-include ${BUILD_ROOT}/Makefile

$(eval $(call cdl_makefile_template,${SRC_ROOT},${BUILD_ROOT},${OTHER_SRCS}))

help:
	@echo "'make all' will build the batch simulator and python shared library"
	@echo ""
	@echo "Use 'make regress_python' to run a python library regression"
	@echo "Use 'make regress_batch' to run a batch simulation regression"

regress_python: ${PYSIM}
	(cd ${REGRESSION_MAKEFILE_DIR}/.. && PYTHONPATH=${BUILD_ROOT}:${CDL_ROOT}/lib/cdl/python:${PYTHONPATH} python3 -m regression.regress -v)

do_exec_me: all
	(cd ${BUILD_ROOT} && ./cdl_regression_exec_me )

local_cdl:
	(cd ${REGRESSION_MAKEFILE_DIR}/.. && ./configure --prefix=${REGRESSION_MAKEFILE_DIR}/../install)
	(cd ${REGRESSION_MAKEFILE_DIR}/.. && make clean && make install)

# regress_batch:
# 	CDL_ROOT=${CDL_ROOT} ./regress

# mkdir regression
# make -f ${CDL_ROOT}/cdl/regression/Makefile CDL_ROOT=${CDL_ROOT}/tools SRC_ROOT=${CDL_ROOT}/regression BUILD_ROOT=${CDL_ROOT}/build/cdl/regression clean
# make -f $CDL_ROOT/cdl/regression/Makefile CDL_ROOT=$CDL_ROOT/tools SRC_ROOT=$CDL_ROOT/regression BUILD_ROOT=$CDL_ROOT/build/cdl/regression clean
