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
PREREQS = SBi
include ${CDL_SCRIPTS_DIR}/makefile_hdr

#a Source files
CYC_SRCS = \
	c_type_value_pool.cpp \
	c_library.cpp \
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

SRC_DIR = .
OBJ_DIR = ${CDL_BUILD_ROOT}/cdl_frontend

#a Objects
CMD_SRCS = ${CYC_SRCS} cyclicity.cpp
CMD_OBJS = $(call objs_from_srcs,${OBJ_DIR},${CMD_SRCS})
CMD_OBJS += ${OBJ_DIR}/cyclicity_grammar.o

$(eval $(call compile_cpps,${OBJ_DIR},${SRC_DIR},${CMD_SRCS},-I${OBJ_DIR},${OBJ_DIR}/cyclicity_grammar.h))
$(eval $(call bison_to_h_and_o,${OBJ_DIR},${SRC_DIR},cyclicity_grammar.y))

CMDLINE_PROG = ${CDL_BUILD_BIN_DIR}/cdl

clean:
	@rm -f ${CMD_OBJS} ${CMDLINE_PROG} ${OBJ_DIR}/cyclicity_grammar.h ${OBJ_DIR}/cyclicity_grammar.cpp ${OBJ_DIR}/*.P core.*
	mkdir -p ${OBJ_DIR}

build: ${CMDLINE_PROG}
$(eval $(call make_static_binary,${CMDLINE_PROG},${CMD_OBJS},${CYCLICITY_LIBS} -lc))
$(eval $(call install_static_binary,cdl))

#a Clean, depend, etc
$DEPFILES := $(patsubst %.y,${OBJ_DIR}/%.P,$(SRCS:%.cpp=${OBJ_DIR}/%.P))

-include $DEPFILES

