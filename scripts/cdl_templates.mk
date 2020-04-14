#a Variables if not defined yet
CDL_SCRIPTS_DIR ?= ${CDL_ROOT}/lib/cdl
CDL_BIN_DIR     ?= ${CDL_ROOT}/bin
CDL_LIBEXEC_DIR ?= ${CDL_ROOT}/libexec/cdl
CDL_INCLUDES    ?= -I${CDL_ROOT}/include/cdl
Q?=@
LINK_STATIC?=libtool -static -o

# PYTHONLINKLIB          := ${CXX} -bundle -o
# CYCLICITY_PYTHON_LIBS  := -L${CDL_ROOT}/lib -lcdl_se_python -L/Users/gavinprivate/Git/brew/opt/python/Frameworks/Python.framework/Versions/3.7/lib/python3.7/config-3.7m-darwin -lpython3.7m -ldl -framework CoreFoundation -lc++ -lc 
# CFLAGS   += -I${CDL_INCLUDE_DIR}
# CXXFLAGS += -I${CDL_INCLUDE_DIR}

MODEL_LIBS=
MODELS=
C_MODEL_SRCS=
C_MODEL_OBJS=
VERILOG_FILES=
CDLH_FILES=

#a Templates
#v Notes
#
# MODELS contains a list of model names for this library that are to be 'init'ed
# C_MODEL_OBJS contains a list of object files to be included in the static library

#f library_makefile_template
define library_makefile_template
# @param $1 library name - for targets
# @param $2 library root directory - where library_desc.py exists
# @param $3 build directory - where to put Makefile
$3/Makefile: $2/library_desc.py
	PYTHONPATH=$2:${PYTHONPATH} ${CDL_LIBEXEC_DIR}/cdl_desc.py > $$@

clean: clean_library_makefile_$1

clean_library_makefile_$1:
	rm -f $3/Makefile
endef

#f cpp_template
define cpp_template
# @param $1 cpp source directory
# @param $2 output directory
# @param $3 cpp filename within cpp source directory
# @param $4 model name ("" if not a model)
# @param $5 object filename to go in output dir [model name .o]
# @param $6 C flags

$2/$5 : $1/$3
	@echo "CC $1 -o $3" 
	$(Q)$(CXX) $(CXXFLAGS) ${CDL_INCLUDES} -c -o $$@ $1/$3 $6

ifneq ($4,)
  MODELS += $4
endif

C_MODEL_SRCS += $1/$3
C_MODEL_OBJS += $2/$5

endef

#f ef_template
define ef_template
# @param $1 ef filename inside src_root
# @param $2 c filename in output dir
# @param $3 model name
# @param $4 object filename
# @param $5 options
${TARGET_DIR}/$2 : ${SRC_ROOT}/$1 $(CYCLICITY_BIN_DIR)/ef
	@echo "EF $1 -cpp -$2" 
	$(Q)$(CYCLICITY_BIN_DIR)/ef --model $3 --cpp ${TARGET_DIR}/$2 $5 ${SRC_ROOT}/$1

${TARGET_DIR}/$4 : ${TARGET_DIR}/$2
	@echo "CC $1 -o -$2" 
	$(Q)$(CXX) $(CXXFLAGS) -c -o ${TARGET_DIR}/$4 ${TARGET_DIR}/$2

MODELS += $3
C_MODEL_OBJS += ${TARGET_DIR}/$4

endef

#f cdl_template
define cdl_template
# @param $1 cdl source directory
# @param $2 output directory
# @param $3 cdl filename within cdl source directory
# @param $4 model name
# @param $5 c filename to go in output dir [model name .cpp]
# @param $6 object filename to go in output dir [model name .o]
# @param $7 verilog filename to go in output dir [model name .v]
# @param $8 CDL options
.PHONY: $4
$4: $2/$5 $2/$6 $2/$7  $2/$4.cdlh  $2/$4.xml

ifneq (${6},)

