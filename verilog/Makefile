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

VERILOG_FILES= \
	verilator/srams.v \
	verilator/clock_gate_module.v \
	altera/srams.v \
	altera/clock_gate_module.v \
	xilinx/srams.v \
	xilinx/clock_gate_module.v

#a Add verilog files
$(eval $(call add_verilog_files,${VERILOG_FILES}))
