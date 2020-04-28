/*a Copyright
  
  This file 'md_target_c.h' copyright Gavin J Stark 2003, 2004
  
  This program is free software; you can redistribute it and/or modify it under
  the terms of the GNU General Public License as published by the Free Software
  Foundation, version 2.0.
  
  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even implied warranty of MERCHANTABILITY
  or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
  for more details.
*/

/*a Wrapper
 */
#ifdef __INC_MD_TARGET_C
#else
#define __INC_MD_TARGET_C

/*a Includes
 */
#include "c_md_target.h"
#include "c_model_descriptor.h"

/*a Subclass of c_md_target for C++ */
/*c Class c_md_target_c */
class c_md_target_c: public c_md_target {
    void output_type(t_md_type_instance *instance, int indent, int indirect );
    void output_clocked_storage_types(void);
    void output_input_types(void);
    void output_output_types(void); // for cdl-wrapped verilator only
    void output_combinatorial_types(void);
    void output_net_types(void);
    void output_instance_types(t_md_module_instance *module_instance);
    void output_all_signals_type(void); // t_*_all_signals
    void output_simulation_methods_display_message_to_buffer(t_md_statement *statement, int indent, t_md_message *message, const char *buffer_name );
    void output_simulation_methods_lvar(t_md_lvar *lvar, int main_indent, int sub_indent, int in_expression );
    void output_simulation_methods_expression(t_md_expression *expr, int main_indent, int sub_indent );
    void output_simulation_methods_statement_if_else(t_md_statement *statement);
    void output_simulation_methods_statement_parallel_switch(t_md_statement *statement);
    void output_simulation_methods_assignment(t_md_lvar *lvar, int clocked, int wired_or, t_md_expression *expr );
    void output_simulation_methods_statement_print_assert_cover(t_md_statement *statement);
    void output_simulation_methods_statement_log(t_md_statement *statement);
    void output_simulation_methods_statement(t_md_statement *statement);
    void output_simulation_methods_statement_list(t_md_statement *statement, int subindent );
    void output_simulation_methods_code_block_statements(t_md_code_block *code_block, int indent );
    void output_simulation_methods_code_block(t_md_code_block *code_block, t_md_signal *clock, int edge, t_md_type_instance *instance );
    void output_simulation_code_to_make_combinatorial_signals_valid(void);
    void output_simulation_methods_port_net_assignment(int indent, t_md_module_instance *module_instance, t_md_lvar *lvar, t_md_type_instance *port_instance );
    t_md_code_block *code_block; // for output of statements, code_block that we are in (NULL for net assignment)
    t_md_signal *clock; // for output of statements, clock that output is for (NULL for combinatorial)
    int edge; // for output of statements, clock edge that output is for (ignored if clock==NULL)
    t_md_type_instance *instance; // for output of statements, the variable as to why for combinatorial (NULL for clocked)
    int indent; // for output of statements, current indent

    t_md_module *module;
    std::list<std::string> all_signals_list;
    std::list<std::string> module_registrations;
    const char *module_verilated_name;
    void output_header(void);
    void cwv_output_header(void);
    void output_defines(void);
    void output_types(void);
    void cwv_output_types(void);
    void output_static_variables(void);
    void cwv_output_static_variables(void);
    void output_constructors_destructors(void);
    void output_simulation_methods(void);
    void output_static_functions(void);
    void cwv_output_static_functions(void);
    void output_initalization_functions(void);
public:
    c_md_target_c(class c_model_descriptor *model, t_md_output_fn output_fn, void *output_handle):
        c_md_target(model, output_fn, output_handle)
        {
        }
    void output_cpp_model(void);
    void output_cwv_model(void);
};

/*a Wrapper
 */
#endif

