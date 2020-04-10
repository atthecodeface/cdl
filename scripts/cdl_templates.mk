#a Templates
#f cmodel_template
define cmodel_template
# @param $1 c filename
# @param $2 object filename
# @param $3 model name
# @param $4 options

${TARGET_DIR}/$2 : ${SRC_ROOT}/$1
	@echo "CC $1 -o $2" 
	$(Q)$(CXX) $(CXXFLAGS) -c -o ${TARGET_DIR}/$2 ${SRC_ROOT}/$1 $4

MODELS += $3
C_MODEL_SRCS += ${SRC_ROOT}/$1
C_MODEL_OBJS += ${TARGET_DIR}/$2

endef

#f csrc_template
define csrc_template
# @param $1 c filename
# @param $2 object filename
# @param $3 options
${TARGET_DIR}/$2 : ${SRC_ROOT}/$1
	@echo "CC $1 -o -$2" 
	$(Q)$(CXX) $(CXXFLAGS) -c -o ${TARGET_DIR}/$2 ${SRC_ROOT}/$1 $3
C_MODEL_SRCS += ${SRC_ROOT}/$1
C_MODEL_OBJS += ${TARGET_DIR}/$2

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
# @param $1 cdl filename inside src_root
# @param $2 c filename in output dir
# @param $3 model name
# @param $4 object filename
# @param $5 verilog filename
# @param $6 options
${TARGET_DIR}/$2 : ${SRC_ROOT}/$1 $(CREATE_MAKE) $(CYCLICITY_BIN_DIR)/cdl
	@echo "CDL $1 -cpp $2" 
	$(Q)$(CYCLICITY_BIN_DIR)/cdl $(CDL_FLAGS) --model $3 --cpp ${TARGET_DIR}/$2 --cdlh ${TARGET_DIR}/${2:.cpp=.cdlh} $6 ${SRC_ROOT}/$1

${TARGET_DIR}/$4 : ${TARGET_DIR}/$2
	@echo "CC $2 -o $4" 
	$(Q)$(CXX) $(CXXFLAGS) -c -o ${TARGET_DIR}/$4 ${TARGET_DIR}/$2

${TARGET_DIR}/$5 : ${SRC_ROOT}/$1 $(CREATE_MAKE) $(CYCLICITY_BIN_DIR)/cdl
	@echo "CDL $5 -v $1" 
	$(Q)$(CYCLICITY_BIN_DIR)/cdl $(CDL_FLAGS) --model $3 --verilog ${TARGET_DIR}/$5 $6 ${SRC_ROOT}/$1

${TARGET_DIR}/$3.cdlh : ${SRC_ROOT}/$1 $(CREATE_MAKE) $(CYCLICITY_BIN_DIR)/cdl
	@echo "CDL $3 -cdlh $1" 
	$(Q)$(CYCLICITY_BIN_DIR)/cdl $(CDL_FLAGS) --model $3 --cdlh ${TARGET_DIR}/$3.cdlh $6 ${SRC_ROOT}/$1

${TARGET_DIR}/$3.xml : ${SRC_ROOT}/$1 $(CREATE_MAKE) $(CYCLICITY_BIN_DIR)/cdl
	@echo "CDL $3 -xml $1" 
	$(Q)$(CYCLICITY_BIN_DIR)/cdl $(CDL_FLAGS) --model $3 --xml ${TARGET_DIR}/$3.xml $6 ${SRC_ROOT}/$1

MODELS += $3
VERILOG_FILES += ${TARGET_DIR}/$5
C_MODEL_OBJS += ${TARGET_DIR}/$4
CDLH_FILES += ${TARGET_DIR}/$3.cdlh
XML_FILES += ${TARGET_DIR}/$3.xml

endef
#f cdl_no_cpp_template
define cdl_no_cpp_template
# @param $1 cdl filename inside src_root
# @param $2 None
# @param $3 model name
# @param $4 None
# @param $5 verilog filename
# @param $6 options
${TARGET_DIR}/$5 : ${SRC_ROOT}/$1 $(CREATE_MAKE) $(CYCLICITY_BIN_DIR)/cdl
	@echo "CDL $5 -v $1" 
	$(Q)$(CYCLICITY_BIN_DIR)/cdl $(CDL_FLAGS) --model $3 --verilog ${TARGET_DIR}/$5 $6 ${SRC_ROOT}/$1

${TARGET_DIR}/$3.cdlh : ${SRC_ROOT}/$1 $(CREATE_MAKE) $(CYCLICITY_BIN_DIR)/cdl
	@echo "CDL $3 -cdlh $1" 
	$(Q)$(CYCLICITY_BIN_DIR)/cdl $(CDL_FLAGS) --model $3 --cdlh ${TARGET_DIR}/$3.cdlh $6 ${SRC_ROOT}/$1

${TARGET_DIR}/$3.xml : ${SRC_ROOT}/$1 $(CREATE_MAKE) $(CYCLICITY_BIN_DIR)/cdl
	@echo "CDL $3 -xml $1" 
	$(Q)$(CYCLICITY_BIN_DIR)/cdl $(CDL_FLAGS) --model $3 --xml ${TARGET_DIR}/$3.xml $6 ${SRC_ROOT}/$1

MODELS += $3
VERILOG_FILES += ${TARGET_DIR}/$5
XML_FILES += ${TARGET_DIR}/$3.xml

endef

