#a Copyright
#  
#  This file 'Makefile' copyright Gavin J Stark 2003, 2004, 2020
#  
#  This is free software; you can redistribute it and/or modify it however you wish,
#  with no obligations
#  
#  This software is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even implied warranty of MERCHANTABILITY
#  or FITNESS FOR A PARTICULAR PURPOSE.

include ${CDL_ROOT}/Makefile_build_config
PREREQS = 
include ${CDL_SCRIPTS_DIR}/makefile_hdr

#a Source files
BASIC_LIB_SRCS := \
		sl_debug.cpp \
		c_sl_error.cpp \
		sl_cons.cpp \
		sl_token.cpp \
		sl_mif.cpp \
		sl_indented_file.cpp \
		sl_ef_lib_memory.cpp \
		sl_ef_lib_fifo.cpp \
		sl_ef_lib_event.cpp \
		sl_ef_lib_random.cpp \
		sl_random.cpp \
		sl_data_stream.cpp \
		sl_fifo.cpp \
		sl_hier_mem.cpp \
		sl_work_list.cpp \
		sl_pthread_barrier.cpp \
		sl_general.cpp

INCLUDES = c_sl_error.h \
			sl_debug.h

SRCS = ${BASIC_LIB_SRCS}
OBJ_DIR = ${CDL_BUILD_ROOT}/support_libraries

#a Objects
objs_from_srcs = $(foreach SRC,${1},$(patsubst %.cpp,${OBJ_DIR}/%.o,${SRC:.y=.cpp}))
BASIC_LIB_OBJS  := $(call objs_from_srcs,${BASIC_LIB_SRCS})
PLAIN_LIB_OBJS  := ${BASIC_LIB_OBJS} ${OBJ_DIR}/sl_exec_file.o        ${OBJ_DIR}/sl_option.o 
PYTHON_LIB_OBJS := ${BASIC_LIB_OBJS} ${OBJ_DIR}/sl_exec_file_python.o ${OBJ_DIR}/sl_option_python.o

#a Resultant 'libraries'
PLAIN_LIBRARY  := ${CDL_LIB_DIR}/sl_support.o
PYTHON_LIBRARY := ${CDL_LIB_DIR}/sl_support_with_python.o
ifeq ($(BUILD_PYTHON),no)
PYTHON_LIBRARY :=
endif

#a Dependencies and build requirements
clean:
	@rm -f ${PLAIN_LIBRARY} ${PYTHON_LIBRARY} ${PLAIN_LIB_OBJS} ${PLAIN_LIB_OBJS} ${PYTHON_LIB_OBJS} ${OBJ_DIR}/*.P core.*
	mkdir -p ${OBJ_DIR}

build: ${PLAIN_LIBRARY} ${PYTHON_LIBRARY}

${PLAIN_LIBRARY}: ${PLAIN_LIB_OBJS}
	${LINKASOBJ} ${PLAIN_LIBRARY} ${PLAIN_LIB_OBJS}

${PYTHON_LIBRARY}: ${PYTHON_LIB_OBJS}
	${LINKASOBJ} ${PYTHON_LIBRARY} ${PYTHON_LIB_OBJS}

#a Special build objects
${OBJ_DIR}/sl_exec_file_python.o: sl_exec_file.cpp
	$(Q)$(CC) ${CXXFLAGS} -I${PYTHON_INCLUDES} -DSL_PYTHON -c sl_exec_file.cpp -o ${OBJ_DIR}/sl_exec_file_python.o
${OBJ_DIR}/sl_option_python.o: sl_option.cpp
	$(Q)$(CC) ${CXXFLAGS} -I${PYTHON_INCLUDES} -DSL_PYTHON -c sl_option.cpp -o ${OBJ_DIR}/sl_option_python.o

#a Clean etc
-include $(SRCS:%.cpp=${CDL_BUILD_OBJ_DIR}/%.P)

#a Default patterns
${OBJ_DIR}/%.o : %.cpp
	@echo "CC $< -o $@"
	$(Q)$(CC) -c ${CXXFLAGS} -Wp,-MD,${OBJ_DIR}/$*.P $< -o $@

#a Include make - copy relevant header files
include:${INCLUDES}
	cp ${INCLUDES} ${CDL_INCLUDE_DIR}
