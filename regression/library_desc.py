import cdl_desc
from cdl_desc import CdlModule, CModel, CSrc, CdlSimVerilatedModule, Verilog
from typing import Dict, List

class Library(cdl_desc.Library):
    name="cdl_regression"
    pass

class CModels(cdl_desc.Modules):
    name = "cmodels"
    modules = []
    modules += [ CModel("c_log_toggle", src_dir="tests/log") ]
    modules += [ CSrc("csrc_test", src_dir="tests/log") ]

class Executable(cdl_desc.Executable):
    name     = "exec_me"
    src_dir  = "tests/csrc"
    cpp_include_dirs = ["tests/csrc", "tests/log"]
    srcs = []
    srcs += [ CSrc("exec_me") ]
    pass

class SimpleModules(cdl_desc.Modules):
    name = "simple"
    src_dir = "tests/simple"
    modules = []
    modules += [ CdlModule("tie_high") ]
    modules += [ CdlModule("tie_both") ]
    modules += [ CdlModule("toggle") ]
    modules += [ CdlModule("invert") ]
    modules += [ CdlModule("and") ]
    modules += [ CdlModule("invert_chain") ]
    modules += [ CdlModule("constants") ]
    modules += [ CdlModule("mux") ]
    modules += [ CdlModule("alu") ]
    modules += [ CdlModule("mux_array") ]
    pass

class LogModules(cdl_desc.Modules):
    name = "log"
    src_dir = "tests/log"
    modules = []
    modules += [ CdlModule("lfsr_log_tracker") ]
    pass

class VerilogModules(cdl_desc.Modules):
    modules : List[cdl_desc.Module]
    name = "verilog"
    src_dir = "tests/verilog"
    modules  = []
    modules += [ Verilog("srw_rams") ]
    modules += [ CModel("rams") ]
    modules += [ CdlModule("ram_burst") ]
    modules += [ Verilog("ram_burst_v") ]
    modules += [ CdlSimVerilatedModule("ram_burst_v",
                                       cdl_filename="ram_burst",
                                       registered_name="ram_burst",
                                       extra_verilog=["srw_rams.v"])]

class VectorModules(cdl_desc.Modules):
    name = "vector"
    src_dir = "tests/vector"
    modules = []
    modules += [ CdlModule("vector_toggle__width_16", constants={"width":16}, cdl_filename="vector_toggle") ]
    modules += [ CdlModule("vector_toggle__width_18", constants={"width":18}, cdl_filename="vector_toggle") ]
    modules += [ CdlModule("vector_toggle_complex__width_18",    constants={"width":18},  cdl_filename="vector_toggle_complex") ] #
    # , rmr:vector_toggle_complex=vector_toggle__width_18 rim:vector_toggle_complex=complex_cdl_model") ]
    modules += [ CdlModule("vector_add__width_4", constants={"width":4}, cdl_filename="vector_add") ]
    modules += [ CdlModule("vector_add__width_8", constants={"width":8}, cdl_filename="vector_add") ]
    modules += [ CdlModule("vector_mult_by_11__width_8", constants={"width":8}, cdl_filename="vector_mult_by_11") ]
    modules += [ CdlModule("vector_reverse__width_8", constants={"width":8}, cdl_filename="vector_reverse") ]
    modules += [ CdlModule("vector_nest__width_8", constants={"width":8}, cdl_filename="vector_nest") ]
    modules += [ CdlModule("vector_sum__width_4", constants={"width":4}, cdl_filename="vector_sum") ]
    modules += [ CdlModule("vector_sum__width_8", constants={"width":8}, cdl_filename="vector_sum") ]
    modules += [ CdlModule("vector_sum__width_64", constants={"width":64}, cdl_filename="vector_sum") ]
    modules += [ CdlModule("vector_op_1") ]
    modules += [ CdlModule("vector_op_2") ]
    modules += [ CdlModule("vector_sum_2__width_4", constants={"width":4}, cdl_filename="vector_sum_2") ]

    modules += [ CdlSimVerilatedModule("vector_sum_2__width_4_v",
                                       verilog_filename="vector_sum_2__width_4",
                                       cdl_filename="vector_sum_2",
                                       constants={"width":4},
    ) ]
    pass

