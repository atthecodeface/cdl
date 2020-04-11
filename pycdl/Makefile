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
	__init__.py \
	c_httpd.py \
	c_logs.py \
	c_python_telnetd.py \
	c_telnetd.py \
	doc-wiki.txt \
	log_server.py

#a Add python files
$(eval $(call add_python_files,${PYTHON_FILES}))
