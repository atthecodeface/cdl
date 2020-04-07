#a Copyright
#  
#  This file 'Makefile' copyright Gavin J Stark 2020
#  
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# @file  Makefile
# @brief Basic makefile for building CDL
#

#a Global variables
include Makefile_build_config

PREREQS = BSE
include ${CDL_SCRIPTS_DIR}/makefile_hdr

#a Targets
.PHONY: ALL clean build rebuild include
ALL: clean include build

rebuild: include build

clean:
	rm -f ${CDL_INCLUDE_DIR}/*.h
	mkdir -p ${CDL_BUILD_ROOT} ${CDL_BUILD_OBJ_DIR} ${CDL_BIN_DIR} ${CDL_LIB_DIR} ${CDL_INCLUDE_DIR}
	cd ${CDL_ROOT}/support_libraries   && ${MAKE} CDL_ROOT=${CDL_ROOT} clean
	cd ${CDL_ROOT}/simulation_engine   && ${MAKE} CDL_ROOT=${CDL_ROOT} clean
	cd ${CDL_ROOT}/execution_harnesses && ${MAKE} CDL_ROOT=${CDL_ROOT} clean
	cd ${CDL_ROOT}/backend             && ${MAKE} CDL_ROOT=${CDL_ROOT} clean
	cd ${CDL_ROOT}/cdl_frontend        && ${MAKE} CDL_ROOT=${CDL_ROOT} clean

build:
	cd ${CDL_ROOT}/support_libraries   && ${MAKE} CDL_ROOT=${CDL_ROOT} build
	cd ${CDL_ROOT}/simulation_engine   && ${MAKE} CDL_ROOT=${CDL_ROOT} build
	cd ${CDL_ROOT}/execution_harnesses && ${MAKE} CDL_ROOT=${CDL_ROOT} build
	cd ${CDL_ROOT}/backend             && ${MAKE} CDL_ROOT=${CDL_ROOT} build
	cd ${CDL_ROOT}/cdl_frontend        && ${MAKE} CDL_ROOT=${CDL_ROOT} build

include:
	cd ${CDL_ROOT}/backend             && ${MAKE} CDL_ROOT=${CDL_ROOT} include
	cd ${CDL_ROOT}/execution_harnesses && ${MAKE} CDL_ROOT=${CDL_ROOT} include
	cd ${CDL_ROOT}/support_libraries   && ${MAKE} CDL_ROOT=${CDL_ROOT} include
	cd ${CDL_ROOT}/simulation_engine   && ${MAKE} CDL_ROOT=${CDL_ROOT} include


BUILD_LIB_DIR = ${CDL_ROOT}/build/lib
BUILD_INCLUDE_DIR = ${CDL_ROOT}/build/include
fudge: build/execution_harnesses/eh_batch_scripting_harness.o  build/lib/se_simulation_engine.o build/lib/sl_support.o build/lib/sl_support_with_python.o
	libtool -static -o ${BUILD_LIB_DIR}/libcdl_batch.a  build/execution_harnesses/eh_batch_scripting_harness.o  build/lib/se_simulation_engine.o build/lib/sl_support.o
	libtool -static -o ${BUILD_LIB_DIR}/libcdl_python.a build/execution_harnesses/eh_python_scripting_harness.o build/lib/se_simulation_engine.o build/lib/sl_support_with_python.o
	mkdir -p ${BUILD_LIB_DIR}/cdl
	mkdir -p ${BUILD_LIB_DIR}/cdl/python
	mkdir -p ${BUILD_INCLUDE_DIR}/cdl
	cp ${CDL_ROOT}/scripts/create_make ${BUILD_LIB_DIR}/cdl
	cp ${CDL_ROOT}/scripts/simulation_build_make ${BUILD_LIB_DIR}/cdl
	cp ${CDL_ROOT}/build/include/*.h ${BUILD_INCLUDE_DIR}/cdl
	cp ${CDL_ROOT}/support_libraries/*.h ${BUILD_INCLUDE_DIR}/cdl
	cp -r ${CDL_ROOT}/pycdl ${BUILD_LIB_DIR}/cdl/python/
#
# 1013  10:07:23 libtool -static -o libcdl.a se_simulation_engine.o sl_support_with_python.o ../obj/be_backend.o
# libtool -static -o libcdl.a ../execution_harnesses/eh_batch_scripting_harness.o se_simulation_engine.o sl_support.o
# 1014  10:08:22 cp libcdl.a ../../../tools/lib
# libtool -static -o libcdl_python.a ../execution_harnesses/eh_python_scripting_harness.o se_simulation_engine.o sl_support_with_python.o
# 11:09:28:1045:657:~/Git/cdl_tools_grip/cdl/build/lib$ cp libcdl_python.a ../../../tools/lib
# 1015  10:08:33 man strip
# 1016  10:08:57 mkdir ../../../tools/lib/cdl
# 1017  10:09:00 cd ..
# 1018  10:09:38 mkdir ../../tools/include/cdl
# 1019  10:09:47 cp include/* ../../tools/include/cdl/
# 1020  10:10:13 ls ../scripts/
# 1021  10:10:23 ls ..
# 1022  10:10:35 less ../config.h
# 1023  10:10:56 ls ../scripts/
# 1024  10:11:17 cp ../scripts/create_make ../../tools/lib/cdl
# 1025  10:11:49 less ../Makefile_build_config
# 1026  10:12:15 cp ../Makefile_build_config ../../tools/lib/cdl
# libtool -static -o libcdl.a se_simulation_engine.o sl_support_with_python.o ../obj/be_backend.o

# libtool -static -o libcdl_batch.a  ../execution_harnesses/eh_batch_scripting_harness.o  se_simulation_engine.o sl_support.o
# libtool -static -o libcdl_python.a ../execution_harnesses/eh_python_scripting_harness.o se_simulation_engine.o sl_support_with_python.o
