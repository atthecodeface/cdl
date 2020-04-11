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
include ${CDL_SRC_ROOT}/Makefile_build_config
PREREQS = seib
include ${CDL_SCRIPTS_DIR}/makefile_hdr

#a Source files
OBJ_DIR = ${CDL_BUILD_ROOT}/execution_harnesses
SRC_DIR = .
CMDLINE_SRCS = \
		eh_scripting_none.cpp \
		eh_batch_mode.cpp

PYTHON_SRCS = \
	eh_scripting_python.cpp \
	eh_py_engine.cpp

VPI_SRCS = eh_vpi.cpp

INCLUDES = eh_scripting.h

SRCS := ${CMDLINE_SRCS}
ifneq ($(BUILD_PYTHON),no)
SRCS := ${SRCS} ${PYTHON_SRCS}
endif
ifneq ($(BUILD_VPI),no)
SRCS := ${SRCS} ${VPI_SRCS}
endif

#a Objects
CMDLINE_OBJS = $(call objs_from_srcs,${OBJ_DIR},${CMDLINE_SRCS})
PYTHON_OBJS  = $(call objs_from_srcs,${OBJ_DIR},${PYTHON_SRCS})
VPI_OBJS     = $(call objs_from_srcs,${OBJ_DIR},${VPI_SRCS})
$(eval $(call compile_cpps,${OBJ_DIR},${SRC_DIR},${CMDLINE_SRCS},))
$(eval $(call compile_cpps,${OBJ_DIR},${SRC_DIR},${PYTHON_SRCS},-DSL_PYTHON -I${PYTHON_INCLUDES}))
$(eval $(call compile_cpps,${OBJ_DIR},${SRC_DIR},${VPI_SRCS},-I${VPI_INCLUDES}))

#a Make include - copy relevant header files
$(eval $(call add_includes,${INCLUDES}))

#a Resultant 'libraries'
build: ${CDL_BUILD_LIB_DIR}/${SIMULATION_LIBRARY_BATCH}
$(eval $(call make_static_library,${CDL_BUILD_LIB_DIR}/${SIMULATION_LIBRARY_BATCH},${CMDLINE_OBJS},cdl_se_no_harness cdl_sl))
$(eval $(call install_static_library,${SIMULATION_LIBRARY_BATCH}))

ifeq ($(BUILD_PYTHON),yes)
build: ${CDL_BUILD_LIB_DIR}/${SIMULATION_LIBRARY_PYTHON}
$(eval $(call make_static_library,${CDL_BUILD_LIB_DIR}/${SIMULATION_LIBRARY_PYTHON},${PYTHON_OBJS},cdl_se_no_harness cdl_sl_python))
$(eval $(call install_static_library,${SIMULATION_LIBRARY_PYTHON}))
endif

ifeq ($(BUILD_VPI),yes)
build: ${VPI_LIB}
${VPI_LIB}: $(VPI_OBJS)
	${LINKASOBJ} $@ ${VPI_OBJS}
endif

#a Clean, dependencies and build requirements
clean:
	@rm -f ${LIBRARIES} ${CMDLINE_OBJS} ${PYTHON_OBJS} ${VPI_OBJS} ${OBJ_DIR}/*.P core.*
	mkdir -p ${OBJ_DIR}

#a Clean etc

-include $(SRCS:%.cpp=${OBJ_DIR}/%.P)



