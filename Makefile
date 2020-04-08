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
# include Makefile_build_config MUST come first as it uses MAKEFILE_LIST
include Makefile_build_config
include ${CDL_SCRIPTS_DIR}/makefile_hdr

#a Targets
.PHONY: ALL reconfigure clean build include install
ALL: build

reconfigure: configure.ac
	autoreconf

Makefile_build_config: Makefile_build_config.in	./configure
	./configure --prefix=${CDL_BUILD_ROOT}

clean:
	rm -rf ${CDL_BUILD_INCLUDE_DIR}/*
	rm -rf ${CDL_BUILD_LIB_DIR}/*
	rm -f ${CDL_BUILD_OBJ_DIR}/*
	rm -f ${CDL_BUILD_BIN_DIR}/*
	rm -f ${CDL_BUILD_STAMPS_DIR}/*
	mkdir -p ${CDL_BUILD_ROOT} ${CDL_BUILD_OBJ_DIR} ${CDL_BUILD_BIN_DIR} ${CDL_BUILD_LIB_DIR} ${CDL_BUILD_INCLUDE_DIR} ${CDL_BUILD_STAMPS_DIR}
	cd ${CDL_SRC_ROOT}/support_libraries   && ${SUBMAKE} clean
	cd ${CDL_SRC_ROOT}/simulation_engine   && ${SUBMAKE} clean
	cd ${CDL_SRC_ROOT}/execution_harnesses && ${SUBMAKE} clean
	cd ${CDL_SRC_ROOT}/backend             && ${SUBMAKE} clean
	cd ${CDL_SRC_ROOT}/cdl_frontend        && ${SUBMAKE} clean

$(eval $(call new_stamp,test_clean))
${MK_test_clean}:
	${MAKE} clean
	date > $@

$(eval $(call new_stamp,include))
${MK_include}: ${MK_test_clean}
	cd ${CDL_SRC_ROOT}/support_libraries   && ${SUBMAKE} include
	cd ${CDL_SRC_ROOT}/backend             && ${SUBMAKE} include
	cd ${CDL_SRC_ROOT}/simulation_engine   && ${SUBMAKE} include
	date > $@

$(eval $(call new_stamp,build))
${MK_build}: ${MK_include}
	cd ${CDL_SRC_ROOT}/support_libraries   && ${SUBMAKE} build
	cd ${CDL_SRC_ROOT}/backend             && ${SUBMAKE} build
	cd ${CDL_SRC_ROOT}/cdl_frontend        && ${SUBMAKE} build
	cd ${CDL_SRC_ROOT}/simulation_engine   && ${SUBMAKE} build
	cd ${CDL_SRC_ROOT}/execution_harnesses && ${SUBMAKE} build
	date > $@

install: ${MK_build}
	cd ${CDL_SRC_ROOT}/scripts             && ${SUBMAKE} install
	cd ${CDL_SRC_ROOT}/support_libraries   && ${SUBMAKE} install
	cd ${CDL_SRC_ROOT}/simulation_engine   && ${SUBMAKE} install
	cd ${CDL_SRC_ROOT}/execution_harnesses && ${SUBMAKE} install
	cd ${CDL_SRC_ROOT}/backend             && ${SUBMAKE} install
	cd ${CDL_SRC_ROOT}/cdl_frontend        && ${SUBMAKE} install
	cd ${CDL_SRC_ROOT}/pycdl               && ${SUBMAKE} install
