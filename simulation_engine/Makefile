#a Copyright
#  
#  This file 'Makefile' copyright Gavin J Stark 2003, 2004
#  
#  This is free software; you can redistribute it and/or modify it under
#  the terms of the GNU Lesser General Public License as published by the Free Software
#  Foundation, version 2.1.
#  
#  This software is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even implied warranty of MERCHANTABILITY
#  or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License
#  for more details.

#a Global variables
include ${CDL_SRC_ROOT}/Makefile_build_config
PREREQS = S
include ${CDL_SCRIPTS_DIR}/makefile_hdr

SPECIFIC_INCLUDES =
ifeq ("$(BUILD_PYTHON)","yes")
SPECIFIC_INCLUDES += -D SE_ENGINE_PYTHON -DSL_PYTHON -I${PYTHON_INCLUDES}
endif

#a Source files
ENGINE_SRCS = \
		se_cmodel_assist.cpp \
		se_internal_module.cpp \
		se_internal_module__ddr.cpp \
		se_internal_module__sram.cpp \
		se_internal_module__sram_srw.cpp \
		se_internal_module__sram_mrw.cpp \
		se_internal_module__logger.cpp \
		se_internal_module__test_harness.cpp \
		se_external_module.cpp \
		se_engine_function.cpp \
		c_se_engine__checkpoint_restore.cpp \
		c_se_engine__interrogation.cpp \
		c_se_engine__instantiation.cpp \
		c_se_engine__registration.cpp \
		c_se_engine__submodule.cpp \
		c_se_engine__simulation.cpp \
		c_se_engine__waveform.cpp \
		c_se_engine__coverage.cpp \
		c_se_engine__log.cpp \
		c_se_engine.cpp

INCLUDES = se_cmodel_assist.h \
			c_se_engine.h \
			se_errors.h \
			se_external_module.h

SRCS = ${ENGINE_SRCS}
OBJ_DIR = ${CDL_BUILD_ROOT}/simulation_engine

#a Objects
objs_from_srcs = $(foreach SRC,${1},$(patsubst %.cpp,${OBJ_DIR}/%.o,${SRC:.y=.cpp}))
ENGINE_OBJS = $(call objs_from_srcs,${ENGINE_SRCS})

#a Make include - copy relevant header files
$(eval $(call add_includes,${INCLUDES}))

#a Resultant 'libraries'
build: ${CDL_BUILD_LIB_DIR}/${SIMULATION_LIBRARY}
$(eval $(call make_static_library,${CDL_BUILD_LIB_DIR}/${SIMULATION_LIBRARY},${ENGINE_OBJS}))
# $(eval $(call install_static_library,${SUPPORT_PLAIN_LIBRARY}))

#a Default patterns
${OBJ_DIR}/%.o : %.cpp
	@echo "CC $< -o $@"
	$(Q)$(CC) -c ${CXXFLAGS} -Wp,-MD,${OBJ_DIR}/$*.P $< -o $@

#a Clean, depend, etc
clean:
	@rm -f ${LIBRARIES} ${CMDLINE_OBJS} ${PYTHON_OBJS} ${ENGINE_OBJS} ${OBJ_DIR}/*.P core.*
	mkdir -p ${OBJ_DIR}

-include $(SRCS:%.cpp=${OBJ_DIR}/%.P)


