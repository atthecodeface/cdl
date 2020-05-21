#a Notes
# Ubuntu 18.04 - VERILATOR_C_FLAGS needs -fPIC
# Building threaded requires -ftls-model=local-dynamic
VERILATOR_C_FLAGS ?= -DVM_COVERAGE=0 -DVM_SC=0 -DVM_TRACE=0 -faligned-new -DVL_THREADED -std=gnu++14 -fPIC -g -ftls-model=local-dynamic
VERILATOR_LIBS    ?= -pthread -lpthread -latomic -lm -lstdc++
VERILATOR         ?= PATH=${VERILATOR_ROOT}/bin:${PATH} ${VERILATOR_ROOT}/bin/verilator

#a Variables if not defined yet
CDL_SCRIPTS_DIR ?= ${CDL_ROOT}/lib/cdl
CDL_BIN_DIR     ?= ${CDL_ROOT}/bin
CDL_LIBEXEC_DIR ?= ${CDL_ROOT}/libexec/cdl
CDL_INCLUDES    ?= -I${CDL_ROOT}/include/cdl
CDL_VERILOG_DIR ?= ${CDL_ROOT}/lib/cdl/verilog
Q?=@

-include ${CDL_SCRIPTS_DIR}/Makefile_cdl_template_config

BUILD_STAMPS = ${BUILD_ROOT}/stamps
TIMESTAMP = date >
CDL_FLAGS += --include-assertions --v_displays

#a Templates
#v Notes
#
# LIB__lib__MODELS contains a list of model names for this library that are to be 'init'ed
# LIB__lib__C_OBJS contains a list of object files to be included in the static library
# BIN__lib__bin__OBJS contains a list of object files to be included in a binary for a library
# LIB__lib__VERILOG contains a list of verilog files to be included in a library

#f toplevel_init_template
define toplevel_init_template
.PHONY: makefiles
$(eval $(call timestamp,verilog))
$(eval $(call timestamp,all_obj))
$(eval $(call timestamp,all_cpp))

ifneq (${VERILATOR_SHARE},)
MODEL_VERILATOR_OBJS = ${BUILD_ROOT}/verilated.o
endif

${BUILD_ROOT}/verilated.o:  ${VERILATOR_SHARE}/include/verilated.cpp
	${Q}${CXX} -c ${VERILATOR_C_FLAGS} ${VERILATOR_SHARE}/include/verilated.cpp -o $$@  -I ${VERILATOR_SHARE}/include -I. $${VERILATOR_LIBS}

endef

#f timestamp
define timestamp
# @param $1 reason (verilog, cpp, etc)
.PHONY: $1
$1: ${BUILD_STAMPS}/$1
${BUILD_STAMPS}/$1:
	${TIMESTAMP} $$@
endef

#f lib_timestamp
define lib_timestamp
# @param $1 reason (verilog, cpp, etc)
# @param $2 library name

$1: ${BUILD_STAMPS}/lib__$2__$1

${BUILD_STAMPS}/$1: ${BUILD_STAMPS}/lib__$2__$1

${BUILD_STAMPS}/lib__$2__$1:
	${TIMESTAMP} $$@

endef

#f lib_timestamp_depends
define lib_timestamp_depends
# @param $1 reason (verilog, cpp, etc)
# @param $2 library name
# @param $3 dependencies
${BUILD_STAMPS}/lib__$2__$1: $3

endef

#f library_init_template
# @param $1 library name
# @param $2 build directory for the library
# @param $3 source directory where library_desc.py sits
# @param $4 library description path for the library
# @param $5 relative_to
define library_init_template
.PHONY: verilog
.PHONY: makefiles
$(eval $(call lib_timestamp,verilog,$1))
$(eval $(call lib_timestamp,all_cpp,$1))
$(eval $(call lib_timestamp,all_obj,$1))

LIB__$1__CLEAN_TARGETS +=
.PHONY: lib__$1__clean
clean: lib__$1__clean

lib__$1__clean:
	@echo "Clean library $1"
	${Q}rm -rf $${LIB__$1__CLEAN_TARGETS}

verilog_$1: $${LIB__$1__VERILOG}
verilog: verilog_$1

clean_verilog_$1:
	@echo "Delete library $1 verilog files"
	${Q} rm -f $${LIB__$1__VERILOG}

clean_verilog: clean_verilog_$1

endef

#f toplevel_clean_template
define toplevel_clean_template

clean: clean_build