$2/$5 : $1/$3
	@echo "CDL $3 -cpp $5" 
	${Q}${CDL_BIN_DIR}/cdl ${CDL_FLAGS} --model $4 --dependencies-target $$@ --dependencies $2/$5.dep --dependencies-relative $(dir $1/$3) --cpp $$@  $8 $1/$3

-include $2/$5.dep

C_MODEL_OBJS  += ${2}/$6
$2/$6 : $2/$5
	@echo "CC $5 -o $6" 
	${Q}${CXX} ${CDL_INCLUDES} ${CXXFLAGS} -c -o $$@ $2/$5

endif

$2/$7 : $1/$3
	@echo "CDL $3 -v $7" 
	${Q}${CDL_BIN_DIR}/cdl ${CDL_FLAGS} --model $4 --verilog $$@ $8 $1/$3

$2/$4.cdlh : $1/$3
	@echo "CDL $3 -cdlh $4" 
	${Q}${CDL_BIN_DIR}/cdl ${CDL_FLAGS} --model $4 --cdlh $$@ $8 $1/$3

$2/$4.xml : $1/$3
	@echo "CDL $3 -xml $4" 
	${Q}${CDL_BIN_DIR}/cdl ${CDL_FLAGS} --model $4 --xml $$@ $8 $1/$3

MODELS += $4
VERILOG_FILES += ${2}/$7
CDLH_FILES    += ${2}/$3.cdlh
XML_FILES     += ${2}/$3.xml

endef

#f library_init_object_file
define library_init_object_file
# @param $1 output directory
# @param $2 output filename in output directory
# @param $3 library name

$1/$2.cpp: ${LIB_MAKEFILE}
	@echo "Creating library_init_object_file source"
	${Q}echo "// Library $3 initialization source created by cdl" > $$@
	${Q}for a in $${MODELS} ; do echo "extern void $$$${a}__init( void );" >> $$@ ; done
	${Q}echo "extern void lib_$3_init(void) {" >> $$@
	${Q}for a in $${MODELS} ; do echo "$$$${a}__init();" >> $$@ ; done
	${Q}echo "};" >> $$@

C_MODEL_OBJS  += $1/$2.o
$1/$2.o: $1/$2.cpp
	${Q}${CXX} ${CXXFLAGS} -c -o $$@ $$<

endef

#f init_object_file
define init_object_file
# @param $1 output directory
# @param $2 output filename in output directory
# @param $3 library name

$1/$2.cpp: ${LIB_MAKEFILE}
	@echo "Creating init_object_file source"
	${Q}echo "// Object initialization source for library $3 created by cdl" > $$@
	${Q}echo '#include <stdlib.h>' >> $$@
	${Q}echo 'extern "C" void *PyInit_py_engine(void); extern void unused(void) {(void)PyInit_py_engine();}' >> $$@
	${Q}echo "typedef void (*t_init_fn)(void);" >> $$@
	${Q}echo "extern void lib_$3_init(void);" >> $$@
	${Q}echo "t_init_fn model_init_fns[] = {lib_$3_init, NULL};" >> $$@

C_MODEL_OBJS  += $1/$2.o
$1/$2.o: $1/$2.cpp
	${Q}${CXX} ${CXXFLAGS} -c -o $$@ $$<

endef

#f cdl_library_template
define cdl_library_template
# @param $1 output directory
# @param $2 library name
library: $1/lib_$2.a

$1/lib_$2.a: ${C_MODEL_OBJS}
	@echo "Link static $$@"
	${Q}${LINK_STATIC} $$@ ${C_MODEL_OBJS}

endef

#f command_line_sim
define command_line_sim
# @param $1 output filename
# @param $2 output directory
# @param $3 libraries
.PHONY: $4

ALL: $1

$1: $2/lib_$3.a
	@echo "Building command line simulation ${CMDLINE_PROG}"
	${Q}${CXX} -o $1 $2/lib_$3.a ${MODEL_LIBS} -L${CDL_ROOT}/lib -lcdl_se_batch

endef
