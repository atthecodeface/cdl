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
CDL_ROOT ?= /set/cdl/root/please
CDL_SCRIPTS_DIR = ${CDL_ROOT}/lib/cdl
LINKASBIN     = g++ -o 
LINKDYNLIB    = linkdynlib
PYTHONLINKLIB = pythonlinklib
CREATE_MAKE   = ${CDL_ROOT}/libexec/cdl/cdl_create_make
BUILD_FLAGS = ${CONFIG_OPTIMIZATION_FLAGS}
CDL_INCLUDE_DIR = ${CDL_ROOT}/include/cdl
CYCLICITY_BIN_DIR      = ${CDL_ROOT}/bin
CYCLICITY_INCLUDES     = -I ${CDL_INCLUDE_DIR} ${SUPPORT_INCLUDES} ${BACKEND_INCLUDES} ${ENGINE_INCLUDES} ${HARNESS_INCLUDES}
CYCLICITY_OBJS         = ${BACKEND_OBJECTS} ${SUPPORT_OBJECTS}
CYCLICITY_PYTHON_OBJS  = ${BACKEND_OBJECTS} ${SUPPORT_WITH_PYTHON_OBJECTS}
CYCLICITY_LIBS          = ${ENGINE_LIBS} ${SUPPORT_LIBS} -L${CDL_ROOT}/lib -lcdl_se_batch
CYCLICITY_PYTHON_LIBS   = ${ENGINE_LIBS} ${SUPPORT_LIBS} -L${CDL_ROOT}/lib -Wl,--whole-archive -lcdl_se_python
CYCLICITY_PYTHON_LIBS   = ${ENGINE_LIBS} ${SUPPORT_LIBS} -L${CDL_ROOT}/lib -Wl,-all_load -lcdl_se_python
GPP = g++
FRAMEWORK_PATH = /Library/Frameworks
PYTHONLINKLIB := ${GPP} ${LINKFLAGS} -bundle -framework Python  -Wl,-F${FRAMEWORK_PATH} ${LOCAL_LINKFLAGS} -o
PYTHONLINKLIB := ${GPP} -bundle -L/Users/gavinprivate/Git/brew/opt/python/Frameworks/Python.framework/Versions/3.7/lib/python3.7/config-3.7m-darwin -lpython3.7m -ldl -framework CoreFoundation -o
PYTHONLINKLIB := ${GPP} -bundle -L/Users/gavinprivate/Git/brew/opt/python/Frameworks/Python.framework/Versions/3.7/lib/python3.7/config-3.7m-darwin -lpython3.7m -ldl -framework CoreFoundation -o

PYTHONLINKLIB := ${GPP} -bundle -o
CYCLICITY_PYTHON_LIBS  := -L${CDL_ROOT}/lib -lcdl_se_python -L/Users/gavinprivate/Git/brew/opt/python/Frameworks/Python.framework/Versions/3.7/lib/python3.7/config-3.7m-darwin -lpython3.7m -ldl -framework CoreFoundation -lc++ -lc 

${OS_DIR}/%.o : %.cpp
	@echo "CC $< -o $@"
	$(Q)$(CC) -c ${CXXFLAGS} -Wp,-MD,${OS_DIR}/$*.P $< -o $@

${TARGET_DIR}/%.o : %.cpp
	@echo "CC $< -o $@"
	$(Q)$(CC) -c ${CXXFLAGS} -Wp,-MD,${TARGET_DIR}/$*.P $< -o $@


LIBS = 
LIB_DEP_EXT = so
LIB_EXT = so

#a Makefile flags
# for verbose builds use Q:=
Q:=@

#a Compiler flags
COMPILE_OPTIMIZATION_FLAGS := -O2 -Wall
LINK_OPTIMIZATION_FLAGS := 
ifeq (${DEBUG_BUILD},yes)
	COMPILE_OPTIMIZATION_FLAGS := -DDEBUG_ENABLED -g -Wall
	LINK_OPTIMIZATION_FLAGS := -g
endif

CFLAGS   = ${COMPILE_OPTIMIZATION_FLAGS} ${CYCLICITY_INCLUDES} ${SPECIFIC_INCLUDES} ${OS_CFLAGS}    ${LOCAL_CFLAGS}
CXXFLAGS = ${COMPILE_OPTIMIZATION_FLAGS} ${CYCLICITY_INCLUDES} ${SPECIFIC_INCLUDES} ${OS_CXXFLAGS}  ${LOCAL_CXXFLAGS}
LINKFLAGS = ${LINK_OPTIMIZATION_FLAGS} -L${CDL_ROOT}/lib/${OS_DIR}                 ${OS_LINKFLAGS} ${LOCAL_LINKFLAGS}
LD_LIBS = ${CYCLICITY_LIBS} -lm -lc

