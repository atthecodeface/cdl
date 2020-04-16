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

#a Templates
#v Notes
#
# MODELS contains a list of model names for this library that are to be 'init'ed
# C_MODEL_OBJS contains a list of object files to be included in the static library

#f cdl_makefile_template
define cdl_makefile_template
# @param $1 required source directory - where library_desc.py exists
# @param $2 build directory - where to put Makefile
# @param $3 other source directories - where libraries may exist
.PHONY:makefiles

makefiles: $2/Makefile

BUILD_MAKEFILE = $2/Makefile

$2/Makefile:
	${CDL_LIBEXEC_DIR}/cdl_desc.py --require $1 --build_root $2 $3

clean: clean_makefile

clean_makefile:
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

LIB__$1__C_MODEL_OBJS  += $3/$6
$3/$6 : $2/$4
	@echo "CC $4 -o $6" 
	$(Q)$(CXX) $(CXXFLAGS) ${CDL_INCLUDES} -c -o $$@ $2/$4 $7

ifneq ($5,)
    LIB__$1__MODELS += $5
endif

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
.PHONY: $5
$5: $3/$6 $3/$7 $3/$8  $3/$5.cdlh  $3/$5.xml

ifneq (${6},)

$3/$6 : $2/$4
	@echo "CDL $4 -cpp $6" 
	${Q}${CDL_BIN_DIR}/cdl $${CDL_FLAGS} --model $5 --dependencies-target $$@ --dependencies $3/$6.dep --dependencies-relative $(dir $2/$4) --cpp $$@  $9 $2/$4

-include $3/$6.dep

LIB__$1__C_MODEL_OBJS  += $3/$7
$3/$7 : $3/$6
	@echo "CC $6 -o $7" 
	${Q}${CXX} ${CDL_INCLUDES} ${CXXFLAGS} -c -o $$@ $3/$6

endif

$3/$8 : $2/$4
	@echo "CDL $4 -v $8" 
	${Q}${CDL_BIN_DIR}/cdl $${CDL_FLAGS} --model $5 --verilog $$@ $9 $2/$4

$3/$5.cdlh : $2/$4
	@echo "CDL $4 -cdlh $5" 
	${Q}${CDL_BIN_DIR}/cdl $${CDL_FLAGS} --model $5 --cdlh $$@ $9 $2/$4

$3/$5.xml : $2/$4
	@echo "CDL $4 -xml $5" 
	${Q}${CDL_BIN_DIR}/cdl $${CDL_FLAGS} --model $5 --xml $$@ $9 $2/$4

LIB__$1__MODELS += $5

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

LIB__$1__C_MODEL_OBJS  += $2/$3.o
$2/$3.o: $2/$3.cpp
	@echo "Compile library init module $$@"
	${Q}${CXX} ${CXXFLAGS} -c -o $$@ $$<

endef

#f cdl_library_template
define cdl_library_template
# @param $1 library name
# @param $2 output directory
library: $2/lib_$1.a

lib_$1: $2/lib_$1.a

$2/lib_$1.a: $${LIB__$1__C_MODEL_OBJS}
	@echo "Link static $$@"
	${Q}${LINK_STATIC} $$@ $${LIB__$1__C_MODEL_OBJS}

endef

#f sim_add_cdl_library
define sim_add_cdl_library
# @param $1 build directory where library is built
# @param $2 library name
MODEL_LIBS += $1/lib_$2.a

endef

#f sim_init_object_file
#
# The file created here links with lib<name>.a and other libraries and an execution harness in libcdl_*.a
#
define sim_init_object_file
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

#f command_line_sim
define command_line_sim
# @param $1 output filename
# @param $2 output directory
# @param $3 init object files
.PHONY: sim
sim: $1

$1: ${MODEL_LIBS} $3
	@echo "Building command line simulation ${CMDLINE_PROG}"
	${Q}${CXX} -o $1 $3 ${MODEL_LIBS} -L${CDL_ROOT}/lib -lcdl_se_batch ${LDFLAGS}

endef
