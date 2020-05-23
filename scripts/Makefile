#a Copyright
#  
#  This file 'Makefile' copyright Gavin J Stark 2003, 2004
#  
#  This is free software; you can redistribute it and/or modify it however you wish,
#  with no obligations
#  
#  This software is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even implied warranty of MERCHANTABILITY
#  or FITNESS FOR A PARTICULAR PURPOSE.

#a Global variables
include ${CDL_MAKEFILE_CONFIG}
include ${CDL_SCRIPTS_DIR}/makefile_hdr

$(eval $(call install_script,${CDL_SCRIPTS_DIR},cdl_create_make))
$(eval $(call install_data,${CDL_SCRIPTS_DIR},cdl_simulation.mk))
$(eval $(call install_data,${CDL_SCRIPTS_DIR},cdl_templates.mk))
$(eval $(call install_data,${CDL_SCRIPTS_DIR},cdl_templates_old.mk))
$(eval $(call install_script,${CDL_SCRIPTS_DIR},cdl_desc.py))
$(eval $(call install_data,${CDL_CONFIGURED_DIR}/scripts,Makefile_cdl_template_config))

.PHONY: check_python_types
check_python_types: check_python_types_cdl_desc

check_python_types_cdl_desc:
	mypy --strict ${CDL_SCRIPTS_DIR}/cdl_desc.py 