class StructModules(cdl_desc.Modules):
    name = "struct"
    src_dir = "tests/struct"
    modules = []
    modules += [ CdlModule("generic_fifo_word",      cdl_filename="generic_fifo", types={"gt_fifo_content":"t_fifo_content_word"}) ] # force_includes=["dprintf.h"]
    modules += [ CdlModule("generic_fifo_struct",    cdl_filename="generic_fifo", types={"gt_fifo_content":"t_fifo_content_struct"}) ] # force_includes=["dprintf.h"]
    modules += [ CdlModule("generic_fifo_hierarchy", cdl_filename="generic_fifo", types={"gt_fifo_content":"t_fifo_content_hierarchy"}) ] # force_includes=["dprintf.h"]
    #cdl struct generic_fifo rmn:generic_fifo=generic_fifo_deep_struct  rmt:gt_fifo_content=t_fifo_content_deep_struct  model:generic_fifo_deep_struct

class ClockGateModules(cdl_desc.Modules):
    name = "struct"
    src_dir = "tests/clock_gate"
    modules = []
    modules += [ CdlModule("gc_simple") ]

    """



modules += [ CdlModule("copy_bits vabi:copy_bits_body_feedthrus vapi:copy_bits_port_feedthrus") ]
#cdl struct nested_structures  rmt:t_cline=t_cline_lg rmt:t_color=t_color_lg
modules += [ CdlModule("nested_structures  rmt:t_cline=t_cline_lg rmt:t_color_lg=t_color") ]
#cdl struct nested_structures_2 This does not work as arrays of structures are not correctly indexed yet
modules += [ CdlModule("nested_structures_3 inc:struct finc:point.h finc:color.h") ]
modules += [ CdlModule("nested_structures_4") ]

modules += [ CdlModule("enum_cycle") ]

modules += [ CdlModule("fsm_cycle") ]
modules += [ CdlModule("fsm_machine") ]

modules += [ CdlModule("hierarchy_reg") ]
modules += [ CdlModule("hierarchy_reg2") ]
modules += [ CdlModule("hierarchy_and         rim:hierarchy_and=simple") ]
modules += [ CdlModule("hierarchy_gated_clock") ]
cdl_options mul:on
cdl instantiation hierarchy_comb_and_clocked
cdl_options mul:off
modules += [ CdlModule("hierarchy_comb_and_clocked2") ]
modules += [ CdlModule("hierarchy_complex") ]
modules += [ CdlModule("hierarchy                     inc:instantiation") ]
modules += [ CdlModule("hierarchy_test_harness        inc:instantiation") ]
modules += [ CdlModule("hierarchy_struct              inc:instantiation") ]
modules += [ CdlModule("hierarchy_struct_test_harness inc:instantiation") ]
modules += [ CdlModule("failure_0") ]

#cdl bugs missing_reset
#cdl bugs output_cyclic_dependency
#cdl bugs empty_case_statements
#cdl bugs sm_test inc:bugs
#cdl bugs sm_sub inc:bugs
#cdl bugs check_64bits
#cdl bugs bundle_width
#cdl bugs operator_precedence
#cdl bugs single_entry_arrays
cdl bugs case_expression_lists
cdl bugs for_case
cdl bugs partial_ports

# uncomment the following to check errors do not cause bus errors
#cdl bugs type_errors
#cdl bugs constant_errors
#cdl bugs prototype_errors
#cdl bugs module_errors

modules += [ CdlModule("reg") ]
modules += [ CdlModule("adder") ]
modules += [ CdlModule("clocked_adder") ]


"""
