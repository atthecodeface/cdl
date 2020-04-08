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
	./configure

clean:
	rm -rf ${CDL_BUILD_INCLUDE_DIR}/*
	rm -rf ${CDL_BUILD_LIB_DIR}/*
	rm -f ${CDL_BUILD_OBJ_DIR}/*
	rm -f ${CDL_BUILD_BIN_DIR}/*
	mkdir -p ${CDL_BUILD_ROOT} ${CDL_BUILD_OBJ_DIR} ${CDL_BUILD_BIN_DIR} ${CDL_BUILD_LIB_DIR} ${CDL_BUILD_INCLUDE_DIR} ${CDL_BUILD_STAMPS_DIR}
	cd ${CDL_ROOT}/support_libraries   && ${MAKE} CDL_ROOT=${CDL_ROOT} clean
	cd ${CDL_ROOT}/simulation_engine   && ${MAKE} CDL_ROOT=${CDL_ROOT} clean
	cd ${CDL_ROOT}/execution_harnesses && ${MAKE} CDL_ROOT=${CDL_ROOT} clean
	cd ${CDL_ROOT}/backend             && ${MAKE} CDL_ROOT=${CDL_ROOT} clean
	cd ${CDL_ROOT}/cdl_frontend        && ${MAKE} CDL_ROOT=${CDL_ROOT} clean

$(eval $(call new_stamp,test_clean))
${MK_test_clean}:
	${MAKE} clean
	touch $@

$(eval $(call new_stamp,include))
${MK_include}: ${MK_test_clean}
	cd ${CDL_ROOT}/support_libraries   && ${MAKE} CDL_ROOT=${CDL_ROOT} include
	cd ${CDL_ROOT}/backend             && ${MAKE} CDL_ROOT=${CDL_ROOT} include
	cd ${CDL_ROOT}/simulation_engine   && ${MAKE} CDL_ROOT=${CDL_ROOT} include
	touch $@

$(eval $(call new_stamp,build))
${MK_build}: ${MK_include}
	cd ${CDL_ROOT}/support_libraries   && ${MAKE} CDL_ROOT=${CDL_ROOT} build
	cd ${CDL_ROOT}/backend             && ${MAKE} CDL_ROOT=${CDL_ROOT} build
	cd ${CDL_ROOT}/cdl_frontend        && ${MAKE} CDL_ROOT=${CDL_ROOT} build
	cd ${CDL_ROOT}/simulation_engine   && ${MAKE} CDL_ROOT=${CDL_ROOT} build
	cd ${CDL_ROOT}/execution_harnesses && ${MAKE} CDL_ROOT=${CDL_ROOT} build
	touch $@

install: ${MK_build}
	cd ${CDL_ROOT}/scripts             && ${MAKE} CDL_ROOT=${CDL_ROOT} install
	cd ${CDL_ROOT}/support_libraries   && ${MAKE} CDL_ROOT=${CDL_ROOT} install
	cd ${CDL_ROOT}/simulation_engine   && ${MAKE} CDL_ROOT=${CDL_ROOT} install
	cd ${CDL_ROOT}/execution_harnesses && ${MAKE} CDL_ROOT=${CDL_ROOT} install
	cd ${CDL_ROOT}/backend             && ${MAKE} CDL_ROOT=${CDL_ROOT} install
	cd ${CDL_ROOT}/cdl_frontend        && ${MAKE} CDL_ROOT=${CDL_ROOT} install
	cd ${CDL_ROOT}/pycdl               && ${MAKE} CDL_ROOT=${CDL_ROOT} install

#	cp -r ${CDL_ROOT}/pycdl ${BUILD_LIB_DIR}/cdl/python/
