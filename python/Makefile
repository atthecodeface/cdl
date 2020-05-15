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
	cdl/__init__.py \
	cdl/verilog.py \
	cdl/parametrize_verilog.py

PYTHON_CDL_SIM_FILES= \
	cdl/sim/__init__.py \
	cdl/sim/c_httpd.py \
	cdl/sim/c_logs.py \
	cdl/sim/c_python_telnetd.py \
	cdl/sim/c_telnetd.py \
	cdl/sim/doc-wiki.txt \
	cdl/sim/log_server.py

#a Add python files
$(eval $(call add_python_files,cdl,${PYTHON_CDL_FILES}))
$(eval $(call add_python_files,cdl/sim,${PYTHON_CDL_SIM_FILES}))

#a Type checking
PYTHON_DIR = $(CURDIR)
PYTHON_SRCS = cdl/sim/engine.py cdl/sim/exec_file.py cdl/sim/base.py cdl/sim/exceptions.py cdl/sim/hardware.py
check_types:
	PYTHONPATH=${PYTHON_DIR}:$PYTHONPATH mypy --strict ${PYTHON_SRCS}
