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
include ${CDL_ROOT}/Makefile_build_config
PREREQS = Si
include ${CDL_SCRIPTS_DIR}/makefile_hdr

#a Source files
BACKEND_SRCS = \
		c_model_descriptor.cpp \
		md_output_markers.cpp \
		md_target_c.cpp \
		md_target_xml.cpp \
		md_target_cdl_header.cpp \
		md_target_verilog.cpp

INCLUDES = be_model_includes.h cdl_version.h

SRCS = ${BACKEND_SRCS}
OBJ_DIR = ${CDL_BUILD_ROOT}/backend

#a Objects
objs_from_srcs = $(foreach SRC,${1},$(patsubst %.cpp,${OBJ_DIR}/%.o,${SRC:.y=.cpp}))
BACKEND_OBJS = $(call objs_from_srcs,${BACKEND_SRCS})

#a Resultant 'libraries'
BACKEND_LIB = ${CDL_BUILD_OBJ_DIR}/be_backend.o

#a Dependencies and build requirements
clean:
	@rm -f ${CMDLINE_PROG} ${BACKEND_OBJS} ${OBJ_DIR}/*.P core.*
	mkdir -p ${OBJ_DIR}

build: ${BACKEND_LIB}

${BACKEND_LIB}: ${BACKEND_OBJS}
	${LINKASOBJ} $@ ${BACKEND_OBJS}

#a Clean etc
-include $(SRCS:%.cpp=${OBJ_DIR}/%.P)

#a Default patterns
${OBJ_DIR}/%.o : %.cpp
	@echo "CC $< -o $@"
	$(Q)$(CC) -c ${CXXFLAGS} -Wp,-MD,${OBJ_DIR}/$*.P $< -o $@

#a Include make - copy relevant header files
include:${INCLUDES}
	cp ${INCLUDES} ${CDL_INCLUDE_DIR}