clean_build:
	rm -f ${BUILD_STAMPS}/*
	rm -f ${SIM}
	rm -f ${BUILD_ROOT}/obj_init.o
	mkdir -p ${BUILD_ROOT}
	mkdir -p ${BUILD_STAMPS}

endef

#f cdl_makefile_template
define cdl_makefile_template
# @param $1 required source directory - where library_desc.py exists
# @param $2 build directory - where to put Makefile
# @param $3 other source directories - where libraries may exist
#
# This must be invoked AFTER a -include of the created Makefile
# as this will only make the specified makefile ONCE
#
$(eval $(call $(if ${CDL_MAKEFILES_MADE__$2},,cdl_makefile_template_inner),$1,$2,$3))
endef

#f cdl_makefile_template_inner
define cdl_makefile_template_inner
# @param $1 required source directory - where library_desc.py exists
# @param $2 build directory - where to put Makefile
# @param $3 other source directories - where libraries may exist
.PHONY:makefiles
CDL_MAKEFILES_MADE__$2 += $2/Makefile
makefiles: $2/Makefile

BUILD_MAKEFILE = $2/Makefile

$2/Makefile: $(foreach s,$1,$(wildcard ${s}/library_desc.py))
$2/Makefile: $(foreach s,$3,$(wildcard ${s}/library_desc.py))
$2/Makefile: ${CDL_LIBEXEC_DIR}/cdl_desc.py
	${CDL_LIBEXEC_DIR}/cdl_desc.py $(foreach s,$1,--require ${s}) --build_root $2 $3

clean: clean_makefile__$2

clean_makefile__$2:
	rm -f $2/Makefile

endef

#f cpp_template
define cpp_template
# @param $1 library name
# @param $2 cpp source directory
# @param $3 output directory
# @param $4 cpp filename within cpp source directory
# @param $5 model name ("" if not a model)
# @param $6 object filename to go in output dir [model name .o]
# @param $7 C flags
# @param $8 Destination make variable to add object file to

$(if $8,BIN__$1__$8__OBJS,LIB__$1__C_OBJS) += $3/$6
LIB__$1__MODELS += $5
$3/$6 : $2/$4
	@echo "CC $4 -o $6"
	${Q}${CXX} -g -Wall ${CXXFLAGS} ${CDL_INCLUDES} -c -o $$@ $2/$4 $7

LIB__$1__CLEAN_TARGETS += $3/$6

$(eval $(call lib_timestamp_depends,all_obj,$1,$3/$6))

endef

#f cdl_template
define cdl_template
# @param $1 library name
# @param $2 cdl source directory
# @param $3 output directory
# @param $4 cdl filename within cdl source directory
# @param $5 model name
# @param $6 c filename to go in output dir [model name .cpp]
# @param $7 object filename to go in output dir [model name .o]
# @param $8 verilog filename to go in output dir [model name .v]
# @param $9 CDL options
do_all_cdl: $3/$6 $3/$8 $3/$5.cdlh $3/$5.xml

.PHONY: $5
$5: $3/$6 $3/$7 $3/$8  $3/$5.cdlh  $3/$5.xml

$3/$6 : $2/$4
	@echo "CDL $4 -cpp $6"
	${Q}${CDL_BIN_DIR}/cdl $${CDL_FLAGS} --model $5 --dependencies-target $$@ --dependencies $3/$6.dep --dependencies-relative $(dir $2/$4) --cpp $$@  $9 $2/$4

$(eval $(call lib_timestamp_depends,all_cpp,$1,$3/$6))

-include $3/$6.dep

LIB__$1__C_OBJS  += $3/$7
$3/$7 : $3/$6
	@echo "CC $6 -o $7"
	${Q}${CXX} ${CDL_INCLUDES} ${CXXFLAGS} -c -o $$@ $3/$6

$(eval $(call lib_timestamp_depends,all_obj,$1,$3/$7))

LIB__$1__VERILOG += $(if $8,$3/$8,)

$3/$8 : $2/$4
	@echo "CDL $4 -v $8"
	${Q}${CDL_BIN_DIR}/cdl $${CDL_FLAGS} --v_clks_must_have_enables --model $5 --verilog $$@ $9 $2/$4

$(eval $(call lib_timestamp_depends,verilog,$1,$3/$8))

$3/$5.cdlh : $2/$4
	@echo "CDL $4 -cdlh $5"
	${Q}${CDL_BIN_DIR}/cdl $${CDL_FLAGS} --model $5 --cdlh $$@ $9 $2/$4

$3/$5.xml : $2/$4
	@echo "CDL $4 -xml $5"
	${Q}${CDL_BIN_DIR}/cdl $${CDL_FLAGS} --model $5 --xml $$@ $9 $2/$4

LIB__$1__MODELS += $5
LIB__$1__CLEAN_TARGETS += $3/$6 $3/$7 $3/$8 $3/$5.cdlh $3/$5.xml

endef

#f executable_template
define executable_template
# @param $1 library name
# @param $2 executable name
# @param $3 build directory
# @param $4 library build directory
# @param $5 object files within library build directory not in its lib_.a
# @param $6 libraries required ($x/lib_$x.a)
# @param $7 other link flags
.PHONY: $1_$2
$1_$2: $3/$1_$2

all: $3/$1_$2

BIN_OBJS__$1__$2 = $(foreach o,$5,$4/${o}.o)
BIN_LIBS__$1__$2 = $(foreach l,$6,$3/$6/lib_${l}.a)

$3/$1_$2: $${BIN_OBJS__$1__$2} $${BIN_LIBS__$1__$2}
	@echo "Link binary executable $$@"
	${Q}${MAKE_STATIC_BINARY} $$@ $${BIN_OBJS__$1__$2} $${BIN_LIBS__$1__$2} ${LD_FLAGS}

LIB__$1__CLEAN_TARGETS += $3/$1_$2

endef

#f library_init_object_file
#
# The file created here goes in the lib<name>.a
#
define library_init_object_file
# @param $1 library name
# @param $2 output directory
# @param $3 output filename in output directory

$2/$3.cpp: $${LIB__$1__MAKEFILE}
	@echo "Creating library $1 init source $$@"
	${Q}echo "// Library $1 initialization source created by cdl" > $$@
	${Q}for a in $${LIB__$1__MODELS} ; do echo "extern void $$$${a}__init( void );" >> $$@ ; done
	${Q}echo "extern void lib_$1_init(void) {" >> $$@
	${Q}for a in $${LIB__$1__MODELS} ; do echo "$$$${a}__init();" >> $$@ ; done
	${Q}echo "};" >> $$@

LIB__$1__C_OBJS  += $2/$3.o
$2/$3.o: $2/$3.cpp
	@echo "Compile library init module $$@"
	${Q}${CXX} ${CXXFLAGS} -c -o $$@ $$<

LIB__$1__CLEAN_TARGETS += $2/$3.cpp $2/$3.o

endef

#f cdl_library_template
define cdl_library_template
# @param $1 library name
# @param $2 output directory
library: $2/lib_$1.a

lib_$1: $2/lib_$1.a

$2/lib_$1.a: $${LIB__$1__C_OBJS}
	@echo "Link static library $$@"
	${Q}${MAKE_STATIC_LIBRARY} $$@ $${LIB__$1__C_OBJS}

LIB__$1__CLEAN_TARGETS += $2/lib_$1.a

endef

#f sim_add_cdl_library
define sim_add_cdl_library
# @param $1 build directory where library is built
# @param $2 library name
MODEL_LIBS += $1/lib_$2.a

endef

#f sim_init_object_file_template
#
# The file created here links with lib<name>.a and other libraries and an execution harness in libcdl_*.a
#
define sim_init_object_file_template
# @param $1 output directory
# @param $2 output filename in output directory
# @param $3 library names

$1/$2.cpp: ${BUILD_MAKEFILE}
	@echo "Creating init object source $$@"
	${Q}echo "// Object initialization source for library $3 created by cdl" > $$@
	${Q}echo '#include <stdlib.h>' >> $$@
	${Q}echo 'extern "C" void *PyInit_py_engine(void); extern void unused(void) {(void)PyInit_py_engine();}' >> $$@
	${Q}echo "typedef void (*t_init_fn)(void);" >> $$@
	${Q}for a in $3 ; do echo "extern void lib_$$$${a}_init(void);" >> $$@ ; done
	${Q}echo "t_init_fn model_init_fns[] = {" >> $$@
	${Q}for a in $3 ; do echo "lib_$$$${a}_init," >> $$@ ; done
	${Q}echo "NULL};" >> $$@

$1/$2.o: $1/$2.cpp
	${Q}${CXX} ${CXXFLAGS} -c -o $$@ $$<

endef

#f command_line_sim_template
define command_line_sim_template
# @param $1 output filename
# @param $2 output directory
# @param $3 init object files
.PHONY: sim
sim: $1

all: $1

# MODEL_VERILATOR_OBJS should be set once
# MODEL_VERILATOR_LIBS can be added to
# These should be empty if verilator builds are not required
# MODEL_VERILATOR_LIBS = $${VLIB__bbc_micro_with_rams__LIB}
# MODEL_VERILATOR_OBJS = ${BUILD_ROOT}/bbc/verilate/verilated.o
$1: ${MODEL_LIBS} $3 ${MODEL_VERILATOR_OBJS} ${MODEL_VERILATOR_LIBS}
	@echo "Building command line simulation ${CMDLINE_PROG}"
	${Q}${MAKE_STATIC_BINARY} $1 $3 ${MODEL_LIBS} ${MODEL_VERILATOR_LIBS} ${MODEL_VERILATOR_OBJS} -L${CDL_ROOT}/lib -lcdl_se_batch ${LDFLAGS}

endef

#f python_library_template
define python_library_template
# @param $1 output filename
# @param $2 output directory
# @param $3 init object files
.PHONY: python
python: $1

all: $1

# MODEL_VERILATOR_OBJS should be set once
# MODEL_VERILATOR_LIBS can be added to
# These should be empty if verilator builds are not required
# MODEL_VERILATOR_LIBS = $${VLIB__bbc_micro_with_rams__LIB}
# MODEL_VERILATOR_OBJS = ${BUILD_ROOT}/bbc/verilate/verilated.o
$1: ${MODEL_LIBS} ${MODEL_VERILATOR_OBJS} ${MODEL_VERILATOR_LIBS} $3
	@echo "Building python library"
	${Q}${MAKE_DYNAMIC_LIBRARY} $$@ $3 ${MODEL_LIBS} ${MODEL_VERILATOR_LIBS} ${MODEL_VERILATOR_OBJS} -L${CDL_ROOT}/lib -lcdl_se_python ${PYTHON_LIBS} -lc++ -lc ${LDFLAGS}

endef

#f make_cwv_template
# @param $1 library name
# @param $2 cdl source directory
# @param $3 output directory
# @param $4 cdl filename within cdl source directory
# @param $5 model name (not including cwv - must have done a make_verilator_lib on this)
# @param $6 c filename for cwv to go in output dir [model name .cpp]
# @param $7 object filename to go in output dir [model name .o]
# @param $8 CDL options
# @param $9 verilator build directory
define make_cwv_template

$3/$6 : $2/$4
	@echo "CDL $4 -cwv $6"
	${Q}${CDL_BIN_DIR}/cdl $${CDL_FLAGS} --model cwv__$5 --cwv $$@ $8 $2/$4

.PHONY:all_cwv
all_cwv:$3/$7
# The library we depend on is <model>, not cwv__<model>
$3/$7 : $3/$6 $${VLIB__$5__H} $${VLIB__$5__LIB}
	@echo "CC $6 -o $7"
	${Q}${CXX} ${CDL_INCLUDES} ${CXXFLAGS} -I $9 -I ${VERILATOR_SHARE}/include -I ${VERILATOR_SHARE}/include/vltstd -c -o $$@ $3/$6

MODEL_VERILATOR_LIBS += $${VLIB__$5__LIB}

LIB__$1__C_OBJS  += $3/$7
LIB__$1__MODELS += cwv__$5
LIB__$1__CLEAN_TARGETS += $3/$6 $3/$7

endef

#f make_verilator_lib_template
define make_verilator_lib_template
# @param $1 output directory (for .h file and V<module>.a archive)
# @param $2 verilator build directory
# @param $3 module (top for verilator)
# @param $4 verilog source directory (containing <module>.v)
# @param $5 verilog source directories to include
# @param $6 other verilog source files

VLIB__$3__H    := $1/V$3.h
VLIB__$3__SYMS := $1/V$3__Syms.h
VLIB__$3__LIB  := $1/V$3__ALL.a

.PHONY:verilate_libs
verilate_libs: $${VLIB__$3__H} $${VLIB__$3__LIB}

$${VLIB__$3__H}: $2/V$3.h
	cp $$< $$@

$${VLIB__$3__SYMS}: $2/V$3__Syms.h
	cp $$< $$@

$${VLIB__$3__LIB}: $2/V$3__ALL.a
	cp $$< $$@

$2/V$3.h: $2/V$3__ALL.a

$2/V$3__Syms.h: $2/V$3__ALL.a

$2/V$3.cpp: ${BUILD_STAMPS}/verilog
	@echo "verilate $3 $$< $$@"
	${Q}${VERILATOR} -CFLAGS "${VERILATOR_C_FLAGS}" --cc --top-module $3 --threads 1 -Mdir $2 -Wno-fatal $4/$3.v $6 $(foreach s,$5,+incdir+${s})

$2/V$3__ALL.a: $2/V$3.cpp
	@echo "cpp for verilate $3"
	(cd $2 && make CFLAGS="${VERILATOR_C_FLAGS}" VERILATOR_ROOT=${VERILATOR_SHARE} -f V$3.mk )

LIB__$1__CLEAN_TARGETS += $2/V$3__ALL.a $2/V$3.h $2/V$3__Syms.h $${VLIB__$3__H} $${VLIB__$3__SYMS} $${VLIB__$3__LIB}

endef
