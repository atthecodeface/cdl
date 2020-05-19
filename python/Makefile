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
include ${CDL_MAKEFILE_CONFIG}
include ${CDL_SCRIPTS_DIR}/makefile_hdr

PYTHON_CDL_FILES= \
	cdl/__init__.py

PYTHON_CDL_SIM_FILES_TYPE_CLEAN = \
	cdl/sim/__init__.py \
	cdl/sim/base.py \
	cdl/sim/engine.py \
	cdl/sim/connectivity.py \
	cdl/sim/exceptions.py \
	cdl/sim/exec_file.py \
	cdl/sim/extensions.py \
	cdl/sim/hardware.py \
	cdl/sim/hierarchy.py \
	cdl/sim/instantiable.py \
	cdl/sim/modules.py \
	cdl/sim/th_exec_file.py \
	cdl/sim/types.py \
	cdl/sim/unittest.py \
	cdl/sim/verbose.py \
	cdl/sim/wires.py \
	cdl/sim/waves.py

PYTHON_CDL_UTILS_FILES_TYPE_CLEAN = \
	cdl/utils/__init__.py \
	cdl/utils/memory.py

PYTHON_CDL_TOOLS_FILES_TYPE_CLEAN = \
	cdl/tools/parametrize_verilog.py

PYTHON_CDL_SIM_FILES= \
	${PYTHON_CDL_SIM_FILES_TYPE_CLEAN} \
	cdl/sim/c_httpd.py \
	cdl/sim/c_logs.py \
	cdl/sim/c_python_telnetd.py \
	cdl/sim/c_telnetd.py \
	cdl/sim/doc-wiki.txt \
	cdl/sim/log_server.py

PYTHON_CDL_TOOLS_FILES= \
	${PYTHON_CDL_TOOLS_FILES_TYPE_CLEAN} \
	cdl/tools/cdl_mem_convert.py

PYTHON_CDL_UTILS_FILES= \
	${PYTHON_CDL_UTILS_FILES_TYPE_CLEAN} \
	cdl/utils/verilog.py \
	cdl/utils/xilinx.py

#a Add python files
$(eval $(call add_python_files,cdl,${PYTHON_CDL_FILES}))
$(eval $(call add_python_files,cdl/sim,${PYTHON_CDL_SIM_FILES}))
$(eval $(call add_python_files,cdl/utils,${PYTHON_CDL_UTILS_FILES}))
$(eval $(call add_python_files,cdl/tools,${PYTHON_CDL_TOOLS_FILES}))

#a Type checking
PYTHON_DIR = $(CURDIR)

check_types: check_types_sim check_types_utils check_types_tools

check_types_sim:
	PYTHONPATH=${PYTHON_DIR}:${PYTHONPATH} mypy --strict ${PYTHON_CDL_SIM_FILES_TYPE_CLEAN}

check_types_utils:
	PYTHONPATH=${PYTHON_DIR}:${PYTHONPATH} mypy --strict ${PYTHON_CDL_UTILS_FILES_TYPE_CLEAN}

check_types_tools:
	PYTHONPATH=${PYTHON_DIR}:${PYTHONPATH} mypy --strict ${PYTHON_CDL_TOOLS_FILES_TYPE_CLEAN}
