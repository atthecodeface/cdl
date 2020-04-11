#a Copyright
#  
#  This file 'Makefile' copyright Gavin J Stark 2003, 2004
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
CDL_ROOT    ?= $(abspath $(CURDIR)/../../build_cdl/install)
BUILD_DIR    = $(abspath $(CURDIR)/build)

MODEL_LIST   = $(CURDIR)/../tests/model_list
SRC_ROOT     = $(CURDIR)/../
PYTHON_DIR   = ${SRC_ROOT}/python
ROM_DIR      = ${SRC_ROOT}/roms

MODELS_MAKE  = $(BUILD_DIR)/models.make
TARGET_DIR   = $(BUILD_DIR)

PREFIX_OBJ_DIR  = $(CURDIR)/build/
DEBUG_BUILD     = no

#a Include standard build makefile
include ${CDL_ROOT}/lib/cdl/cdl_simulation.mk

verilog: ${VERILOG_FILES}

TESTS_DIR = ${SRC_ROOT}/tests
VERILATOR_ROOT = ${CDL_ROOT}
VERILATOR_BIN   = ${VERILATOR_ROOT}/bin/verilator
VERILATOR_SHARE = ${VERILATOR_ROOT}/share/verilator
VERILATOR_INCLUDE = ${VERILATOR_SHARE}/include

SV_TEST_HARNESS = vector_test_harness
V_BUILD_DIR = ${BUILD_DIR}/verilator__${SV_TEST_HARNESS}
VERILATOR_TOP_CPP = ${TESTS_DIR}/vector/verilator_top.cpp
test_in_verilator:
	${VERILATOR_BIN} --cc -Mdir ${V_BUILD_DIR} $(TESTS_DIR)/vector/${SV_TEST_HARNESS}.sv ${BUILD_DIR}/vector_sum__width_8.v
	(cd ${V_BUILD_DIR} && make -f V${SV_TEST_HARNESS}.mk)
	g++ -o ${BUILD_DIR}/vsim__${SV_TEST_HARNESS} -I${V_BUILD_DIR} -I${TESTS_DIR}/vector -I ${VERILATOR_INCLUDE}/ ${VERILATOR_INCLUDE}/verilated.cpp ${VERILATOR_TOP_CPP} ${V_BUILD_DIR}/V${SV_TEST_HARNESS}__ALL.a
	${BUILD_DIR}/vsim__${SV_TEST_HARNESS}


#a Editor preferences and notes
# Local Variables: ***
# mode: Makefile ***
# outline-regexp: "#[a!]\\\|#[\t ]*[b-z][\t ]" ***
# End: ***

