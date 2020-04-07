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
BUILD_DIR    = $(abspath $(CURDIR)/build)
MODELS_MAKE := $(BUILD_DIR)/models.make
TARGET_DIR  := $(BUILD_DIR)
MODEL_LIST  := $(CURDIR)/../tests/model_list
SRC_ROOT    := $(CURDIR)/../
PYTHON_DIR  := ${SRC_ROOT}/python
ROM_DIR     := ${SRC_ROOT}/roms
PREFIX_OBJ_DIR := $(CURDIR)/build/
DEBUG_BUILD := no

#a Include standard build makefile
include ${CDL_ROOT}/lib/cdl/simulation_build_make

verilog: ${VERILOG_FILES}

#a Editor preferences and notes
# Local Variables: ***
# mode: Makefile ***
# outline-regexp: "#[a!]\\\|#[\t ]*[b-z][\t ]" ***
# End: ***

