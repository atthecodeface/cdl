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

PYTHON_FILES= \
	cdl/__init__.py \
	cdl/verilog.py \
	cdl/parametrize_verilog.py \
	cdl/sim/__init__.py \
	cdl/sim/c_httpd.py \
	cdl/sim/c_logs.py \
	cdl/sim/c_python_telnetd.py \
	cdl/sim/c_telnetd.py \
	cdl/sim/doc-wiki.txt \
	cdl/sim/log_server.py

#a Add python files
$(eval $(call add_python_files,${PYTHON_FILES}))