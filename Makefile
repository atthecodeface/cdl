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

