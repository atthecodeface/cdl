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

include ${CDL_MAKEFILE_CONFIG}
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

EXTRA_LIB_SRCS := \
	sl_exec_file.cpp \
	sl_option.cpp


INCLUDES = c_sl_error.h \
            sl_ef_lib_event.h \
            sl_exec_file.h \
            sl_indented_file.h \
            sl_random.h \
            sl_cons.h \
            sl_ef_lib_fifo.h \
            sl_fifo.h \
            sl_mif.h \
            sl_timer.h \
            sl_data_stream.h \
            sl_ef_lib_memory.h \
            sl_general.h \
            sl_option.h \
            sl_token.h \
            sl_debug.h \
            sl_ef_lib_random.h \
            sl_hier_mem.h \
            sl_pthread_barrier.h \
            sl_work_list.h

SRC_DIR = .
SRCS    = ${BASIC_LIB_SRCS}
OBJ_DIR = ${CDL_BUILD_ROOT}/support_libraries

#a Objects
objs_from_srcs = $(foreach SRC,${1},$(patsubst %.cpp,${OBJ_DIR}/%.o,${SRC:.y=.cpp}))
BASIC_LIB_OBJS  := $(call objs_from_srcs,${BASIC_LIB_SRCS})
PLAIN_LIB_OBJS  := ${BASIC_LIB_OBJS} ${OBJ_DIR}/sl_exec_file.o        ${OBJ_DIR}/sl_option.o 
PYTHON_LIB_OBJS := ${BASIC_LIB_OBJS} ${OBJ_DIR}/sl_exec_file_python.o ${OBJ_DIR}/sl_option_python.o

#a Make include - copy relevant header files
$(eval $(call add_includes,${INCLUDES}))

#a Clean, dependencies and build requirements
$(eval $(call compile_cpps,${OBJ_DIR},${SRC_DIR},${BASIC_LIB_SRCS}))
$(eval $(call compile_cpps,${OBJ_DIR},${SRC_DIR},${EXTRA_LIB_SRCS}))
$(eval $(call compile_cpps,${OBJ_DIR},${SRC_DIR},${EXTRA_LIB_SRCS},-DSL_PYTHON ${PYTHON_INCLUDE},,_python))

clean:
	@rm -f ${PLAIN_LIBRARY} ${PYTHON_LIBRARY} ${PLAIN_LIB_OBJS} ${PLAIN_LIB_OBJS} ${PYTHON_LIB_OBJS} ${OBJ_DIR}/*.P
	mkdir -p ${OBJ_DIR}

build: ${CDL_BUILD_LIB_DIR}/${SUPPORT_PLAIN_LIBRARY}
$(eval $(call make_static_library,${CDL_BUILD_LIB_DIR}/${SUPPORT_PLAIN_LIBRARY},${PLAIN_LIB_OBJS}))
$(eval $(call install_static_library,${CDL_BUILD_LIB_DIR},${SUPPORT_PLAIN_LIBRARY}))

ifeq ($(BUILD_PYTHON),yes)
build: ${CDL_BUILD_LIB_DIR}/${SUPPORT_PYTHON_LIBRARY}
$(eval $(call make_static_library,${CDL_BUILD_LIB_DIR}/${SUPPORT_PYTHON_LIBRARY},${PYTHON_LIB_OBJS}))
$(eval $(call install_static_library,${CDL_BUILD_LIB_DIR},${SUPPORT_PYTHON_LIBRARY}))
endif

#a Include dependencies
-include $(SRCS:%.cpp=${OBJ_DIR}/%.P)

