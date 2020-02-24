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
PREREQS = SBi
include ${CDL_SCRIPTS_DIR}/makefile_hdr

#a Source files
CYC_SRCS = \
	cyclicity_grammar.y \
	c_type_value_pool.cpp \
	c_cyc_object.cpp \
	c_co_constructors.cpp \
	c_co_chain.cpp \
	c_co_expression.cpp \
	c_co_toplevel_cross_reference.cpp \
	c_co_toplevel_evaluate.cpp \
	c_co_module_cross_reference_pre_type_resolution.cpp \
	c_co_module_type_resolution.cpp \
	c_co_module_cross_reference_post_type_resolution.cpp \
	c_co_module_check_types.cpp \
	c_co_module_evaluate_constant_expressions.cpp \
	c_co_module_high_level_checks.cpp \
	c_co_build_model.cpp \
	c_lexical_analyzer.cpp \
	c_cyclicity.cpp

OBJ_DIR = ${CDL_BUILD_ROOT}/cdl_frontend

#a Objects
objs_from_srcs = $(foreach SRC,${1},$(patsubst %.cpp,${OBJ_DIR}/%.o,${SRC:.y=.cpp}))
CYC_OBJS = $(call objs_from_srcs,${CYC_SRCS})

CMD_SRCS = ${CYC_SRCS} cyclicity.cpp
CMD_OBJS = $(call objs_from_srcs,${CMD_SRCS})

PY_SRCS = ${CYC_SRCS} py_cyclicity.cpp
PY_OBJS = $(call objs_from_srcs,${CMD_SRCS})

SRCS =  ${CYC_SRCS} py_cyclicity.cpp cyclicity.cpp

#a Resultant 'libraries'
CMDLINE_PROG = ${CDL_BIN_DIR}/cdl
PY_LIB       = ${OBJ_DIR}/py_cdl.${LIB_EXT}
ifeq ($(BUILD_PYTHON),no)
	PY_LIB =
endif
PY_LIB =

#a Dependencies and build requirements
clean:
	@rm -f ${CMD_OBJS} ${PY_OBJS} ${CMDLINE_PROG} ${PY_LIB} ${OBJ_DIR}/cyclicity_grammar.h ${OBJ_DIR}/cyclicity_grammar.cpp ${OBJ_DIR}/*.P core.*
	mkdir -p ${OBJ_DIR}

# We put in cyclicity_grammar.h here so that it is built first. Its a hack.
build: ${OBJ_DIR}/cyclicity_grammar.h ${CMDLINE_PROG} ${PY_LIB}

${BACKEND_OBJ}: ${LANGUAGE_OBJS}
	${LINKASBIN} ${BACKEND_OBJ} ${LANGUAGE_OBJS}

${CMDLINE_PROG}: $(CMD_OBJS) $(CYCLICITY_OBJS)
	${LINKASBIN} ${CMDLINE_PROG} $(CMD_OBJS) ${CYCLICITY_OBJS} ${LD_LIBS}

${PY_LIB}: $(PY_OBJS)
	${LINKDYNLIB} ${PY_LIB} ${PY_OBJS} ${CYCLICITY_OBJS} ${LD_LIBS}


${OBJ_DIR}/cyclicity_grammar.h: cyclicity_grammar.y
ifeq (${BISON_VERSION},2.5)
	bison -v --defines=$@ cyclicity_grammar.y
else
	bison -v -d -o ${OBJ_DIR}/ignore.me$(BISON_TAIL) cyclicity_grammar.y
	mv ${OBJ_DIR}/ignore.me.h ${OBJ_DIR}/cyclicity_grammar.h
endif

${OBJ_DIR}/cyclicity_grammar.cpp: cyclicity_grammar.y
	@rm -f ${OBJ_DIR}/cyclicity_grammar.cpp
	bison --debug cyclicity_grammar.y -o ${OBJ_DIR}/cyclicity_grammar.cpp

${OBJ_DIR}/cyclicity_grammar.o: ${OBJ_DIR}/cyclicity_grammar.cpp ${OBJ_DIR}/cyclicity_grammar.h
	@echo "CC $< -o $@"
	$(Q)$(CC) -c ${CXXFLAGS} -I${OBJ_DIR} -I${CDL_ROOT}/cdl_frontend $< -o $@

${OBJ_DIR}/%.o : %.cpp ${OBJ_DIR}/cyclicity_grammar.h
	@echo "CC $< -o $@"
	$(Q)$(CC) -c ${CXXFLAGS} -I${OBJ_DIR} -Wp,-MD,${OBJ_DIR}/$*.P $< -o $@

#a Clean, depend, etc
$DEPFILES := $(patsubst %.y,${OBJ_DIR}/%.P,$(SRCS:%.cpp=${OBJ_DIR}/%.P))

-include $DEPFILES

