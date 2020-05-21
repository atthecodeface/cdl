CDL_ROOT ?= set_cdl_root
include ${CDL_ROOT}/lib/cdl/cdl_templates.mk
BUILD_ROOT = /home/gavin/Git/cdl/regression/build
SIM   ?= ${BUILD_ROOT}/sim
PYSIM ?= ${BUILD_ROOT}/py_engine.so
all: sim
SUBMAKE=${MAKE} CDL_ROOT=${CDL_ROOT}

$(eval $(call toplevel_init_template))

$(eval $(call cdl_makefile_template,/home/gavin/Git/cdl/regression,/home/gavin/Git/cdl/regression/build,))
-include /home/gavin/Git/cdl/regression/build/cdl_regression/Makefile
$(eval $(call sim_add_cdl_library,/home/gavin/Git/cdl/regression/build/cdl_regression,cdl_regression))
${BUILD_ROOT}/cdl_regression/Makefile: /home/gavin/Git/cdl/regression/library_desc.py

$(eval $(call sim_init_object_file_template,${BUILD_ROOT},obj_init,cdl_regression))
$(eval $(call command_line_sim_template,${SIM},${BUILD_ROOT},${BUILD_ROOT}/obj_init.o))
$(eval $(call python_library_template,${PYSIM},${BUILD_ROOT},${BUILD_ROOT}/obj_init.o))

$(eval $(call toplevel_clean_template))