ifeq ($(BUILD_PYTHON),no)
SUPPORT_COMMAND_OBJS := ${HARNESS_BATCH_OBJECTS} ${CYCLICITY_OBJS}
SUPPORT_PYTHON_OBJS  := ${HARNESS_GUI_OBJECTS}   ${CYCLICITY_OBJS}
SUPPORT_VPI_OBJS     := ${HARNESS_VPI_OBJECTS}   ${CYCLICITY_OBJS}
else
SUPPORT_COMMAND_OBJS := ${HARNESS_BATCH_OBJECTS} ${CYCLICITY_OBJS}
SUPPORT_PYTHON_OBJS  := ${HARNESS_GUI_OBJECTS}   ${CYCLICITY_PYTHON_OBJS}
SUPPORT_VPI_OBJS     := ${HARNESS_VPI_OBJECTS}   ${CYCLICITY_OBJS}
endif

CMDLINE_PROG := ${TARGET_DIR}/sim
PYTHON_LIB := 
ifneq ($(BUILD_PYTHON),no)
PYTHON_LIB := ${TARGET_DIR}/py_engine.so
endif

ALL2: ALL

include $(MODELS_MAKE)
#models.make

ALL: $(CMDLINE_PROG) ${PYTHON_LIB}

${TARGET_DIR}/derived_model.a: $(TARGET_DIR)/derived_model_list.o ${ENGINE_OBJECTS} ${C_MODEL_OBJS} 
	libtool -static -o $@ ${ENGINE_OBJECTS} ${C_MODEL_OBJS} 

${CMDLINE_PROG}: $(TARGET_DIR)/derived_model_list.o ${TARGET_DIR}/derived_model.a$ ${SUPPORT_COMMAND_OBJS} 
	@echo "Building command line simulation ${CMDLINE_PROG}"
	${Q}${LINKASBIN} ${CMDLINE_PROG} $(TARGET_DIR)/derived_model_list.o ${TARGET_DIR}/derived_model.a ${SUPPORT_COMMAND_OBJS} ${MODEL_LIBS} ${LOCAL_LINKLIBS} ${LD_LIBS}

${PYTHON_LIB}: $(TARGET_DIR)/derived_model_list.o ${TARGET_DIR}/derived_model.a ${SUPPORT_PYTHON_OBJS} 
	@echo "Building Python simulation library for GUI sims ${PYTHON_LIB}"
	${Q}${PYTHONLINKLIB} $@ $(call os_lib_hdr,$@) $(TARGET_DIR)/derived_model_list.o ${TARGET_DIR}/derived_model.a ${SUPPORT_PYTHON_OBJS} ${MODEL_LIBS} ${LOCAL_LINKLIBS} ${CYCLICITY_PYTHON_LIBS}

${VPI_LIB}: $(TARGET_DIR)/derived_model_list.a ${SUPPORT_VPI_OBJS} 
	@echo "Building VPI library for verilog simulation ${VPI_LIB}"
	${Q}${LINKDYNLIB} $@ $(TARGET_DIR)/derived_model_list.o ${SUPPORT_VPI_OBJS} ${MODEL_LIBS} ${LOCAL_LINKLIBS} ${CYCLICITY_LIBS}

# models.make
$(TARGET_DIR)/derived_model_list.o: Makefile ${MODELS_MAKE}
	@echo "Creating derived_mode_list source"
	@echo "#include <stdlib.h>" > ${TARGET_DIR}/derived_model_list.cpp
	@echo "#include <stdio.h>" >> ${TARGET_DIR}/derived_model_list.cpp
	@echo 'extern "C" void *PyInit_py_engine(void); extern void unused(void) {(void)PyInit_py_engine();}' >> ${TARGET_DIR}/derived_model_list.cpp
	@echo "typedef void (*t_python_init_fn)(void);" >> ${TARGET_DIR}/derived_model_list.cpp
	@for a in ${MODELS}; do \
		echo "extern void $${a}__init( void );" >> ${TARGET_DIR}/derived_model_list.cpp; \
	done
	@echo "t_python_init_fn model_init_fns[] = {" >> ${TARGET_DIR}/derived_model_list.cpp
	@for a in ${MODELS}; do \
		echo "$${a}__init," >> ${TARGET_DIR}/derived_model_list.cpp; \
	done
	@echo "NULL" >> ${TARGET_DIR}/derived_model_list.cpp
	@echo "};" >> ${TARGET_DIR}/derived_model_list.cpp
	$(Q)$(CC) $(CXXFLAGS) -c -o ${TARGET_DIR}/derived_model_list.o ${TARGET_DIR}/derived_model_list.cpp
	$(Q)rm ${TARGET_DIR}/derived_model_list.cpp

${MODELS_MAKE}: ${CREATE_MAKE} ${MODEL_LIST}
	@echo "Creating models.make"
	$(Q)${CREATE_MAKE} ${EXTRA_CDLFLAGS} -f ${MODEL_LIST} -m ${MODELS_MAKE}

clean:
	@for a in ${TARGET_DIR}/*cpp ${TARGET_DIR}/*o ${TARGET_DIR}/*v ${TARGET_DIR}/*cdlh ${TARGET_DIR}/*map ${TARGET_DIR}/coverage.map ${CMDLINE_PROG} models.make; do \
		rm -f $${a}; \
	done

backup:
	tar zcvf backups/backup_`date +%y%m%d%H%M`.tgz Makefile ${SRCS} ${HDRS}

#a Editor preferences and notes
# Local Variables: ***
# mode: Makefile ***
# outline-regexp: "#[a!]\\\|#[\t ]*[b-z][\t ]" ***
# End: ***
