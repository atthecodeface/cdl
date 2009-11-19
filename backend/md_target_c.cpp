/*a Copyright
  
  This file 'md_target_c.cpp' copyright Gavin J Stark 2003, 2004, 2007
  
  This program is free software; you can redistribute it and/or modify it under
  the terms of the GNU General Public License as published by the Free Software
  Foundation, version 2.0.
  
  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even implied warranty of MERCHANTABILITY
  or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
  for more details.
*/

/*a Documentation
Added
#ifdef INPUT_STORAGE

The theory is that we should have:

a) a prepreclock function - INPUTS ARE NOT VALID:
this would clear 'inputs copied', 'clocks at this step'

b) preclock function for each clock about to fire- INPUTS ARE VALID:
if (!inputs copied) {capture inputs to input_state; inputs_copied=1;}
set bit for 'clocks at this step'

c) clock function - INPUTS ARE NOT VALID, NON-COMB OUTPUTS MUST BE VALID ON EXIT
Propagate from inputs
Do all internal combs and set inputs to all instances and flops (current preclock functionality)
  calls some submodule comb functions if they are purely combinatorial
set bits for gated clocks derived from 'clocks at this step'
for all clocks with bits set, call prepreclock submodule functions
for all clocks with bits set, call preclock submodule functions
for all clocks with bits set, call clock submodule functions
copy next state to state
generate outputs from state
clear 'clocks at this step'

e) comb function
only for combinatorial functions; input to outputs only.
  calls some submodule comb functions if they are purely combinatorial

f) propagate function for simulation waveform validity
do all internal combs and set inputs to all instances and flops
call propagate submodule functions
do all internal state to outputs
do all inputs to outputs


For sets of functions, we need a new simulation engine function call group for sets of submodule/clock handles:
submodule_clock_set_declare( int n )
submodule_clock_set_entry( int i, void *submodule_handle )
invoke_submodule_clock_set_function( submodule_clock_set, int *bitmask, function call type, int int_arg, void *handle_arg )
 type = prepreclock, preclock, clock, postclock, comb, propagate

These functions can then be split using pthreads by the simulation engine by providing an affinity, splitting, and doing a join

 */

/*a Includes
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "be_errors.h"
#include "cdl_version.h"
#include "c_model_descriptor.h"

/*a Static variables
 */
static const char *edge_name[] = {
     "posedge",
     "negedge",
     "bug in use of edge!!!!!"
};
static const char *level_name[] = {
     "active_low",
     "active_high",
     "bug in use of level!!!!!"
};
static const char *usage_type_comment[] = { // Note this must match md_usage_type
    "/* rtl */",
    "/* assert use only */",
    "/* cover use only */",
};
static const char *bit_mask[] = {
     "0LL", "1LL", "3LL", "7LL",
     "0xfLL", "0x1fLL", "0x3fLL", "0x7fLL",
     "0xffLL", "0x1ffLL", "0x3ffLL", "0x7ffLL",
     "0xfffLL", "0x1fffLL", "0x3fffLL", "0x7fffLL",
     "((1LL<<16)-1)", "((1LL<<17)-1)", "((1LL<<18)-1)", "((1LL<<19)-1)", 
     "((1LL<<20)-1)", "((1LL<<21)-1)", "((1LL<<22)-1)", "((1LL<<23)-1)", 
     "((1LL<<24)-1)", "((1LL<<25)-1)", "((1LL<<26)-1)", "((1LL<<27)-1)", 
     "((1LL<<28)-1)", "((1LL<<29)-1)", "((1LL<<30)-1)", "((1LL<<31)-1)", 
     "((1LL<<32)-1)", "((1LL<<33)-1)", "((1LL<<34)-1)", "((1LL<<35)-1)", 
     "((1LL<<36)-1)", "((1LL<<37)-1)", "((1LL<<38)-1)", "((1LL<<39)-1)", 
     "((1LL<<40)-1)", "((1LL<<41)-1)", "((1LL<<42)-1)", "((1LL<<43)-1)", 
     "((1LL<<44)-1)", "((1LL<<45)-1)", "((1LL<<46)-1)", "((1LL<<47)-1)", 
     "((1LL<<48)-1)", "((1LL<<49)-1)", "((1LL<<50)-1)", "((1LL<<51)-1)", 
     "((1LL<<52)-1)", "((1LL<<53)-1)", "((1LL<<54)-1)", "((1LL<<55)-1)", 
     "((1LL<<56)-1)", "((1LL<<57)-1)", "((1LL<<58)-1)", "((1LL<<59)-1)", 
     "((1LL<<60)-1)", "((1LL<<61)-1)", "((1LL<<62)-1)", "((1LL<<63)-1)", 
     "(-1LL)"
};
static char type_buffer[64];

/*a Forward function declarations
 */
static void output_simulation_methods_statement( c_model_descriptor *model, t_md_output_fn output, void *handle, t_md_code_block *code_block, t_md_statement *statement, int indent, t_md_signal *clock, int edge, t_md_type_instance *instance );
static void output_simulation_methods_expression( c_model_descriptor *model, t_md_output_fn output, void *handle, t_md_code_block *code_block, t_md_expression *expr, int main_indent, int sub_indent );

/*a Output functions
 */
/*f string_type
 */
static char *string_type( int width )
{
     if (width<=MD_BITS_PER_UINT64)
     {
          strcpy( type_buffer, "" );
     }
     else
     {
          sprintf( type_buffer, "[%d]", (width+MD_BITS_PER_UINT64-1)/MD_BITS_PER_UINT64 );
     }
     return type_buffer;
}

/*f output_header
 */
static void output_header( c_model_descriptor *model, t_md_output_fn output, void *handle )
{

     output( handle, 0, "/*a Note: created by cyclicity CDL " __CDL__VERSION_STRING " - do not hand edit without adding a comment line here \n");
     output( handle, 0, " */\n");
     output( handle, 0, "\n");
     output( handle, 0, "/*a Includes\n");
     output( handle, 0, " */\n");
     output( handle, 0, "#include <stdio.h>\n");
     output( handle, 0, "#include <stdlib.h>\n");
     output( handle, 0, "#include <string.h>\n");
     output( handle, 0, "#include \"be_model_includes.h\"\n");
     output( handle, 0, "\n");

}

/*f output_defines
 */
static void output_defines( c_model_descriptor *model, t_md_output_fn output, void *handle, int include_assertions, int include_coverage, int include_stmt_coverage )
{

    output( handle, 0, "/*a Defines\n");
    output( handle, 0, " */\n");
    output( handle, 0, "#define ASSIGN_TO_BIT(vector,size,bit,value) se_cmodel_assist_assign_to_bit(vector,size,bit,value)\n" ) ;
    output( handle, 0, "#define ASSIGN_TO_BIT_RANGE(vector,size,bit,length,value) se_cmodel_assist_assign_to_bit_range(vector,size,bit,length,value)\n" ) ;
    output( handle, 0, "#define DISPLAY_STRING(error_number,string) { \\\n" );
    output( handle, 1, "engine->message->add_error( NULL, error_level_info, error_number, error_id_sl_exec_file_allocate_and_read_exec_file, \\\n");
    output( handle, 2, "error_arg_type_integer, engine->cycle(),\\\n" );
    output( handle, 2, "error_arg_type_const_string, \"%s\",\\\n", model->get_name() );
    output( handle, 2, "error_arg_type_malloc_string, string,\\\n" );
    output( handle, 2, "error_arg_type_none ); }\n" );
    output( handle, 0, "#define PRINT_STRING(string) { DISPLAY_STRING(error_number_se_dated_message,string); }\n" );
    if (include_stmt_coverage)
    {
        output( handle, 0, "#define COVER_STATEMENT(stmt_number) {if(stmt_number>=0)se_cmodel_assist_stmt_coverage_statement_reached(stmt_coverage,stmt_number);}\n" ) ;
    }
    else
    {
        output( handle, 0, "#define COVER_STATEMENT(stmt_number) {};\n" ) ;
    }
    if (include_assertions)
    {
        output( handle, 0, "#define ASSERT_STRING(string) { DISPLAY_STRING(error_number_se_dated_assertion,string); }\n" );
        output( handle, 0, "#define ASSERT_START        { if (!(   \n" );
        output( handle, 0, "#define ASSERT_COND_NEXT           ||  \n" );
        output( handle, 0, "#define ASSERT_COND_END             )) { \n" );
        output( handle, 0, "#define ASSERT_START_UNCOND { if (1) {  \n" );
        output( handle, 0, "#define ASSERT_END                   }}\n" );
    }
    else
    {
        output( handle, 0, "#define ASSERT_STRING(string) {}\n" );
        output( handle, 0, "#define ASSERT_START    { if (0 && !(   \n" );
        output( handle, 0, "#define ASSERT_COND_NEXT       &&  \n" );
        output( handle, 0, "#define ASSERT_COND_END        )) { \n" );
        output( handle, 0, "#define ASSERT_START_UNCOND { if (0) {  \n" );
        output( handle, 0, "#define ASSERT_END      }}\n" );
    }

    if (include_coverage)
    {
        output( handle, 0, "#define COVER_STRING(string) { DISPLAY_STRING(error_number_se_dated_coverage,string); }\n" );
        output( handle, 0, "#define COVER_CASE_START(c,b)   { if ( se_cmodel_assist_code_coverage_case_already_reached(code_coverage,c,b) && (\n" );
        output( handle, 0, "#define COVER_CASE_MESSAGE(c,b)       ) ) { se_cmodel_assist_code_coverage_case_now_reached(code_coverage,c,b); \n" );
        output( handle, 0, "#define COVER_CASE_END                 }} \n" );

        output( handle, 0, "#define COVER_START_UNCOND { if (1) {  \n" );
        output( handle, 0, "#define COVER_END                   }}\n" );
    }
    else
    {
        output( handle, 0, "#define COVER_STRING(string) {}\n" );
        output( handle, 0, "#define COVER_CASE_START(c,b) { if ( 0 && ( \n" );
        output( handle, 0, "#define COVER_CASE_MESSAGE(c,b)            )) { \n" );
        output( handle, 0, "#define COVER_CASE_END               }} \n" );

        output( handle, 0, "#define COVER_START_UNCOND { if (0) {  \n" );
        output( handle, 0, "#define COVER_END                   }}\n" );
    }
    output( handle, 0, "#define WHERE_I_AM_VERBOSE {fprintf(stderr,\"%%s:%%s:%%p:%%d\\n\",__FILE__,__func__,this,__LINE__ );}\n");
    output( handle, 0, "#define WHERE_I_AM {}\n");
    output( handle, 0, "#define DEFINE_DUMMY_INPUT static t_sl_uint64 dummy_input[16]={0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0};\n");
    output( handle, 0, "\n");
}

/*f output_type
 */
static void output_type( c_model_descriptor *model, t_md_output_fn output, void *handle, t_md_type_instance *instance, int indent )
{
     switch (instance->type)
     {
     case md_type_instance_type_bit_vector:
          output( handle, indent, "t_sl_uint64 %s%s;\n", instance->output_name, string_type(instance->type_def.data.width) );
          break;
     case md_type_instance_type_array_of_bit_vectors:
          output( handle, indent, "t_sl_uint64 %s[%d]%s;\n", instance->output_name, instance->size, string_type(instance->type_def.data.width) );
          break;
     default:
          output( handle, indent, "<NO TYPE FOR STRUCTURES>\n");
          break;
     }
}

/*f output_types
 */
static void output_types( c_model_descriptor *model, t_md_module *module, t_md_output_fn output, void *handle, int include_coverage, int include_stmt_coverage )
{
    int edge, level;
    t_md_signal *clk;
    t_md_signal *signal;
    t_md_state *reg;
    int i;
    t_md_module_instance *module_instance;

    /*b Output types header
     */
    output( handle, 0, "/*a Types for %s\n", module->output_name);
    output( handle, 0, "*/\n");

    /*b Output clocked storage types
     */ 
    for (clk=module->clocks; clk; clk=clk->next_in_list)
    {
        for (edge=0; edge<2; edge++)
        {
            if (clk->data.clock.edges_used[edge])
            {
                output( handle, 0, "/*t t_%s_%s_%s_state\n", module->output_name, edge_name[edge], clk->name );
                output( handle, 0, "*/\n");
                output( handle, 0, "typedef struct t_%s_%s_%s_state\n", module->output_name, edge_name[edge], clk->name );
                output( handle, 0, "{\n");
                for (reg=module->registers; reg; reg=reg->next_in_list)
                {
                    if ( (reg->clock_ref==clk) && (reg->edge==edge) )
                    {
                        for (i=0; i<reg->instance_iter->number_children; i++)
                        {
                            output_type( model, output, handle, reg->instance_iter->children[i], 1 );
                        }
                    }
                    if (reg->usage_type!=md_usage_type_rtl) output( handle, -1, usage_type_comment[reg->usage_type] );
                }
                output( handle, 0, "} t_%s_%s_%s_state;\n", module->output_name, edge_name[edge], clk->name );
                output( handle, 0, "\n");
            }
        }
    }

    /*b Output input pointer type
     */ 
    output( handle, 0, "/*t t_%s_inputs\n", module->output_name);
    output( handle, 0, "*/\n");
    output( handle, 0, "typedef struct t_%s_inputs\n", module->output_name);
    output( handle, 0, "{\n");
    for (signal=module->inputs; signal; signal=signal->next_in_list)
    {
        for (i=0; i<signal->instance_iter->number_children; i++)
        {
            output( handle, 1, "t_sl_uint64 *%s;\n", signal->instance_iter->children[i]->output_name );
        }
    }
    output( handle, 0, "} t_%s_inputs;\n", module->output_name );
    output( handle, 0, "\n");

    /*b Output input storage type
     */
    output( handle, 0, "/*t t_%s_input_state\n", module->output_name);
    output( handle, 0, "*/\n");
    output( handle, 0, "typedef struct t_%s_input_state\n", module->output_name);
    output( handle, 0, "{\n");
    for (signal=module->inputs; signal; signal=signal->next_in_list)
    {
        for (i=0; i<signal->instance_iter->number_children; i++)
        {
            output_type( model, output, handle, signal->instance_iter->children[i], 1 );
        }
    }
    output( handle, 0, "} t_%s_input_state;\n", module->output_name );
    output( handle, 0, "\n");

    /*b Output combinatorials storage type
     */ 
    output( handle, 0, "/*t t_%s_combinatorials\n", module->output_name );
    output( handle, 0, "*/\n");
    output( handle, 0, "typedef struct t_%s_combinatorials\n", module->output_name );
    output( handle, 0, "{\n");
    for (signal=module->combinatorials; signal; signal=signal->next_in_list)
    {
        for (i=0; i<signal->instance_iter->number_children; i++)
        {
            output_type( model, output, handle, signal->instance_iter->children[i], 1 );
        }
        if (signal->usage_type!=md_usage_type_rtl) output( handle, -1, usage_type_comment[signal->usage_type] );
    }
    output( handle, 0, "} t_%s_combinatorials;\n", module->output_name );
    output( handle, 0, "\n");

    /*b Output nets storage type
     */ 
    output( handle, 0, "/*t t_%s_nets\n", module->output_name );
    output( handle, 0, "*/\n");
    output( handle, 0, "typedef struct t_%s_nets\n", module->output_name );
    output( handle, 0, "{\n");
    for (signal=module->nets; signal; signal=signal->next_in_list)
    {
        for (i=0; i<signal->instance_iter->number_children; i++)
        {
            if (signal->instance_iter->children[i]->driven_in_parts)
            {
                output_type( model, output, handle, signal->instance_iter->children[i], 1 );
            }
            else
            {
                output( handle, 1, "t_sl_uint64 *%s;\n", signal->instance_iter->children[i]->output_name );
            }
        }
    }
    output( handle, 0, "} t_%s_nets;\n", module->output_name );
    output( handle, 0, "\n");

    /*b Output instantiations storage types
     */
    for (module_instance=module->module_instances; module_instance; module_instance=module_instance->next_in_list)
    {
        t_md_module_instance_input_port *input_port;
        t_md_module_instance_output_port *output_port;

        output( handle, 0, "/*t t_%s_instance__%s %s\n", module->output_name, module_instance->name, module_instance->type );
        output( handle, 0, "*/\n");
        output( handle, 0, "typedef struct t_%s_instance__%s\n", module->output_name, module_instance->name );
        output( handle, 0, "{\n");
        output( handle, 1, "void *handle;\n" );
        if (module_instance->module_definition)
        {
            for (clk=module_instance->module_definition->clocks; clk; clk=clk->next_in_list)
            {
                output( handle, 1, "void *%s__clock_handle;\n", clk->name );
            }
            output( handle, 1, "struct\n" );
            output( handle, 1, "{\n" );
            for (input_port=module_instance->inputs; input_port; input_port=input_port->next_in_list)
            {
                output_type( model, output, handle, input_port->module_port_instance, 2 );
            }        
            output( handle, 1, "} inputs;\n" );
            output( handle, 1, "struct\n" );
            output( handle, 1, "{\n" );
            for (output_port=module_instance->outputs; output_port; output_port=output_port->next_in_list)
            {
                if (output_port->module_port_instance->output_name )
                {
                    output( handle, 2, "t_sl_uint64 *%s;\n", output_port->module_port_instance->output_name );
                }
                else
                {
                    output( handle, 2, "t_sl_uint64 *<<UNKNOWN OUTPUT - PORT ON INSTANCE NOT ON ACTUAL MODULE?>>;\n" );
                }
            }
            output( handle, 1, "} outputs;\n" );
        }
        output( handle, 0, "} t_%s_instance__%s;\n", module->output_name, module_instance->name );
        output( handle, 0, "\n");
    }

    /*b Output coverage storage types - if we include coverage
     */ 
    if (include_coverage)
    {
        output( handle, 0, "/*t t_%s_code_coverage\n", module->output_name );
        output( handle, 0, "*/\n");
        output( handle, 0, "typedef struct t_%s_code_coverage\n", module->output_name );
        output( handle, 0, "{\n");
        output( handle, 1, "t_sl_uint64 bitmap[%d];\n", module->next_cover_case_entry );
        output( handle, 0, "} t_%s_code_coverage;\n", module->output_name );
        output( handle, 0, "\n");
    }
    if (include_stmt_coverage)
    {
        output( handle, 0, "/*t t_%s_stmt_coverage\n", module->output_name );
        output( handle, 0, "*/\n");
        output( handle, 0, "typedef struct t_%s_stmt_coverage\n", module->output_name );
        output( handle, 0, "{\n");
        output( handle, 1, "unsigned char map[%d];\n", module->last_statement_enumeration?module->last_statement_enumeration:1 );
        output( handle, 0, "} t_%s_stmt_coverage;\n", module->output_name );
        output( handle, 0, "\n");
    }

    /*b Output C++ class for the module
     */ 
    output( handle, 0, "/*t c_%s\n", module->output_name );
    output( handle, 0, "*/\n");
    output( handle, 0, "class c_%s;\n", module->output_name );
    output( handle, 0, "typedef t_sl_error_level t_%s_clock_callback_fn( void );\n", module->output_name );
    output( handle, 0, "typedef t_%s_clock_callback_fn (c_%s::*t_c_%s_clock_callback_fn);\n", module->output_name, module->output_name, module->output_name );
    output( handle, 0, "typedef struct\n");
    output( handle, 0, "{\n");
    output( handle, 1, "t_c_%s_clock_callback_fn preclock;\n", module->output_name );
    output( handle, 1, "t_c_%s_clock_callback_fn clock;\n", module->output_name );
    output( handle, 0, "} t_c_%s_clock_callback_fns;\n", module->output_name );
    output( handle, 0, "class c_%s\n", module->output_name );
    output( handle, 0, "{\n");
    output( handle, 0, "public:\n");
    output( handle, 1, "c_%s( class c_engine *eng, void *eng_handle );\n", module->output_name);
    output( handle, 1, "~c_%s();\n", module->output_name);
    output( handle, 1, "t_c_%s_clock_callback_fns clocks_fired[1000];\n", module->output_name);
    output( handle, 1, "t_sl_error_level delete_instance( void );\n" );
    output( handle, 1, "t_sl_error_level reset( int pass );\n" );
    output( handle, 1, "t_sl_error_level capture_inputs( void );\n" );
    output( handle, 1, "t_sl_error_level propagate_inputs( void );\n" );
    output( handle, 1, "t_sl_error_level propagate_state( void );\n" );
    output( handle, 1, "t_sl_error_level prepreclock( void );\n" );
    output( handle, 1, "t_sl_error_level preclock( t_c_%s_clock_callback_fn preclock, t_c_%s_clock_callback_fn clock );\n", module->output_name, module->output_name, module->output_name );
    output( handle, 1, "t_sl_error_level clock( void );\n" );
    for (clk=module->clocks; clk; clk=clk->next_in_list)
    {
        for (edge=0; edge<2; edge++)
        {
            if (clk->data.clock.edges_used[edge])
            {
                output( handle, 1, "t_sl_error_level preclock_%s_%s( void );\n", edge_name[edge], clk->name );
                output( handle, 1, "t_sl_error_level clock_%s_%s( void );\n", edge_name[edge], clk->name );
            }
        }
    }
    for (signal=module->inputs; signal; signal=signal->next_in_list)
    {
        for (level=0; level<2; level++)
        {
            if (signal->data.input.levels_used_for_reset[level])
            {
                output( handle, 1, "t_sl_error_level reset_%s_%s( void );\n", level_name[level], signal->name );
            }
        }
    }
    output( handle, 0, "private:\n");
    output( handle, 1, "c_engine *engine;\n");
    output( handle, 1, "int clocks_to_call;\n" );
    output( handle, 1, "void *engine_handle;\n");
    output( handle, 1, "int inputs_captured;\n" );

    for (clk=module->clocks; clk; clk=clk->next_in_list)
    {
        for (edge=0; edge<2; edge++)
        {
            if (clk->data.clock.edges_used[edge])
            {
                t_md_signal *clk2;
                for (clk2=module->clocks; clk2; clk2=clk2->next_in_list)
                {
                    if (clk2->data.clock.clock_ref == clk)
                    {
                        if (clk2->data.clock.edges_used[edge])
                        {
                            output( handle, 1, "int clock_enable__%s_%s;\n", edge_name[edge], clk2->name );
                        }
                    }
                }
            }
        }
    }

    output( handle, 1, "t_%s_inputs inputs;\n", module->output_name );
    output( handle, 1, "t_%s_input_state input_state;\n", module->output_name );
    output( handle, 1, "t_%s_combinatorials combinatorials;\n", module->output_name);
    output( handle, 1, "t_%s_nets nets;\n", module->output_name);
    for (module_instance=module->module_instances; module_instance; module_instance=module_instance->next_in_list)
    {
        output( handle, 1, "t_%s_instance__%s instance_%s;\n", module->output_name, module_instance->name, module_instance->name );
    }
    if (include_coverage)
    {
        output( handle, 1, "t_%s_code_coverage code_coverage;\n", module->output_name);
    }
    if (include_stmt_coverage)
    {
        output( handle, 1, "t_%s_stmt_coverage stmt_coverage;\n", module->output_name);
    }
    if (1)// include_log
    {
        output( handle, 1, "struct t_engine_log_event_array *log_event_array;\n");
        output( handle, 1, "t_se_signal_value *log_signal_data;\n");
    }
    for (clk=module->clocks; clk; clk=clk->next_in_list)
    {
        for (edge=0; edge<2; edge++)
        {
            if (clk->data.clock.edges_used[edge])
            {
                output( handle, 1, "t_%s_%s_%s_state next_%s_%s_state;\n", module->output_name, edge_name[edge], clk->name, edge_name[edge], clk->name );
                output( handle, 1, "t_%s_%s_%s_state %s_%s_state;\n", module->output_name, edge_name[edge], clk->name, edge_name[edge], clk->name );
            }
        }
    }
    output( handle, 0, "};\n");
    output( handle, 0, "\n");
}

/*f output_static_variables
 */
static void output_static_variables( c_model_descriptor *model, t_md_module *module, t_md_output_fn output, void *handle )
{
    int i;
    int edge;
    t_md_signal *clk, *signal;
    t_md_state *reg;
    t_md_type_instance *instance;

    /*b Output header with #define
     */
    output( handle, 0, "/*a Static variables for %s\n", module->output_name);
    output( handle, 0, "*/\n");

    output( handle, 0, "/*v struct_offset wrapper\n");
    output( handle, 0, "*/\n");
    output( handle, 0, "#define struct_offset( ptr, a ) (((char *)&(ptr->a))-(char *)ptr)\n");

    /*b Output logging
     */
    module->output.total_log_args = 0;
    if (1) // include_log)
    {
        t_md_statement *stmt;
        int num_args;
        int i, j;
        i=0;
        num_args=0;
        for (stmt=module->statements; stmt; stmt=stmt->next_in_module)
        {
            if (stmt->type==md_statement_type_log)
            {
                t_md_labelled_expression *arg;
                stmt->data.log.id_within_module = i;
                stmt->data.log.arg_id_within_module = num_args;
                for (j=0, arg=stmt->data.log.arguments; arg; arg=arg->next_in_chain, j++);
                if (i==0)
                {
                    output( handle, 0, "\n/*v %s_log_event_descriptor\n", module->output_name );
                    output( handle, 0, "*/\n");
                    output( handle, 0, "static t_engine_text_value_pair %s_log_event_descriptor[] = \n", module->output_name );
                    output( handle, 0, "{\n");
                }
                output( handle, 0, "{\"%s\", %d},\n", stmt->data.log.message, j );
                for (j=0, arg=stmt->data.log.arguments; arg; arg=arg->next_in_chain, j++)
                {
                    output( handle, 0, "{\"%s\", %d},\n", arg->text, j+num_args ); // Consumes log_signal_data[num_args -> num_args+j-1]
                }
                num_args+=j;
                i++;
            }
        }
        if (i!=0)
        {
            output( handle, 0, "{NULL, 0},\n" );
            output( handle, 0, "};\n\n" );
        }
        module->output.total_log_args = num_args;
    }

    /*b Output nets structures if required
     */
    if (module->nets)
    {
        int has_indirect;
        int has_direct;
        has_indirect = has_direct = 0;
        for (signal=module->nets; signal; signal=signal->next_in_list)
        {
            for (i=0; i<signal->instance_iter->number_children; i++)
            {
                if (signal->instance_iter->children[i]->driven_in_parts)
                {
                    has_direct=1;
                }
                else
                {
                    has_indirect=1;
                }
            }
        }

        if (has_indirect)
        {
            output( handle, 0, "/*v state_desc_%s_nets\n", module->output_name );
            output( handle, 0, "*/\n");
            output( handle, 0, "static t_%s_nets *___%s_indirect_net__ptr;\n", module->output_name, module->output_name );
            output( handle, 0, "static t_engine_state_desc state_desc_%s_indirect_nets[] =\n", module->output_name );
            output( handle, 0, "{\n");
            for (signal=module->nets; signal; signal=signal->next_in_list)
            {
                for (i=0; i<signal->instance_iter->number_children; i++)
                {
                    if (!signal->instance_iter->children[i]->driven_in_parts)
                    {
                        instance = signal->instance_iter->children[i];
                        switch (instance->type)
                        {
                        case md_type_instance_type_bit_vector:
                            output( handle, 1, "{\"%s\",engine_state_desc_type_bits, NULL, struct_offset(___%s_indirect_net__ptr, %s), {%d,0,0,0}, {NULL,NULL,NULL,NULL} },\n", instance->output_name, module->output_name, instance->output_name, instance->type_def.data.width );
                            break;
                        case md_type_instance_type_array_of_bit_vectors:
                            output( handle, 1, "{\"%s\",engine_state_desc_type_memory, NULL, struct_offset(___%s_indirect_net__ptr, %s), {%d,%d,0,0}, {NULL,NULL,NULL,NULL} },\n", instance->output_name, module->output_name, instance->output_name, instance->type_def.data.width, instance->size );
                            break;
                        default:
                            output( handle, 1, "<NO TYPE FOR STRUCTURES>\n");
                            break;
                        }
                    }
                }
            }
            output( handle, 1, "{\"\", engine_state_desc_type_none, NULL, 0, {0,0,0,0}, {NULL,NULL,NULL,NULL} }\n");
            output( handle, 0, "};\n\n");
        }
        if (has_direct)
        {
            output( handle, 0, "/*v state_desc_%s_nets\n", module->output_name );
            output( handle, 0, "*/\n");
            output( handle, 0, "static t_%s_nets *___%s_direct_net__ptr;\n", module->output_name, module->output_name );
            output( handle, 0, "static t_engine_state_desc state_desc_%s_direct_nets[] =\n", module->output_name );
            output( handle, 0, "{\n");
            for (signal=module->nets; signal; signal=signal->next_in_list)
            {
                for (i=0; i<signal->instance_iter->number_children; i++)
                {
                    if (signal->instance_iter->children[i]->driven_in_parts)
                    {
                        instance = signal->instance_iter->children[i];
                        switch (instance->type)
                        {
                        case md_type_instance_type_bit_vector:
                            output( handle, 1, "{\"%s\",engine_state_desc_type_bits, NULL, struct_offset(___%s_direct_net__ptr, %s), {%d,0,0,0}, {NULL,NULL,NULL,NULL} },\n", instance->output_name, module->output_name, instance->output_name, instance->type_def.data.width );
                            break;
                        case md_type_instance_type_array_of_bit_vectors:
                            output( handle, 1, "{\"%s\",engine_state_desc_type_memory, NULL, struct_offset(___%s_direct_net__ptr, %s), {%d,%d,0,0}, {NULL,NULL,NULL,NULL} },\n", instance->output_name, module->output_name, instance->output_name, instance->type_def.data.width, instance->size );
                            break;
                        default:
                            output( handle, 1, "<NO TYPE FOR STRUCTURES>\n");
                            break;
                        }
                    }
                }
            }
            output( handle, 1, "{\"\", engine_state_desc_type_none, NULL, 0, {0,0,0,0}, {NULL,NULL,NULL,NULL} }\n");
            output( handle, 0, "};\n\n");
        }
    }

    /*b Output combinatorials structure if required
     */
    if (module->combinatorials)
    {
        output( handle, 0, "/*v state_desc_%s_combs\n", module->output_name );
        output( handle, 0, "*/\n");
        output( handle, 0, "static t_%s_combinatorials *___%s_comb__ptr;\n", module->output_name, module->output_name );
        output( handle, 0, "static t_engine_state_desc state_desc_%s_combs[] =\n", module->output_name );
        output( handle, 0, "{\n");
        for (signal=module->combinatorials; signal; signal=signal->next_in_list)
        {
            for (i=0; i<signal->instance_iter->number_children; i++)
            {
                instance = signal->instance_iter->children[i];
                switch (instance->type)
                {
                case md_type_instance_type_bit_vector:
                    output( handle, 1, "{\"%s\",engine_state_desc_type_bits, NULL, struct_offset(___%s_comb__ptr, %s), {%d,0,0,0}, {NULL,NULL,NULL,NULL} },\n", instance->output_name, module->output_name, instance->output_name, instance->type_def.data.width );
                    break;
                case md_type_instance_type_array_of_bit_vectors:
                    output( handle, 1, "{\"%s\",engine_state_desc_type_memory, NULL, struct_offset(___%s_comb__ptr, %s), {%d,%d,0,0}, {NULL,NULL,NULL,NULL} },\n", instance->output_name, module->output_name, instance->output_name, instance->type_def.data.width, instance->size );
                    break;
                default:
                    output( handle, 1, "<NO TYPE FOR STRUCTURES>\n");
                    break;
                }
            }
        }
        output( handle, 1, "{\"\", engine_state_desc_type_none, NULL, 0, {0,0,0,0}, {NULL,NULL,NULL,NULL} }\n");
        output( handle, 0, "};\n\n");
    }

    /*b Output structure for each clock, if required
     */
    for (clk=module->clocks; clk; clk=clk->next_in_list)
    {
        int header_done;
        for (edge=0; edge<2; edge++)
        {
            if (clk->data.clock.edges_used[edge])
            {
                header_done = 0;
                for (reg=module->registers; reg; reg=reg->next_in_list)
                {
                    if ( (reg->clock_ref==clk) && (reg->edge==edge) )
                    {
                        if (!header_done)
                        {
                            output( handle, 0, "/*v state_desc_%s_%s_%s\n", module->output_name, edge_name[edge], clk->name );
                            output( handle, 0, "*/\n");
                            output( handle, 0, "static t_%s_%s_%s_state *___%s_%s_%s__ptr;\n", module->output_name, edge_name[edge], clk->name, module->output_name, edge_name[edge], clk->name );
                            output( handle, 0, "static t_engine_state_desc state_desc_%s_%s_%s[] =\n", module->output_name, edge_name[edge], clk->name );
                            output( handle, 0, "{\n");
                            header_done = 1;
                        }
                        for (i=0; i<reg->instance_iter->number_children; i++)
                        {
                            instance = reg->instance_iter->children[i];
                            switch (instance->type)
                            {
                            case md_type_instance_type_bit_vector:
                                output( handle, 1, "{\"%s\",engine_state_desc_type_bits, NULL, struct_offset(___%s_%s_%s__ptr, %s), {%d,0,0,0}, {NULL,NULL,NULL,NULL} },\n", instance->output_name, module->output_name, edge_name[edge], clk->name, instance->output_name, instance->type_def.data.width );
                                break;
                            case md_type_instance_type_array_of_bit_vectors:
                                output( handle, 1, "{\"%s\",engine_state_desc_type_memory, NULL, struct_offset(___%s_%s_%s__ptr, %s), {%d,%d,0,0}, {NULL,NULL,NULL,NULL} },\n", instance->output_name, module->output_name, edge_name[edge], clk->name, instance->output_name, instance->type_def.data.width, instance->size );
                                break;
                            default:
                                output( handle, 1, "<NO TYPE FOR STRUCTURES>\n");
                                break;
                            }
                        }
                    }
                }
                if (header_done)
                {
                    output( handle, 1, "{\"\", engine_state_desc_type_none, NULL, 0, {0,0,0,0}, {NULL,NULL,NULL,NULL} }\n");
                    output( handle, 0, "};\n");
                    output( handle, 0, "\n");
                }
            }
        }
    }

    output( handle, 0, "/*v struct_offset unwrapper\n");
    output( handle, 0, "*/\n");
    output( handle, 0, "#undef struct_offset\n\n");
}

/*f output_wrapper_functions
 */
static void output_wrapper_functions( c_model_descriptor *model, t_md_module *module, t_md_output_fn output, void *handle )
{
    int edge;
    t_md_signal *clk;

    output( handle, 0, "/*a Static wrapper functions for %s\n", module->output_name);
    output( handle, 0, "*/\n");
    output( handle, 0, "/*f %s_instance_fn\n", module->output_name);
    output( handle, 0, "*/\n");
    output( handle, 0, "static t_sl_error_level %s_instance_fn( c_engine *engine, void *engine_handle )\n", module->output_name);
    output( handle, 0, "{\n");
    output( handle, 1, "c_%s *mod;\n", module->output_name );
    output( handle, 1, "mod = new c_%s( engine, engine_handle );\n", module->output_name);
    output( handle, 1, "if (!mod)\n");
    output( handle, 2, "return error_level_fatal;\n");
    output( handle, 1, "return error_level_okay;\n");
    output( handle, 0, "}\n");
    output( handle, 0, "\n");
    output( handle, 0, "/*f %s_delete_fn - simple callback wrapper for the main method\n", module->output_name);
    output( handle, 0, "*/\n");
    output( handle, 0, "static t_sl_error_level %s_delete_fn( void *handle )\n", module->output_name);
    output( handle, 0, "{\n");
    output( handle, 1, "c_%s *mod;\n", module->output_name);
    output( handle, 1, "t_sl_error_level result;\n");
    output( handle, 1, "mod = (c_%s *)handle;\n", module->output_name);
    output( handle, 1, "result = mod->delete_instance();\n");
    output( handle, 1, "delete( mod );\n");
    output( handle, 1, "return result;\n");
    output( handle, 0, "}\n");
    output( handle, 0, "\n");
    output( handle, 0, "/*f %s_reset_fn\n", module->output_name);
    output( handle, 0, "*/\n");
    output( handle, 0, "static t_sl_error_level %s_reset_fn( void *handle, int pass )\n", module->output_name);
    output( handle, 0, "{\n");
    output( handle, 1, "c_%s *mod;\n", module->output_name);
    output( handle, 1, "mod = (c_%s *)handle;\n", module->output_name);
    output( handle, 1, "return mod->reset( pass );\n");
    output( handle, 0, "}\n");
    output( handle, 0, "\n");
    /* Provide this for everything
       if ( (module->combinatorial_component) || (module->module_instances) )
    */
    output( handle, 0, "/*f %s_combinatorial_fn\n", module->output_name );
    output( handle, 0, "*/\n");
    output( handle, 0, "static t_sl_error_level %s_combinatorial_fn( void *handle )\n", module->output_name );
    output( handle, 0, "{\n");
    output( handle, 1, "c_%s *mod;\n", module->output_name);
    output( handle, 1, "mod = (c_%s *)handle;\n", module->output_name);
    output( handle, 1, "mod->capture_inputs();\n" );
    output( handle, 1, "return mod->propagate_inputs();\n" );
    output( handle, 0, "}\n");
    output( handle, 0, "\n");

    if (module->clocks)
    {
        output( handle, 0, "/*f %s_prepreclock_fn\n", module->output_name );
        output( handle, 0, "*/\n");
        output( handle, 0, "static t_sl_error_level %s_prepreclock_fn( void *handle )\n", module->output_name );
        output( handle, 0, "{\n");
        output( handle, 1, "c_%s *mod;\n", module->output_name);
        output( handle, 1, "mod = (c_%s *)handle;\n", module->output_name);
        output( handle, 1, "return mod->prepreclock();\n" );
        output( handle, 0, "}\n");
        output( handle, 0, "\n");

        output( handle, 0, "/*f %s_clock_fn\n", module->output_name );
        output( handle, 0, "*/\n");
        output( handle, 0, "static t_sl_error_level %s_clock_fn( void *handle )\n", module->output_name );
        output( handle, 0, "{\n");
        output( handle, 1, "c_%s *mod;\n", module->output_name);
        output( handle, 1, "mod = (c_%s *)handle;\n", module->output_name);
        output( handle, 1, "return mod->clock();\n" );
        output( handle, 0, "}\n");
        output( handle, 0, "\n");
    }

    for (clk=module->clocks; clk; clk=clk->next_in_list)
    {
        if (!clk->data.clock.clock_ref) // Not a gated clock - they do not need static functions
        {
            for (edge=0; edge<2; edge++)
            {
                if (clk->data.clock.edges_used[edge])
                {
                    output( handle, 0, "/*f %s_preclock_%s_%s_fn\n", module->output_name, edge_name[edge], clk->name );
                    output( handle, 0, "*/\n");
                    output( handle, 0, "static t_sl_error_level %s_preclock_%s_%s_fn( void *handle )\n", module->output_name, edge_name[edge], clk->name );
                    output( handle, 0, "{\n");
                    output( handle, 1, "c_%s *mod;\n", module->output_name);
                    output( handle, 1, "mod = (c_%s *)handle;\n", module->output_name);
                    output( handle, 1, "mod->preclock( &c_%s::preclock_%s_%s, &c_%s::clock_%s_%s );\n",
                            module->output_name, edge_name[edge], clk->name,
                            module->output_name, edge_name[edge], clk->name );
                    output( handle, 1, "return error_level_okay;\n" );
                    output( handle, 0, "}\n");
                    output( handle, 0, "\n");
                }
            }
        }
    }
}

/*f output_constructors_destructors
 */
static void output_constructors_destructors( c_model_descriptor *model, t_md_module *module, t_md_output_fn output, void *handle, int include_coverage, int include_stmt_coverage )
{
    int edge;
    t_md_signal *clk;
    t_md_signal *signal;
    t_md_state *reg;
    t_md_type_instance *instance;
    t_md_reference_iter iter;
    t_md_reference *reference;
    t_md_module_instance *module_instance;
    int i;

    /*b Header
     */
    output( handle, 0, "/*a Constructors and destructors for %s\n", module->output_name);
    output( handle, 0, "*/\n");

    /*b Constructor header
     */
    output( handle, 0, "/*f c_%s::c_%s\n", module->output_name, module->output_name);
    output( handle, 0, "*/\n");
    output( handle, 0, "c_%s::c_%s( class c_engine *eng, void *eng_handle )\n", module->output_name, module->output_name);
    output( handle, 0, "{\n");
    output( handle, 1, "engine = eng;\n");
    output( handle, 1, "engine_handle = eng_handle;\n");
    output( handle, 0, "\n");
    output( handle, 1, "engine->register_delete_function( engine_handle, (void *)this, %s_delete_fn );\n", module->output_name);
    output( handle, 1, "engine->register_reset_function( engine_handle, (void *)this, %s_reset_fn );\n", module->output_name);
    output( handle, 0, "\n");

    /*b Clear all state and combinatorial data in case of use of unused data elsewhere
     */
    if (1)
    {
        output( handle, 1, "memset(&inputs, 0, sizeof(inputs));\n" ); 
        output( handle, 1, "memset(&input_state, 0, sizeof(input_state));\n" ); 
        output( handle, 1, "memset(&combinatorials, 0, sizeof(combinatorials));\n" ); 
        output( handle, 1, "memset(&nets, 0, sizeof(nets));\n" ); 
        for (clk=module->clocks; clk; clk=clk->next_in_list)
        {
            for (edge=0; edge<2; edge++)
            {
                if (clk->data.clock.edges_used[edge])
                {
                    output( handle, 1, "memset(&next_%s_%s_state, 0, sizeof(next_%s_%s_state));\n", edge_name[edge], clk->name, edge_name[edge], clk->name );
                    output( handle, 1, "memset(&%s_%s_state, 0, sizeof(%s_%s_state));\n", edge_name[edge], clk->name, edge_name[edge], clk->name );
                }
            }
        }
        output( handle, 0, "\n");
    }

    /*b Register combinatorial, input propagation and clock/preclock functions
     */
    if (module->combinatorial_component) // If there is a combinatorial component to this module, then propagate_inputs will work wonders
    {
        output( handle, 1, "engine->register_comb_fn( engine_handle, (void *)this, %s_combinatorial_fn );\n", module->output_name );
    }
    /* GJS Feb 2008 - propagate is used to get all signals valid for display
       This is true of all modules - they need to be called if any of their internal logic is combinatorial for signals
       else if (module->module_instances) // If there are submodules then the inputs to them should be valid after calling propagate_inputs; however, if we are combinatorial we will have already propagated. Note this is overkill, but it works.
    */
    output( handle, 1, "engine->register_propagate_fn( engine_handle, (void *)this, %s_combinatorial_fn );\n", module->output_name );
    if (module->clocks)
    {
        output( handle, 1, "engine->register_prepreclock_fn( engine_handle, (void *)this, %s_prepreclock_fn );\n", module->output_name );
    }
    for (clk=module->clocks; clk; clk=clk->next_in_list)
    {
        if (!clk->data.clock.clock_ref) // Not a gated clock
        {
            if (clk->data.clock.edges_used[1])
            {
                if (clk->data.clock.edges_used[0])
                {
                    output( handle, 1, "engine->register_preclock_fns( engine_handle, (void *)this, \"%s\", %s_preclock_%s_%s_fn, %s_preclock_%s_%s_fn );\n", clk->name,
                            module->output_name, edge_name[0], clk->name, 
                            module->output_name, edge_name[1], clk->name );
                    output( handle, 1, "engine->register_clock_fn( engine_handle, (void *)this, \"%s\", engine_sim_function_type_posedge_clock, %s_clock_fn );\n", clk->name, module->output_name );
                    output( handle, 1, "engine->register_clock_fn( engine_handle, (void *)this, \"%s\", engine_sim_function_type_negedge_clock, %s_clock_fn );\n", clk->name, module->output_name );
                }
                else
                {
                    output( handle, 1, "engine->register_preclock_fns( engine_handle, (void *)this, \"%s\", (t_engine_callback_fn) NULL, %s_preclock_%s_%s_fn );\n", clk->name,
                            module->output_name, edge_name[1], clk->name );
                    output( handle, 1, "engine->register_clock_fn( engine_handle, (void *)this, \"%s\", engine_sim_function_type_negedge_clock, %s_clock_fn );\n", clk->name, module->output_name );
                }
            }
            else
            {
                if (clk->data.clock.edges_used[0])
                {
                    output( handle, 1, "engine->register_preclock_fns( engine_handle, (void *)this, \"%s\", %s_preclock_%s_%s_fn, (t_engine_callback_fn) NULL );\n", clk->name,
                            module->output_name, edge_name[0], clk->name );
                    output( handle, 1, "engine->register_clock_fn( engine_handle, (void *)this, \"%s\", engine_sim_function_type_posedge_clock, %s_clock_fn );\n", clk->name, module->output_name );
                }
            }
        }
    }
    output( handle, 0, "\n");

    /*b Register inputs
     */
    for (signal=module->inputs; signal; signal=signal->next_in_list)
    {
        for (i=0; i<signal->instance_iter->number_children; i++)
        {
            instance = signal->instance_iter->children[i];
            if (instance->type == md_type_instance_type_bit_vector)
            {
                output( handle, 1, "engine->register_input_signal( engine_handle, \"%s\", %d, &inputs.%s );\n", instance->output_name, instance->type_def.data.width, instance->output_name );
            }
            else
            {
                output( handle, 1, "engine->register_input_signal( engine_handle, \"%s\", %d, &inputs.%s ); // ZZZ Don't know how to register an input array\n", instance->output_name, 0, instance->output_name );
            }
        }

        if (signal->data.input.used_combinatorially)
        {
            for (i=0; i<signal->instance_iter->number_children; i++)
            {
                instance = signal->instance_iter->children[i];
                output( handle, 1, "engine->register_comb_input( engine_handle, \"%s\" );\n", instance->output_name );
            }
        }
        for (clk=module->clocks; clk; clk=clk->next_in_list)
        {
            if (!clk->data.clock.clock_ref) // Not a gated clock
            {
                for (edge=0; edge<2; edge++)
                {
                    for (i=0; i<signal->instance_iter->number_children; i++)
                    {
                        t_md_signal *clk2;
                        instance = signal->instance_iter->children[i];
                        for (clk2=module->clocks; clk2; clk2=clk2?clk2->next_in_list:NULL)
                        {
                            if ((clk2==clk) || (clk2->data.clock.clock_ref==clk))
                            {
                                if (model->reference_set_includes( &instance->dependents, clk2, edge ))
                                {
                                    output( handle, 1, "engine->register_input_used_on_clock( engine_handle, \"%s\", \"%s\", %d );\n", instance->output_name, clk->name, edge==md_edge_pos );
                                    clk2=NULL;
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    output( handle, 0, "\n");

    /*b Register outputs
     */
    for (signal=module->outputs; signal; signal=signal->next_in_list)
    {
        if (signal->data.output.register_ref)
        {
            reg = signal->data.output.register_ref;
            for (i=0; i<reg->instance_iter->number_children; i++)
            {
                instance = reg->instance_iter->children[i];
                output( handle, 1, "engine->register_output_signal( engine_handle, \"%s\", %d, &%s_%s_state.%s );\n", instance->output_name, instance->type_def.data.width, edge_name[reg->edge], reg->clock_ref->name, instance->output_name );
                if (!reg->clock_ref->data.clock.clock_ref)
                {
                    output( handle, 1, "engine->register_output_generated_on_clock( engine_handle, \"%s\", \"%s\", %d );\n", instance->output_name, reg->clock_ref->name, reg->edge==md_edge_pos);
                }
                else
                {
                    output( handle, 1, "engine->register_output_generated_on_clock( engine_handle, \"%s\", \"%s\", %d );\n", instance->output_name, reg->clock_ref->data.clock.clock_ref->name, reg->edge==md_edge_pos);
                }
                output( handle, 1, "%s_%s_state.%s = 0;\n", edge_name[reg->edge], reg->clock_ref->name, instance->output_name );
            }
        }
        if (signal->data.output.combinatorial_ref)
        {
            for (i=0; i<signal->data.output.combinatorial_ref->instance_iter->number_children; i++)
            {
                instance = signal->data.output.combinatorial_ref->instance_iter->children[i];
                output( handle, 1, "engine->register_output_signal( engine_handle, \"%s\", %d, &combinatorials.%s );\n", instance->output_name, instance->type_def.data.width, instance->output_name);
                if (signal->data.output.derived_combinatorially )
                {
                    output( handle, 1, "engine->register_comb_output( engine_handle, \"%s\" );\n", instance->output_name );
                }
                output( handle, 1, "combinatorials.%s = 0;\n", instance->output_name);
            }
        }
        if (signal->data.output.net_ref)
        {
            for (i=0; i<signal->data.output.net_ref->instance_iter->number_children; i++)
            {
                instance = signal->data.output.net_ref->instance_iter->children[i];
                output( handle, 1, "engine->register_output_signal( engine_handle, \"%s\", %d, NULL); // Will be tied to submodule\n", instance->output_name, instance->type_def.data.width );
                if (signal->data.output.derived_combinatorially)
                {
                    output( handle, 1, "engine->register_comb_output( engine_handle, \"%s\" );\n", instance->output_name );
                }
                model->reference_set_iterate_start( &signal->data.output.clocks_derived_from, &iter ); // For every clock that the prototype says the output is derived from, map back to clock name, go to top of clock gate tree, and say that generates it
                while ((reference = model->reference_set_iterate(&iter))!=NULL)
                {
                    t_md_signal *clock;
                    clock = reference->data.signal;
                    while (clock->data.clock.clock_ref) { clock=clock->data.clock.clock_ref; }
                    output( handle, 1, "engine->register_output_generated_on_clock( engine_handle, \"%s\", \"%s\", %d );\n", instance->output_name, clock->name, reference->edge==md_edge_pos);
                }
            }
        }
    }
    output( handle, 0, "\n");

    /*b Instantiate submodules and get their handles
     */
    for (module_instance=module->module_instances; module_instance; module_instance=module_instance->next_in_list)
    {
        if (module_instance->module_definition)
        {
            output( handle, 1, "engine->instantiate( engine_handle, \"%s\", \"%s\", NULL );\n", module_instance->output_type, module_instance->name );
            output( handle, 1, "instance_%s.handle = engine->submodule_get_handle( engine_handle, \"%s\" );\n", module_instance->name, module_instance->name);
            for (clk=module_instance->module_definition->clocks; clk; clk=clk->next_in_list)
            {
                output( handle, 1, "instance_%s.%s__clock_handle = engine->submodule_get_clock_handle( instance_%s.handle, \"%s\" );\n", module_instance->name, clk->name, module_instance->name, clk->name );
            }
        }
    }
    output( handle, 0, "\n");

    /*b Tie instance inputs and outputs
     */
    for (module_instance=module->module_instances; module_instance; module_instance=module_instance->next_in_list)
    {
        if (module_instance->module_definition)
        {
            t_md_module_instance_input_port *input_port;
            t_md_module_instance_output_port *output_port;
            for (input_port=module_instance->inputs; input_port; input_port=input_port->next_in_list)
            {
                int is_comb = input_port->module_port_instance->reference.data.signal->data.input.used_combinatorially;
                output( handle, 1, "{ int comb, size;\n");
                output( handle, 2, "engine->submodule_input_type( instance_%s.handle, \"%s\", &comb, &size );\n", module_instance->name, input_port->module_port_instance->output_name );
                output( handle, 2, "if (comb !=%d){ fprintf(stderr,\"Comb of input %s.%s.%s is %%d expected %d\\n\", comb); }\n", is_comb, module->output_name, module_instance->name, input_port->module_port_instance->output_name, is_comb );
                output( handle, 1, "}\n");
                output( handle, 1, "engine->submodule_drive_input( instance_%s.handle, \"%s\", &instance_%s.inputs.%s, %d );\n",
                        module_instance->name, input_port->module_port_instance->output_name,
                        module_instance->name, input_port->module_port_instance->output_name,
                        input_port->module_port_instance->type_def.data.width );
            }
            for (output_port=module_instance->outputs; output_port; output_port=output_port->next_in_list)
            {
                int used_comb = output_port->module_port_instance->reference.data.signal->data.output.derived_combinatorially;
                output( handle, 1, "{ int comb, size;\n");
                output( handle, 2, "engine->submodule_output_type( instance_%s.handle, \"%s\", &comb, &size );\n", module_instance->name, output_port->module_port_instance->output_name );
                output( handle, 2, "if (comb !=%d){ fprintf(stderr,\"Comb of output %s.%s.%s is %%d expected %d\\n\", comb); }\n", used_comb, module->output_name, module_instance->name, output_port->module_port_instance->output_name, used_comb );
                output( handle, 1, "}\n");
                if (output_port->lvar->instance->reference.data.signal->data.net.output_ref) // If the submodule directly drives an output wholly
                {
                    output( handle, 1, "engine->submodule_output_drive_module_output( instance_%s.handle, \"%s\", engine_handle, \"%s\" );\n",
                            module_instance->name, output_port->module_port_instance->output_name,
                            output_port->lvar->instance->output_name );
                }
                // Drive to this module's data instance_SUB.outputs.SUBPORT
                output( handle, 1, "engine->submodule_output_add_receiver( instance_%s.handle, \"%s\", &instance_%s.outputs.%s, %d );\n",
                        module_instance->name, output_port->module_port_instance->output_name,
                        module_instance->name, output_port->module_port_instance->output_name,
                        output_port->module_port_instance->type_def.data.width );
                // Drive to this module's data nets.NETNAME
                if (output_port->lvar->instance->driven_in_parts)
                {
                    //printf("If lvar is partially driven, we don't want the net driven here\n");
                }
                else
                {
                    output( handle, 1, "engine->submodule_output_add_receiver( instance_%s.handle, \"%s\", &nets.%s, %d );\n",
                            module_instance->name, output_port->module_port_instance->output_name,
                            output_port->lvar->instance->output_name,
                            output_port->module_port_instance->type_def.data.width );
                }
            }
        }
    }
    output( handle, 0, "\n");

    /*b Register state descriptors
     */
    if (module->nets)
    {
        int has_indirect;
        int has_direct;
        has_indirect = has_direct = 0;
        for (signal=module->nets; signal; signal=signal->next_in_list)
        {
            for (i=0; i<signal->instance_iter->number_children; i++)
            {
                if (signal->instance_iter->children[i]->driven_in_parts)
                {
                    has_direct=1;
                }
                else
                {
                    has_indirect=1;
                }
            }
        }
        if (has_direct)
        {
            output( handle, 1, "engine->register_state_desc( engine_handle, 1, state_desc_%s_direct_nets, &nets, NULL );\n", module->output_name );
        }
        if (has_indirect)
        {
            output( handle, 1, "engine->register_state_desc( engine_handle, 3, state_desc_%s_indirect_nets, &nets, NULL );\n", module->output_name );
        }
    }
    if (module->combinatorials)
    {
        output( handle, 1, "engine->register_state_desc( engine_handle, 1, state_desc_%s_combs, &combinatorials, NULL );\n", module->output_name );
    }
    for (clk=module->clocks; clk; clk=clk->next_in_list)
    {
        for (edge=0; edge<2; edge++)
        {
            if (clk->data.clock.edges_used[edge])
            {
                for (reg=module->registers; reg; reg=reg->next_in_list)
                {
                    if ( (reg->clock_ref==clk) && (reg->edge==edge) )
                    {
                        output( handle, 1, "engine->register_state_desc( engine_handle, 1, state_desc_%s_%s_%s, &%s_%s_state, NULL );\n", module->output_name, edge_name[edge], clk->name, edge_name[edge], clk->name );
                        break;
                    }
                }
            }
        }
    }

    /*b Register for coverage
     */
    if (include_coverage)
    {
        output( handle, 1, "se_cmodel_assist_code_coverage_register( engine, engine_handle, code_coverage );\n" );
        output( handle, 0, "\n");
    }
    if (include_stmt_coverage)
    {
        output( handle, 1, "se_cmodel_assist_stmt_coverage_register( engine, engine_handle, stmt_coverage );\n" );
        output( handle, 0, "\n");
    }

    /*b Logging declarations
     */
    if (module->output.total_log_args>0)
    {
        output( handle, 1, "log_signal_data = (t_se_signal_value *)malloc(sizeof(t_se_signal_value)*%d);\n", module->output.total_log_args );
        output( handle, 1, "log_event_array = engine->log_event_register_array( engine_handle, %s_log_event_descriptor, log_signal_data );\n", module->output_name );
    }
    output( handle, 0, "}\n");
    output( handle, 0, "\n");

    /*b Output destructor
     */
    output( handle, 0, "/*f c_%s::~c_%s\n", module->output_name, module->output_name);
    output( handle, 0, "*/\n");
    output( handle, 0, "c_%s::~c_%s()\n", module->output_name, module->output_name);
    output( handle, 0, "{\n");
    output( handle, 1, "delete_instance();\n");
    output( handle, 0, "}\n");
    output( handle, 0, "\n");
    output( handle, 0, "/*f c_%s::delete_instance\n", module->output_name);
    output( handle, 0, "*/\n");
    output( handle, 0, "t_sl_error_level c_%s::delete_instance( void )\n", module->output_name);
    output( handle, 0, "{\n");
    output( handle, 1, "return error_level_okay;\n");
    output( handle, 0, "}\n");
    output( handle, 0, "\n");
}

/*f output_simulation_methods_lvar
  If in_expression is 0, then we are assigning so require 'next_state', and we don't insert the bit subscripting
  If in_expression is 1, then we can also add the bit subscripting
 */
static void output_simulation_methods_lvar( c_model_descriptor *model, t_md_output_fn output, void *handle, t_md_code_block *code_block, t_md_lvar *lvar, int main_indent, int sub_indent, int in_expression )
{
    if (in_expression && (lvar->subscript_start.type != md_lvar_data_type_none))
    {
        output( handle, -1, "((" );
    }
    if (lvar->instance_type == md_lvar_instance_type_state)
    {
        t_md_state *state;
        state = lvar->instance_data.state;
        if (in_expression)
        {
            output( handle, -1, "%s_%s_state.%s", edge_name[state->edge], state->clock_ref->name, lvar->instance->output_name );
        }
        else
        {
            output( handle, -1, "next_%s_%s_state.%s", edge_name[state->edge], state->clock_ref->name, lvar->instance->output_name );
        }
    }
    else
    {
        t_md_signal *signal;
        signal = lvar->instance_data.signal;
        switch (signal->type)
        {
        case md_signal_type_input:
            output( handle, -1, "input_state.%s", lvar->instance->output_name );
            break;
        case md_signal_type_output:
            if (signal->data.output.combinatorial_ref)
            {
                output( handle, -1, "combinatorials.%s", lvar->instance->output_name );
            }
            else
            {
                output( handle, -1, "<unresolved output %s>", signal->name );
            }
            break;
        case md_signal_type_combinatorial:
            output( handle, -1, "combinatorials.%s", lvar->instance->output_name );
            break;
        case md_signal_type_net:
            if (lvar->instance->driven_in_parts)
            {
                output( handle, -1, "nets.%s", lvar->instance->output_name );
            }
            else
            {
                output( handle, -1, "nets.%s[0]", lvar->instance->output_name );
            }
            break;
        default:
            output( handle, -1, "<clock signal in expression %s>", signal->name );
            break;
        }
    }
    if (lvar->index.type != md_lvar_data_type_none)
    {
        output( handle, -1, "[" );
        switch (lvar->index.type)
        {
        case md_lvar_data_type_integer:
            output( handle, -1, "%d", lvar->index.data.integer );
            break;
        case md_lvar_data_type_expression:
            output_simulation_methods_expression( model, output, handle, code_block, lvar->index.data.expression, main_indent, sub_indent+1 );
            break;
        default:
            break;
        }
        output( handle, -1, "]" );
    }
    if ((in_expression) && (lvar->subscript_start.type != md_lvar_data_type_none))
    {
        if (lvar->subscript_start.type == md_lvar_data_type_integer)
        {
            output( handle, -1, ">>%d)", lvar->subscript_start.data.integer );
        }
        else if (lvar->subscript_start.type == md_lvar_data_type_expression)
        {
            output( handle, -1, ">>(" );
            output_simulation_methods_expression( model, output, handle, code_block, lvar->subscript_start.data.expression, main_indent, sub_indent+1 );
            output( handle, -1, "))" );
        }
        if (lvar->subscript_length.type != md_lvar_data_type_none)
        {
            output( handle, -1, "&%s/*%d*/)", bit_mask[lvar->subscript_length.data.integer],lvar->subscript_length.data.integer );
        }
        else
        {
            output( handle, -1, "&1)" );
        }
    }
}

/*f output_simulation_methods_expression
 */
static void output_simulation_methods_expression( c_model_descriptor *model, t_md_output_fn output, void *handle, t_md_code_block *code_block, t_md_expression *expr, int main_indent, int sub_indent )
{
    /*b If the expression is NULL then something went wrong...
     */
    if (!expr)
    {
        fprintf( stderr, "ISSUE - NULL expression being output - something has gone wrong\n" );
        output( handle, -1, "0 /*<NULL expression>*/" );
        return;
    }

    /*b Output code for the expression
     */
    if (expr->width>64)
    {
        fprintf( stderr, "ISSUE - expression of size >64 is being output; we don't support that yet\n" );
    }
    switch (expr->type)
    {
    case md_expr_type_value:
        output( handle, -1, "0x%llxLL", expr->data.value.value.value[0] );
        break;
    case md_expr_type_lvar:
        output_simulation_methods_lvar( model, output, handle, code_block, expr->data.lvar, main_indent, sub_indent, 1 );
        break;
    case md_expr_type_bundle:
        output( handle, -1, "(((" );
        output_simulation_methods_expression( model, output, handle, code_block, expr->data.bundle.a, main_indent, sub_indent+1 );
        output( handle, -1, ")<<%d) | (", expr->data.bundle.b->width );
        output_simulation_methods_expression( model, output, handle, code_block, expr->data.bundle.b, main_indent, sub_indent+1 );
        output( handle, -1, "))" );
        break;
    case md_expr_type_cast:
        if ( (expr->data.cast.expression) &&
             (expr->data.cast.expression->width < expr->width) &&
             (expr->data.cast.signed_cast) )
        {
            output( handle, -1, "(SIGNED LENGTHENING CASTS NOT IMPLEMENTED YET: %d to %d)", expr->data.cast.expression->width, expr->width );
        }
        else
        {
            output( handle, -1, "(" );
            output_simulation_methods_expression( model, output, handle, code_block, expr->data.cast.expression, main_indent, sub_indent+1 );
            output( handle, -1, ")&%s/*%d*/", (expr->width<0)?"!!!<0!!!":((expr->width>64)?"!!!!>64":bit_mask[expr->width]),expr->width );
        }
        break;
    case md_expr_type_fn:
        switch (expr->data.fn.fn)
        {
        case md_expr_fn_logical_not:
        case md_expr_fn_not:
        case md_expr_fn_neg:
            switch (expr->data.fn.fn)
            {
            case md_expr_fn_neg:
                output( handle, -1, "(-(" );
                break;
            case md_expr_fn_not:
                output( handle, -1, "(~(" );
                break;
            default:
                output( handle, -1, "(!(" );
            }
            output_simulation_methods_expression( model, output, handle, code_block, expr->data.fn.args[0], main_indent, sub_indent+1 );
            output( handle, -1, "))&%s", bit_mask[expr->width] );
            break;
        case md_expr_fn_add:
        case md_expr_fn_sub:
        case md_expr_fn_mult:
            output( handle, -1, "((" );
            output_simulation_methods_expression( model, output, handle, code_block, expr->data.fn.args[0], main_indent, sub_indent+1 );
            if (expr->data.fn.fn==md_expr_fn_sub)       output( handle, -1, ")-(" );
            else if (expr->data.fn.fn==md_expr_fn_mult) output( handle, -1, ")*(" );
            else                                        output( handle, -1, ")+(" );
            output_simulation_methods_expression( model, output, handle, code_block, expr->data.fn.args[1], main_indent, sub_indent+1 );
            output( handle, -1, "))&%s", bit_mask[expr->width] );
            break;
        case md_expr_fn_and:
        case md_expr_fn_or:
        case md_expr_fn_xor:
        case md_expr_fn_bic:
        case md_expr_fn_logical_and:
        case md_expr_fn_logical_or:
        case md_expr_fn_eq:
        case md_expr_fn_neq:
        case md_expr_fn_ge:
        case md_expr_fn_gt:
        case md_expr_fn_le:
        case md_expr_fn_lt:
            output( handle, -1, "(" );
            output_simulation_methods_expression( model, output, handle, code_block, expr->data.fn.args[0], main_indent, sub_indent+1 );
            if (expr->data.fn.fn==md_expr_fn_and)
                output( handle, -1, ")&(" );
            else if (expr->data.fn.fn==md_expr_fn_or)
                output( handle, -1, ")|(" );
            else if (expr->data.fn.fn==md_expr_fn_xor)
                output( handle, -1, ")^(" );
            else if (expr->data.fn.fn==md_expr_fn_bic)
                output( handle, -1, ")&~(" );
            else if (expr->data.fn.fn==md_expr_fn_logical_and)
                output( handle, -1, ")&&(" );
            else if (expr->data.fn.fn==md_expr_fn_logical_or)
                output( handle, -1, ")||(" );
            else if (expr->data.fn.fn==md_expr_fn_eq)
                output( handle, -1, ")==(" );
            else if (expr->data.fn.fn==md_expr_fn_ge)
                output( handle, -1, ")>=(" );
            else if (expr->data.fn.fn==md_expr_fn_le)
                output( handle, -1, ")<=(" );
            else if (expr->data.fn.fn==md_expr_fn_gt)
                output( handle, -1, ")>(" );
            else if (expr->data.fn.fn==md_expr_fn_lt)
                output( handle, -1, ")<(" );
            else
                output( handle, -1, ")!=(" );
            output_simulation_methods_expression( model, output, handle, code_block, expr->data.fn.args[1], main_indent, sub_indent+1 );
            output( handle, -1, ")" );
            break;
        case md_expr_fn_query:
            output( handle, -1, "(" );
            output_simulation_methods_expression( model, output, handle, code_block, expr->data.fn.args[0], main_indent, sub_indent+1 );
            output( handle, -1, ")?(" );
            output_simulation_methods_expression( model, output, handle, code_block, expr->data.fn.args[1], main_indent, sub_indent+1 );
            output( handle, -1, "):(" );
            output_simulation_methods_expression( model, output, handle, code_block, expr->data.fn.args[2], main_indent, sub_indent+1 );
            output( handle, -1, ")" );
            break;
        default:
            output( handle, -1, "<unknown expression function type %d>", expr->data.fn.fn );
            break;
        }
        break;
    default:
        output( handle, -1, "<unknown expression type %d>", expr->type );
        break;
    }
}

/*f output_simulation_methods_statement_if_else
 */
static void output_simulation_methods_statement_if_else( c_model_descriptor *model, t_md_output_fn output, void *handle, t_md_code_block *code_block, t_md_statement *statement, int indent, t_md_signal *clock, int edge, t_md_type_instance *instance )
{
     if (statement->data.if_else.if_true)
     {
          output( handle, indent+1, "if (");
          output_simulation_methods_expression( model, output, handle, code_block, statement->data.if_else.expr, indent+1, 4 );
          output( handle, -1, ")\n");
          output( handle, indent+1, "{\n");
          output_simulation_methods_statement( model, output, handle, code_block, statement->data.if_else.if_true, indent+1, clock, edge, instance );
          output( handle, indent+1, "}\n");
          if  (statement->data.if_else.if_false)
          {
               output( handle, indent+1, "else\n");
               output( handle, indent+1, "{\n");
               output_simulation_methods_statement( model, output, handle, code_block, statement->data.if_else.if_false, indent+1, clock, edge, instance );
               output( handle, indent+1, "}\n");
          }
     }
     else if (statement->data.if_else.if_false)
     {
          output( handle, indent+1, "if (!(");
          output_simulation_methods_expression( model, output, handle, code_block, statement->data.if_else.expr, indent+1, 4 );
          output( handle, -1, "))\n");
          output( handle, indent+1, "{\n");
          output_simulation_methods_statement( model, output, handle, code_block, statement->data.if_else.if_false, indent+1, clock, edge, instance );
          output( handle, indent+1, "}\n");
     }
}

/*f output_simulation_methods_statement_parallel_switch
 */
static void output_simulation_methods_statement_parallel_switch( c_model_descriptor *model, t_md_output_fn output, void *handle, t_md_code_block *code_block, t_md_statement *statement, int indent, t_md_signal *clock, int edge, t_md_type_instance *instance )
{
    if (statement->data.switch_stmt.all_static && statement->data.switch_stmt.all_unmasked)
    {
        t_md_switch_item *switem;
        int defaulted = 0;

        output( handle, indent+1, "switch (");
        output_simulation_methods_expression( model, output, handle, code_block, statement->data.switch_stmt.expr, indent+1, 4 );
        output( handle, -1, ")\n");
        output( handle, indent+1, "{\n");
        for (switem = statement->data.switch_stmt.items; switem; switem=switem->next_in_list)
        {
            int stmts_reqd;
            stmts_reqd = 1;
            if (switem->statement)
            {
                if (clock && !model->reference_set_includes( &switem->statement->effects, clock, edge ))
                    stmts_reqd = 0;
                if (instance && !model->reference_set_includes( &switem->statement->effects, instance ))
                    stmts_reqd = 0;
            }

            if (switem->type == md_switch_item_type_static)
            {
                if (stmts_reqd || statement->data.switch_stmt.full || 1)
                {
                    output( handle, indent+1, "case 0x%x: // req %d\n", switem->data.value.value.value[0], stmts_reqd );
                    if (switem->statement)
                        output_simulation_methods_statement( model, output, handle, code_block, switem->statement, indent+1, clock, edge, instance );
                    output( handle, indent+2, "break;\n");
                }
            }
            else if (switem->type == md_switch_item_type_default)
            {
                if (stmts_reqd || statement->data.switch_stmt.full)
                {
                    output( handle, indent+1, "default: // req %d\n", stmts_reqd);
                    if (switem->statement)
                        output_simulation_methods_statement( model, output, handle, code_block, switem->statement, indent+1, clock, edge, instance );
                    output( handle, indent+2, "break;\n");
                    defaulted = 1;
                }
            }
            else
            {
                fprintf( stderr, "BUG - non static unmasked case item in parallel static unmasked switch C output\n" );
            }
        }
        if (!defaulted && statement->data.switch_stmt.full)
        {
            char buffer[512];
            model->client_string_from_reference_fn( model->client_handle,
                                                    statement->client_ref.base_handle,
                                                    statement->client_ref.item_handle,
                                                    statement->client_ref.item_reference,
                                                    buffer,
                                                    sizeof(buffer),
                                                    md_client_string_type_human_readable );
            output( handle, indent+1, "default:\n");
            output( handle, indent+2, "ASSERT_STRING(\"%s:Full switch statement did not cover all values\");\n", buffer );
            output( handle, indent+2, "break;\n");
        }
        output( handle, indent+1, "}\n");
    }
    else
    {
        output( handle, indent, "!!!PARALLEL SWITCH ONLY WORKS NOW FOR STATIC UNMASKED EXPRESSIONS\n");
    }
}

/*f output_simulation_methods_port_net_assignment
 */
static void output_simulation_methods_port_net_assignment( c_model_descriptor *model, t_md_output_fn output, void *handle, t_md_code_block *code_block, int indent, t_md_module_instance *module_instance, t_md_lvar *lvar, t_md_type_instance *port_instance )
{
    switch (lvar->instance->type)
    {
    case md_type_instance_type_bit_vector:
    case md_type_instance_type_array_of_bit_vectors:
        if (lvar->instance->size<=MD_BITS_PER_UINT64)
        {
            //printf("output_simulation_methods_port_net_assignment: %s.%s: type %d lvar %p\n", module_instance->name, port_instance->output_name, lvar->subscript_start.type, lvar );
            switch (lvar->subscript_start.type)
            {
            case md_lvar_data_type_none:
                output( handle, indent+1, "" );
                output_simulation_methods_lvar( model, output, handle, code_block, lvar, indent, indent+1, 0 );
                output( handle, -1, " = instance_%s.outputs.%s[0];\n", module_instance->name, port_instance->output_name );
                break;
            case md_lvar_data_type_integer:
                if (lvar->subscript_length.type == md_lvar_data_type_none)
                {
                    output( handle, indent+1, "ASSIGN_TO_BIT( &( " );
                    output_simulation_methods_lvar( model, output, handle, code_block, lvar, indent, indent+1, 0 );
                    output( handle, -1, "), %d, %d, ", lvar->instance->type_def.data.width, lvar->subscript_start.data.integer );
                }
                else
                {
                    output( handle, indent+1, "ASSIGN_TO_BIT_RANGE( &(" );
                    output_simulation_methods_lvar( model, output, handle, code_block, lvar, indent, indent+1, 0 );
                    output( handle, -1, "), %d, %d, %d, ", lvar->instance->type_def.data.width, lvar->subscript_start.data.integer, lvar->subscript_length.data.integer );
                }
                output( handle, -1, "instance_%s.outputs.%s[0]", module_instance->name, port_instance->output_name );
                output( handle, -1, ");\n" );
                break;
            case md_lvar_data_type_expression:
                if (lvar->subscript_length.type == md_lvar_data_type_none)
                {
                    output( handle, indent+1, "ASSIGN_TO_BIT( &(");
                    output_simulation_methods_lvar( model, output, handle, code_block, lvar, indent, indent+1, 0 );
                    output( handle, -1, "), %d, ", lvar->instance->type_def.data.width );
                    output_simulation_methods_expression( model, output, handle, code_block, lvar->subscript_start.data.expression, indent+1, 0 );
                    output( handle, -1, ", " );
                }
                else
                {
                    output( handle, indent+1, "ASSIGN_TO_BIT_RANGE( &(" );
                    output_simulation_methods_lvar( model, output, handle, code_block, lvar, indent, indent+1, 0 );
                    output( handle, -1, "), %d, ", lvar->instance->type_def.data.width );
                    output_simulation_methods_expression( model, output, handle, code_block, lvar->subscript_start.data.expression, indent+1, 0 );
                    output( handle, -1, ", %d,", lvar->subscript_length.data.integer );
                }
                output( handle, -1, "instance_%s.outputs.%s[0]", module_instance->name, port_instance->output_name );
                output( handle, -1, ");\n" );
                break;
            }
        }
        else
        {
            output( handle, indent, "TYPES AND VALUES WIDER THAN 64 NOT IMPLEMENTED YET\n" );
        }
        break;
    case md_type_instance_type_structure:
        if (lvar->subscript_start.type != md_lvar_data_type_none)
        {
            output( handle, indent, "SUBSCRIPT INTO ASSIGNMENT DOES NOT WORK\n" );
        }
        output( handle, indent, "STRUCTURE ASSIGNMENT %p NOT IMPLEMENTED YET\n", lvar );
        break;
    }
}

/*f output_simulation_methods_assignment
 */
static void output_simulation_methods_assignment( c_model_descriptor *model, t_md_output_fn output, void *handle, t_md_code_block *code_block, int indent, t_md_lvar *lvar, int clocked, t_md_expression *expr )
{
    switch (lvar->instance->type)
    {
    case md_type_instance_type_bit_vector:
    case md_type_instance_type_array_of_bit_vectors:
        if (lvar->instance->size<=MD_BITS_PER_UINT64)
        {
            switch (lvar->subscript_start.type)
            {
            case md_lvar_data_type_none:
                output( handle, indent+1, "" );
                output_simulation_methods_lvar( model, output, handle, code_block, lvar, indent, indent+1, 0 );
                output( handle, -1, " = " );
                output_simulation_methods_expression( model, output, handle, code_block, expr, indent+1, 0 );
                output( handle, -1, ";\n" );
                break;
            case md_lvar_data_type_integer:
                if (lvar->subscript_length.type == md_lvar_data_type_none)
                {
                    output( handle, indent+1, "ASSIGN_TO_BIT( &( " );
                    output_simulation_methods_lvar( model, output, handle, code_block, lvar, indent, indent+1, 0 );
                    output( handle, -1, "), %d, %d, ", lvar->instance->type_def.data.width, lvar->subscript_start.data.integer );
                }
                else
                {
                    output( handle, indent+1, "ASSIGN_TO_BIT_RANGE( &(" );
                    output_simulation_methods_lvar( model, output, handle, code_block, lvar, indent, indent+1, 0 );
                    output( handle, -1, "), %d, %d, %d, ", lvar->instance->type_def.data.width, lvar->subscript_start.data.integer, lvar->subscript_length.data.integer );
                }
                output_simulation_methods_expression( model, output, handle, code_block, expr, indent+1, 0 );
                output( handle, -1, ");\n" );
                break;
            case md_lvar_data_type_expression:
                if (lvar->subscript_length.type == md_lvar_data_type_none)
                {
                    output( handle, indent+1, "ASSIGN_TO_BIT( &(");
                    output_simulation_methods_lvar( model, output, handle, code_block, lvar, indent, indent+1, 0 );
                    output( handle, -1, "), %d, ", lvar->instance->type_def.data.width );
                    output_simulation_methods_expression( model, output, handle, code_block, lvar->subscript_start.data.expression, indent+1, 0 );
                    output( handle, -1, ", " );
                }
                else
                {
                    output( handle, indent+1, "ASSIGN_TO_BIT_RANGE( &(" );
                    output_simulation_methods_lvar( model, output, handle, code_block, lvar, indent, indent+1, 0 );
                    output( handle, -1, "), %d, ", lvar->instance->type_def.data.width );
                    output_simulation_methods_expression( model, output, handle, code_block, lvar->subscript_start.data.expression, indent+1, 0 );
                    output( handle, -1, ", %d,", lvar->subscript_length.data.integer );
                }
                output_simulation_methods_expression( model, output, handle, code_block, expr, indent+1, 0 );
                output( handle, -1, ");\n" );
                break;
            }
        }
        else
        {
            output( handle, indent, "TYPES AND VALUES WIDER THAN 64 NOT IMPLEMENTED YET\n" );
        }
        break;
    case md_type_instance_type_structure:
        if (lvar->subscript_start.type != md_lvar_data_type_none)
        {
            output( handle, indent, "SUBSCRIPT INTO ASSIGNMENT DOES NOT WORK\n" );
        }
        output( handle, indent, "STRUCTURE ASSIGNMENT %p NOT IMPLEMENTED YET\n", lvar );
        break;
    }
}

/*f output_simulation_methods_display_message_to_buffer
 */
static void output_simulation_methods_display_message_to_buffer( c_model_descriptor *model, t_md_output_fn output, void *handle, t_md_code_block *code_block, t_md_statement *statement, int indent, t_md_message *message, const char *buffer_name )
{
    if (message)
    {
        int i;
        t_md_expression *expr;
        char buffer[512];
        model->client_string_from_reference_fn( model->client_handle,
                                                 statement->client_ref.base_handle,
                                                 statement->client_ref.item_handle,
                                                 statement->client_ref.item_reference,
                                                 buffer,
                                                 sizeof(buffer),
                                                 md_client_string_type_human_readable );
        for (i=0, expr=message->arguments; expr; i++, expr=expr->next_in_chain);
        output( handle, indent+1, "se_cmodel_assist_vsnprintf( %s, sizeof(%s), \"%s:%s\", %d \n", buffer_name, buffer_name, buffer, message->text, i );
        for (expr=message->arguments; expr; expr=expr->next_in_chain)
        {
            output( handle, indent+2, "," );
            output_simulation_methods_expression( model, output, handle, code_block, expr, indent+2, 0 );
            output( handle, -1, "\n" );
        }
        output( handle, indent+2, " );\n");
    }
}

/*f output_simulation_methods_statement_print_assert_cover
 */
static void output_simulation_methods_statement_print_assert_cover( c_model_descriptor *model, t_md_output_fn output, void *handle, t_md_code_block *code_block, t_md_statement *statement, int indent, t_md_signal *clock, int edge, t_md_type_instance *instance )
{
    const char *string_type = (statement->type==md_statement_type_cover)?"COVER":"ASSERT";
    if ((!clock) && (!statement->data.print_assert_cover.statement))
    {
        return; // If there is no code to run, just a string to display, then only insert code for a clocked process, as the display is on the clock edge
    }
    /*b Handle cover expressions - Note that if cover has an expression, it does NOT have a statement, but it might have a message (though they are optional)
     */
    if ((statement->type==md_statement_type_cover) && statement->data.print_assert_cover.expression && !statement->data.print_assert_cover.statement)
    {
        t_md_expression *expr;
        int i;
        expr = statement->data.print_assert_cover.value_list;
        i = 0;
        do
        {
            output( handle, indent+1, "COVER_CASE_START(%d,%d) ", statement->data.print_assert_cover.cover_case_entry, i );
            output_simulation_methods_expression( model, output, handle, code_block, statement->data.print_assert_cover.expression, indent+2, 0 );
            if (expr)
            {
                output( handle, -1, "==" );
                output_simulation_methods_expression( model, output, handle, code_block, expr, indent+2, 0 );
                output( handle, -1, "\n" );
                expr = expr->next_in_chain;
            }
            output( handle, indent+2, "COVER_CASE_MESSAGE(%d,%d)\n", statement->data.print_assert_cover.cover_case_entry, i );
            output( handle, indent+2, "char buffer[512], buffer2[512];\n");
            output_simulation_methods_display_message_to_buffer( model, output, handle, code_block, statement, indent+2, statement->data.print_assert_cover.message, "buffer" );
            output( handle, indent+2, "snprintf( buffer2, sizeof(buffer2), \"Cover case entry %d subentry %d hit: %%s\", buffer);\n", statement->data.print_assert_cover.cover_case_entry, i );
            output( handle, indent+2, "COVER_STRING(buffer2)\n");
            output( handle, indent+2, "COVER_CASE_END\n" );
            i++;
        } while (expr);
        return;
    }

    /*b Handle assert expressions - either a message or a statement will follow
    */
    if (statement->data.print_assert_cover.expression)
    {
        output( handle, indent+1, "ASSERT_START " );
        if (statement->data.print_assert_cover.value_list)
        {
            t_md_expression *expr;
            expr = statement->data.print_assert_cover.value_list;
            while (expr)
            {
                output_simulation_methods_expression( model, output, handle, code_block, statement->data.print_assert_cover.expression, indent+2, 0 );
                output( handle, -1, "==" );
                output_simulation_methods_expression( model, output, handle, code_block, expr, indent+2, 0 );
                output( handle, -1, "\n" );
                expr = expr->next_in_chain;
                if (expr)
                {
                    output( handle, indent+2, "ASSERT_COND_NEXT " );
                }
            }
        }
        else
        {
            output_simulation_methods_expression( model, output, handle, code_block, statement->data.print_assert_cover.expression, indent+2, 0 );
        }
        output( handle, indent+1, "ASSERT_COND_END\n" );
    }
    else
    {
        output( handle, indent+1, "%s_START_UNCOND ", string_type );
    }
    if (clock && statement->data.print_assert_cover.message)
    {
        output( handle, indent+2, "char buffer[512];\n");
        output_simulation_methods_display_message_to_buffer( model, output, handle, code_block, statement, indent+2, statement->data.print_assert_cover.message, "buffer" );
        if (statement->data.print_assert_cover.expression) // Assertions have an expression, prints do not
        {
            output( handle, indent+2, "ASSERT_STRING(buffer)\n");
        }
        else
        {
            output( handle, indent+2, "PRINT_STRING(buffer)\n");
        }
    }
    if (statement->data.print_assert_cover.statement)
    {
        output_simulation_methods_statement( model, output, handle, code_block, statement->data.print_assert_cover.statement, indent+1, clock, edge, instance );
    }
    output( handle, indent+1, "%s_END\n", string_type );
}

/*f output_simulation_methods_statement_log
 */
static void output_simulation_methods_statement_log( c_model_descriptor *model, t_md_output_fn output, void *handle, t_md_code_block *code_block, t_md_statement *statement, int indent, t_md_signal *clock, int edge, t_md_type_instance *instance )
{
    t_md_labelled_expression *arg;
    int i;

    /*b At present, nothing to do unless clocked
     */
    if (!clock)
    {
        return;
    }
    /*b Set data for the occurrence from expressions, then hit the event
    */
    for (arg=statement->data.log.arguments, i=0; arg; arg=arg->next_in_chain, i++)
    {
        if (arg->expression)
        {
            output( handle, indent+1, "log_signal_data[%d] = ", statement->data.log.arg_id_within_module+i );
            output_simulation_methods_expression( model, output, handle, code_block, arg->expression, indent+2, 0 );
            output( handle, -1, ";\n" );
        }
    }
    /*b Invoke event occurrence
    */
    output( handle, indent+1, "engine->log_event_occurred( engine_handle, log_event_array, %d );\n", statement->data.log.id_within_module ); 
}

/*f output_simulation_methods_statement_clocked
 */
static void output_simulation_methods_statement_clocked( c_model_descriptor *model, t_md_output_fn output, void *handle, t_md_code_block *code_block, t_md_statement *statement, int indent, t_md_signal *clock, int edge )
{
    if (!statement)
        return;

    /*b If the statement does not effect this clock/edge, then return with outputting nothing
     */
    if (!model->reference_set_includes( &statement->effects, clock, edge ))
    {
        output_simulation_methods_statement_clocked( model, output, handle, code_block, statement->next_in_code, indent, clock, edge );
        return;
    }

    /*b Increment coverage
     */
    output( handle, indent+1, "COVER_STATEMENT(%d);\n", statement->enumeration );

    /*b Display the statement
     */
    switch (statement->type)
    {
    case md_statement_type_state_assign:
    {
        output_simulation_methods_assignment( model, output, handle, code_block, indent, statement->data.state_assign.lvar, 1, statement->data.state_assign.expr );
        break;
    }
    case md_statement_type_comb_assign:
        break;
    case md_statement_type_if_else:
        output_simulation_methods_statement_if_else( model, output, handle, code_block, statement, indent, clock, edge, NULL );
        break;
    case md_statement_type_parallel_switch:
        output_simulation_methods_statement_parallel_switch( model, output, handle, code_block, statement, indent, clock, edge, NULL );
        break;
    case md_statement_type_print_assert:
    case md_statement_type_cover:
        output_simulation_methods_statement_print_assert_cover( model, output, handle, code_block, statement, indent, clock, edge, NULL );
        break;
    case md_statement_type_log:
        output_simulation_methods_statement_log( model, output, handle, code_block, statement, indent, clock, edge, NULL );
        break;
    default:
        output( handle, 1, "Unknown statement type %d\n", statement->type );
        break;
    }
    output_simulation_methods_statement_clocked( model, output, handle, code_block, statement->next_in_code, indent, clock, edge );
}

/*f output_simulation_methods_statement_combinatorial
 */
static void output_simulation_methods_statement_combinatorial( c_model_descriptor *model, t_md_output_fn output, void *handle, t_md_code_block *code_block, t_md_statement *statement, int indent, t_md_type_instance *instance )
{
     if (!statement)
          return;

     /*b If the statement does not effect this signal instance, then return with outputting nothing
      */
     if (!model->reference_set_includes( &statement->effects, instance ))
     {
          output_simulation_methods_statement_combinatorial( model, output, handle, code_block, statement->next_in_code, indent, instance );
          return;
     }

     /*b Increment coverage
      */
     output( handle, indent+1, "COVER_STATEMENT(%d);\n", statement->enumeration );

     /*b Display the statement
      */
     switch (statement->type)
     {
     case md_statement_type_state_assign:
          break;
     case md_statement_type_comb_assign:
        output_simulation_methods_assignment( model, output, handle, code_block, indent, statement->data.comb_assign.lvar, 0, statement->data.comb_assign.expr );
        break;
     case md_statement_type_if_else:
          output_simulation_methods_statement_if_else( model, output, handle, code_block, statement, indent, NULL, -1, instance );
          break;
     case md_statement_type_parallel_switch:
          output_simulation_methods_statement_parallel_switch( model, output, handle, code_block, statement, indent, NULL, -1, instance );
          break;
    case md_statement_type_print_assert:
    case md_statement_type_cover:
        output_simulation_methods_statement_print_assert_cover( model, output, handle, code_block, statement, indent, NULL, -1, instance );
        break;
     case md_statement_type_log:
        output_simulation_methods_statement_log( model, output, handle, code_block, statement, indent, NULL, -1, instance );
        break;
     default:
          output( handle, 1, "Unknown statement type %d\n", statement->type );
          break;
     }
     output_simulation_methods_statement_combinatorial( model, output, handle, code_block, statement->next_in_code, indent, instance );
}

/*f output_simulation_methods_statement
 */
static void output_simulation_methods_statement( c_model_descriptor *model, t_md_output_fn output, void *handle, t_md_code_block *code_block, t_md_statement *statement, int indent, t_md_signal *clock, int edge, t_md_type_instance *instance )
{
    if (clock)
    {
        output_simulation_methods_statement_clocked( model, output, handle, code_block, statement, indent, clock, edge );
    }
            else
    {
        output_simulation_methods_statement_combinatorial( model, output, handle, code_block, statement, indent, instance );
    }
}

/*f output_simulation_methods_code_block
 */
static void output_simulation_methods_code_block( c_model_descriptor *model, t_md_output_fn output, void *handle, t_md_code_block *code_block, t_md_signal *clock, int edge, t_md_type_instance *instance )
{
     /*b If the code block does not effect this signal/clock/edge, then return with outputting nothing
      */
     if (clock && !model->reference_set_includes( &code_block->effects, clock, edge ))
          return;
     if (instance && !model->reference_set_includes( &code_block->effects, instance ))
          return;

     /*b Insert comment for the block
      */
     if (instance)
          output( handle, 1, "/*b %s : %s\n", instance->name, code_block->name );
     else
          output( handle, 1, "/*b %s\n", code_block->name );
     output( handle, 1, "*/\n" );

     /*b Display each statement that effects state on the specified clock
      */
     output_simulation_methods_statement( model, output, handle, code_block, code_block->first_statement, 0, clock, edge, instance );

     /*b Close out with a blank line
      */
     output( handle, 0, "\n" );
}

/*f output_simulation_methods
 */
static void output_simulation_methods( c_model_descriptor *model, t_md_module *module, t_md_output_fn output, void *handle )
{
    int edge, level;
    t_md_signal *clk;
    t_md_signal *signal;
    t_md_state *reg;
    t_md_code_block *code_block;
    t_md_type_instance *instance;
    t_md_module_instance *module_instance;
    t_md_module_instance_clock_port *clock_port;
    t_md_reference_iter iter;
    t_md_reference *reference;
    t_md_type_instance *dependency;
    t_md_module_instance_input_port *input_port;
    t_md_module_instance_output_port *output_port;
    int i;
    int more_to_output, did_output;

    /*b Output the main reset function
     */
    output( handle, 0, "/*a Class reset/preclock/clock methods for %s\n", module->output_name );
    output( handle, 0, "*/\n");
    output( handle, 0, "/*f c_%s::reset\n", module->output_name );
    output( handle, 0, "*/\n");
    output( handle, 0, "t_sl_error_level c_%s::reset( int pass )\n", module->output_name );
    output( handle, 0, "{\n");

    for (signal=module->inputs; signal; signal=signal->next_in_list)
    {
        for (level=0; level<2; level++)
        {
            if (signal->data.input.levels_used_for_reset[level])
            {
                output( handle, 1, "reset_%s_%s( );\n", level_name[level], signal->name );
            }
        }
    }
    output( handle, 1, "if (pass==0)\n" );
    output( handle, 2, "{\n" );
    output( handle, 2, "int unconnected_inputs; unconnected_inputs=0;\n");
    output( handle, 2, "int unconnected_nets; unconnected_nets=0;\n");
    for (signal=module->inputs; signal; signal=signal->next_in_list)
    {
        for (i=0; i<signal->instance_iter->number_children; i++)
        {
            instance = signal->instance_iter->children[i];
            output( handle, 2, "if (!inputs.%s) {DEFINE_DUMMY_INPUT;fprintf(stderr,\"POSSIBLY FATAL:Unconnected input %s on module %s at initial reset\\n\");unconnected_inputs=1;inputs.%s=&dummy_input[0];}\n", instance->output_name, instance->output_name, module->output_name, instance->output_name );
        }
    }
    for (signal=module->nets; signal; signal=signal->next_in_list)
    {
        for (i=0; i<signal->instance_iter->number_children; i++)
        {
            instance = signal->instance_iter->children[i];
            if (!instance->driven_in_parts)
            {
                output( handle, 2, "if (!nets.%s) {DEFINE_DUMMY_INPUT;fprintf(stderr,\"POSSIBLY FATAL:Unconnected input %s on module %s at initial reset\\n\");unconnected_nets=1;nets.%s=&dummy_input[0];}\n", instance->output_name, instance->output_name, module->output_name, instance->output_name );
            }
        }
    }
    output( handle, 2, "}\n");
    output( handle, 1, "if (pass>0) {capture_inputs(); propagate_inputs(); propagate_state();} // Dont call capture_inputs on first pass as they may be invalid; wait for second pass\n");
    for (module_instance=module->module_instances; module_instance; module_instance=module_instance->next_in_list)
    {
        output( handle, 1, "engine->submodule_call_reset( instance_%s.handle, pass );\n", module_instance->name );
        if (module_instance->module_definition)
        {
            t_md_module_instance_output_port *output_port;
            for (output_port=module_instance->outputs; output_port; output_port=output_port->next_in_list)
            {
                if (output_port->lvar->instance->driven_in_parts)
                {
                    output_simulation_methods_port_net_assignment( model, output, handle, NULL, 1, module_instance, output_port->lvar, output_port->module_port_instance );
                }
            }
        }
    }

    output( handle, 1, "return error_level_okay;\n");
    output( handle, 0, "}\n");
    output( handle, 0, "\n");

    /*b Output the individual reset functions
     */
    for (signal=module->inputs; signal; signal=signal->next_in_list)
    {
        for (level=0; level<2; level++)
        {
            if (signal->data.input.levels_used_for_reset[level])
            {
                output( handle, 0, "/*f c_%s::reset_%s_%s\n", module->output_name, level_name[level], signal->name );
                output( handle, 0, "*/\n");
                output( handle, 0, "t_sl_error_level c_%s::reset_%s_%s( void )\n", module->output_name, level_name[level], signal->name );
                output( handle, 0, "{\n");

                for (clk=module->clocks; clk; clk=clk->next_in_list)
                {
                    for (edge=0; edge<2; edge++)
                    {
                        if (clk->data.clock.edges_used[edge])
                        {
                            for (reg=module->registers; reg; reg=reg->next_in_list)
                            {
                                if ( (reg->clock_ref==clk) && (reg->edge==edge) && (reg->reset_ref=signal) && (reg->reset_level==level))
                                {
                                    for (i=0; i<reg->instance_iter->number_children; i++)
                                    {
                                        int j, array_size;
                                        t_md_type_instance_data *ptr;
                                        instance = reg->instance_iter->children[i];
                                        array_size = instance->size;
                                        for (j=0; j<(array_size>0?array_size:1); j++)
                                        {
                                            for (ptr = &instance->data[j]; ptr; ptr=ptr->reset_value.next_in_list)
                                            {
                                                if (ptr->reset_value.expression)
                                                {
                                                    if (ptr->reset_value.subscript_start>=0)
                                                    {
                                                        output( handle, 1, "ASSIGN_TO_BIT( &( " );
                                                    }
                                                    if (array_size>1)
                                                    {
                                                        output( handle, 1, "%s_%s_state.%s[%d]", edge_name[reg->edge], reg->clock_ref->name, instance->output_name, j );
                                                    }
                                                    else
                                                    {
                                                        output( handle, 1, "%s_%s_state.%s", edge_name[reg->edge], reg->clock_ref->name, instance->output_name );
                                                    }
                                                    if (ptr->reset_value.subscript_start>=0)
                                                    {
                                                        output( handle, -1, "), %d, %d, ", instance->type_def.data.width, ptr->reset_value.subscript_start );
                                                        output_simulation_methods_expression( model, output, handle, NULL, ptr->reset_value.expression, 2, 0 );
                                                        output( handle, -1, ");\n" );
                                                    }
                                                    else
                                                    {
                                                        output( handle, -1, " = " );
                                                        output_simulation_methods_expression( model, output, handle, NULL, ptr->reset_value.expression, 2, 0 );
                                                        output( handle, -1, ";\n" );
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                output( handle, 1, "return error_level_okay;\n");
                output( handle, 0, "}\n");
                output( handle, 0, "\n");
            }
        }
    }

    /*b Output the function to capture inputs
     */
    output( handle, 0, "/*f c_%s::capture_inputs\n", module->output_name );
    output( handle, 0, "*/\n");
    output( handle, 0, "t_sl_error_level c_%s::capture_inputs( void )\n", module->output_name );
    output( handle, 0, "{\n");
    for (signal=module->inputs; signal; signal=signal->next_in_list)
    {
        for (i=0; i<signal->instance_iter->number_children; i++)
        {
            instance = signal->instance_iter->children[i];
            output( handle, 1, "input_state.%s = inputs.%s[0];\n", instance->output_name, instance->output_name );
        }
    }
    output( handle, 1, "return error_level_okay;\n");
    output( handle, 0, "}\n");

    /*b Output the function to propagate inputs/state to internal combs, through submodules, and through again to submodule inputs
      This function currently assumes all inputs could have changed and so can all internal state and submodule outputs
      In the future this function could be split in to more, each dependent on a subset of those
      Note that if a submodule is combinatorial AND clocked, then there may be a situation where:
        input -> sub.a_in -> sub.b_out -> logic -> sub.c_in; i.e. the c_in for the submodule has to be set AFTER the submodule is called as well as before
     */
    output( handle, 0, "/*f c_%s::propagate_inputs\n", module->output_name );
    output( handle, 0, "*/\n");
    output( handle, 0, "t_sl_error_level c_%s::propagate_inputs( void )\n", module->output_name );
    output( handle, 0, "{\n");

    /*b Handle asynchronous reset
     */
    for (signal=module->inputs; signal; signal=signal->next_in_list)
    {
        for (level=0; level<2; level++)
        {
            if (signal->data.input.levels_used_for_reset[level])
            {
                output( handle, 1, "if (inputs.%s[0]==%d)\n", signal->name, level );
                output( handle, 1, "{\n");
                output( handle, 2, "reset_%s_%s();\n", level_name[level], signal->name );
                output( handle, 1, "}\n");
            }
        }
    }

    /*b   First clear the state we have in the combinatorials and nets. We will use this to indicate whether we have output the code for a signal
          But note that nets that are not generated combinatorially can be marked as already output
     */
    for (signal=module->combinatorials; signal; signal=signal->next_in_list)
    {
        for (i=0; i<signal->instance_iter->number_children; i++)
        {
            instance = signal->instance_iter->children[i];
            instance->output_handle = NULL;
            instance->output_args[0] = 0;
        }
    }
    for (signal=module->nets; signal; signal=signal->next_in_list)
    {
        for (i=0; i<signal->instance_iter->number_children; i++)
        {
            instance = signal->instance_iter->children[i];
            instance->output_handle = NULL;
            instance->output_args[0] = !instance->derived_combinatorially; // Needs to be output only if it is combinatorial
        }
    }
    for (module_instance=module->module_instances; module_instance; module_instance=module_instance->next_in_list)
    {
        module_instance->output_args[0] = 0;
    }

    /*b   Assign outputs of every submodule that is clocked
     */
    for (module_instance=module->module_instances; module_instance; module_instance=module_instance->next_in_list)
    {
        /*b If module_instance is not combinatorial or has been done, skip to next - NOTE WE CURRENTLY DO IT FOR ALL MODULES
         */
        if ( (!module_instance->module_definition) ||
             (0 && module_instance->module_definition->combinatorial_component) ) // Do it for every submodule output and then a part-comb, part-clocked module will have outputs it drives correct also - no need if PURELY comb
        {
            continue;
        }

        t_md_module_instance_output_port *output_port;
        for (output_port=module_instance->outputs; output_port; output_port=output_port->next_in_list)
        {
            if (output_port->lvar->instance->driven_in_parts)
            {
                output_simulation_methods_port_net_assignment( model, output, handle, NULL, 1, module_instance, output_port->lvar, output_port->module_port_instance );
            }
        }
    }

    /*b   Run through combinatorials and nets to see if we can output the code or module instances for one (are all its dependencies done?) - and repeat until we have nothing left
     */
    more_to_output = 1;
    did_output = 1;
    while (more_to_output && did_output)
    {
        /*b Mark us as done nothing yet
         */
        more_to_output = 0;
        did_output = 0;

        /*b Check for combinatorials that have not been done and are ready
         */
        for (signal=module->combinatorials; signal; signal=signal->next_in_list)
        {
            for (i=0; i<signal->instance_iter->number_children; i++)
            {
                /*b If instance has been done, skip to next
                 */
                instance = signal->instance_iter->children[i];
                if (instance->output_args[0] & 1)
                {
                    continue;
                }

                /*b Check dependencies (net and combinatorial) are all done
                 */
                model->reference_set_iterate_start( &instance->dependencies, &iter );
                while ((reference = model->reference_set_iterate(&iter))!=NULL)
                {
                    dependency = reference->data.instance;
                    if ( (dependency->reference.type==md_reference_type_signal) &&
                         ( (dependency->reference.data.signal->type==md_signal_type_combinatorial) ||
                           (dependency->reference.data.signal->type==md_signal_type_net) ) &&
                         (dependency->reference.data.signal!=signal) && // Added so self-dependent signals do get output
                         (dependency->output_args[0]==0) )
                    {
                        break;
                    }
                }
                if (reference) // unsatisfied dependency
                {
                    more_to_output=1;
                    continue;
                }

                /*b Dependencies are all done; mark as done too, and output the code
                 */
                did_output=1;
                instance->output_args[0] |= 1;

                if (!instance->code_block)
                {
                    output( handle, 1, "//No definition of signal %s (%p)\n", instance->name, instance);
                    //break;
                }
                else
                {
                    output_simulation_methods_code_block( model, output, handle, instance->code_block, NULL, -1, instance );
                }

                /*b Next instance
                 */
            }
        }

        /*b Check all module instances which have not been done and are ready
         */
        for (module_instance=module->module_instances; module_instance; module_instance=module_instance->next_in_list)
        {
            /*b If module_instance is not combinatorial or has been done, skip to next
             */
            if ( (!module_instance->module_definition) ||
                 (!module_instance->module_definition->combinatorial_component) ||
                 (module_instance->output_args[0] & 1) )
            {
                continue;
            }

            /*b Check dependencies (net and combinatorial) for combinatorial function are all done
             */
            model->reference_set_iterate_start( &module_instance->combinatorial_dependencies, &iter );
            while ((reference = model->reference_set_iterate(&iter))!=NULL)
            {
                dependency = reference->data.instance;
                if ( (dependency->reference.type==md_reference_type_signal) &&
                     ( (dependency->reference.data.signal->type==md_signal_type_combinatorial) ||
                           (dependency->reference.data.signal->type==md_signal_type_net) ) &&
                     (dependency->output_args[0]==0) )
                {
                    break;
                }
            }
            if (reference)
            {
                more_to_output=1;
                continue;
            }
        
            /*b Dependencies are all done; mark as done too, and output the code, and mark output nets as done
             */
            did_output=1;
            module_instance->output_args[0] |= 1;
            for (input_port=module_instance->inputs; input_port; input_port=input_port->next_in_list)
            {
                if (1||input_port->module_port_instance->reference.data.signal->data.input.used_combinatorially)
                {
                    output( handle, 1, "instance_%s.inputs.%s = ", module_instance->name, input_port->module_port_instance->output_name );
                    output_simulation_methods_expression( model, output, handle, NULL, input_port->expression, 2, 0 );
                    output( handle, -1, ";\n" );
                }
            }
            output( handle, 1, "engine->submodule_call_comb( instance_%s.handle );\n", module_instance->name );
            for (output_port=module_instance->outputs; output_port; output_port=output_port->next_in_list)
            {
                if (output_port->lvar->instance->driven_in_parts)
                {
                    output_simulation_methods_port_net_assignment( model, output, handle, NULL, 1, module_instance, output_port->lvar, output_port->module_port_instance );
                }
                if (output_port->module_port_instance->reference.data.signal->data.output.derived_combinatorially)
                {
                    output_port->lvar->instance->output_args[0] |= 1;
                }
            }

            /*b Next module instance
             */
        }
    }

    /*b Set inputs to all clocked modules EVEN IF THEY HAVE BEEN OUTPUT ALREADY
     */
    for (module_instance=module->module_instances; module_instance; module_instance=module_instance->next_in_list)
    {
        /*b If module_instance is not purely clocked then it has already been done
         */
        if ( (!module_instance->module_definition) )
        {
            continue;
        }

        /*b Set inputs
         */
        for (input_port=module_instance->inputs; input_port; input_port=input_port->next_in_list)
        {
            output( handle, 1, "instance_%s.inputs.%s = ", module_instance->name, input_port->module_port_instance->output_name );
            output_simulation_methods_expression( model, output, handle, NULL, input_port->expression, 2, 0 );
            output( handle, -1, ";\n" );
        }

        /*b Next module instance
         */
    }

    /*b More to output? If so, warn!
     */
    if (more_to_output)
    {
        /*b Warn about combinatorials that have not been done and are ready
         */
        for (signal=module->combinatorials; signal; signal=signal->next_in_list)
        {
            for (i=0; i<signal->instance_iter->number_children; i++)
            {
                /*b If instance has been done, skip to next
                 */
                instance = signal->instance_iter->children[i];
                if (instance->output_args[0] & 1)
                {
                    continue;
                }

                /*b Warn
                 */
                {
                    char buffer[256];
                    output( handle, 1, "//Combinatorial %s has code whose dependents seem cyclic\n", instance->name );
                    snprintf(buffer,sizeof(buffer),"DESIGN ERROR: circular dependency found for %s (depends on...):", instance->name );
                    model->reference_set_iterate_start( &instance->dependencies, &iter );
                    while ((reference = model->reference_set_iterate(&iter))!=NULL)
                    {
                        dependency = reference->data.instance;
                        if ( (dependency->reference.type==md_reference_type_signal) &&
                             ( (dependency->reference.data.signal->type==md_signal_type_combinatorial) ||
                               (dependency->reference.data.signal->type==md_signal_type_net) ) &&
                             (dependency->output_args[0]==0) )
                        {
                            output( handle, 1, "//    dependent '%s' not ready\n", dependency->reference.data.signal->name );
                            snprintf(buffer+strlen(buffer),sizeof(buffer)-strlen(buffer),"%s ", dependency->reference.data.signal->name );
                        }
                    }
                    buffer[sizeof(buffer)-1]=0;
                    model->error->add_error( module, error_level_fatal, error_number_sl_message, error_id_be_backend_message,
                                             error_arg_type_malloc_string, buffer,
                                             error_arg_type_malloc_filename, module->output_name,
                                             error_arg_type_none );
                }
            }
        }

        /*b Warn about all module instances which have not been done
         */
        for (module_instance=module->module_instances; module_instance; module_instance=module_instance->next_in_list)
        {
            /*b If module_instance is not combinatorial or has been done, skip to next
             */
//            output( handle, 1, "//Module instance %s has defn %p\n", module_instance->name, module_instance->module_definition );
//            output( handle, 1, "//Module instance %s is comb %d\n", module_instance->name, module_instance->module_definition->combinatorial_component );
//            output( handle, 1, "//Module instance %s has been output %d\n", module_instance->name, module_instance->output_args[0] );
            if ( (!module_instance->module_definition) ||
                 (!module_instance->module_definition->combinatorial_component) ||
                 (module_instance->output_args[0] & 1) )
            {
                continue;
            }

            /*b Warn
             */
            {
                char buffer[256];
                output( handle, 1, "//Module instance %s has dependents which seem cyclic\n", module_instance->name );

                snprintf(buffer,sizeof(buffer),"DESIGN ERROR: circular dependency found for module %s:", module_instance->name );
                model->error->add_error( module, error_level_info, error_number_sl_message, error_id_be_backend_message,
                                         error_arg_type_malloc_string, buffer,
                                         error_arg_type_malloc_filename, module->output_name,
                                         error_arg_type_none );
            }
        }
    }

    /*b   Finish
     */
    output( handle, 1, "return error_level_okay;\n");
    output( handle, 0, "}\n");
    output( handle, 0, "\n");

    /*b Output the function to propagate from state to outputs and internal combs, through submodules
     */
    output( handle, 0, "/*f c_%s::propagate_state\n", module->output_name );
    output( handle, 0, "*/\n");
    output( handle, 0, "t_sl_error_level c_%s::propagate_state( void )\n", module->output_name );
    output( handle, 0, "{\n");
    output( handle, 1, "return propagate_inputs();\n");
    output( handle, 0, "}\n");

    /*b Output the clocked functions
      On entry to preclocked the inputs to the module we are outputting are correct, and they should be captured
      On entry to the clocked function the recorded input state is valid
     */
    if (module->clocks)
    {
        output( handle, 0, "/*f c_%s::prepreclock\n", module->output_name );
        output( handle, 0, "*/\n");
        output( handle, 0, "t_sl_error_level c_%s::prepreclock( void )\n", module->output_name );
        output( handle, 0, "{\n");
        output( handle, 1, "WHERE_I_AM;\n");
        output( handle, 1, "inputs_captured=0;\n");
        output( handle, 1, "clocks_to_call=0;\n");
        output( handle, 1, "return error_level_okay;\n");
        output( handle, 0, "}\n\n");

        output( handle, 0, "/*f c_%s::preclock\n", module->output_name );
        output( handle, 0, "*/\n");
        output( handle, 0, "t_sl_error_level c_%s::preclock( t_c_%s_clock_callback_fn preclock, t_c_%s_clock_callback_fn clock )\n", module->output_name, module->output_name, module->output_name );
        output( handle, 0, "{\n");
        output( handle, 1, "WHERE_I_AM;\n");
        output( handle, 1, "if (!inputs_captured) { capture_inputs(); inputs_captured++; }\n" );
        output( handle, 1, "if (clocks_to_call>%d)\n", 16 );
        output( handle, 1, "{\n" );
        output( handle, 2, "fprintf(stderr,\"BUG - too many preclock calls after prepreclock\\n\");\n");
        output( handle, 1, "} else {\n" );
        output( handle, 2, "clocks_fired[clocks_to_call].preclock=preclock;\n");
        output( handle, 2, "clocks_fired[clocks_to_call].clock=clock;\n");
        output( handle, 2, "clocks_to_call++;\n");
        output( handle, 1, "}\n" );
        output( handle, 1, "return error_level_okay;\n" );
        output( handle, 0, "}\n");

        output( handle, 0, "/*f c_%s::clock\n", module->output_name );
        output( handle, 0, "*/\n");
        output( handle, 0, "t_sl_error_level c_%s::clock( void )\n", module->output_name );
        output( handle, 0, "{\n");
        output( handle, 1, "WHERE_I_AM;\n");
        output( handle, 1, "if (clocks_to_call>0)\n" );
        output( handle, 1, "{\n" );
        output( handle, 2, "propagate_inputs();\n" ); // At this point all submodules should have valid inputs
        // Prepreclock submodules
        for (module_instance=module->module_instances; module_instance; module_instance=module_instance->next_in_list)
        {
            output( handle, 2, "engine->submodule_call_prepreclock( instance_%s.handle );\n", module_instance->name );
        }
        output( handle, 2, "int i;\n" );
        // preclock submodules that depend on the clock - done in individual preclock functions
        output( handle, 2, "for (i=0; i<clocks_to_call; i++)\n" );
        output( handle, 3, "(this->*clocks_fired[i].preclock)();\n" );
        // clock submodules that depend on the clock - done in individual clock functions - their outputs will be valid after that
        output( handle, 2, "for (i=0; i<clocks_to_call; i++)\n" );
        output( handle, 3, "(this->*clocks_fired[i].clock)();\n" );
        output( handle, 1, "}\n" );
        output( handle, 1, "propagate_state();\n" );
        output( handle, 1, "clocks_to_call=0;\n");
        output( handle, 1, "return error_level_okay;\n");
        output( handle, 0, "}\n");
    }
    for (clk=module->clocks; clk; clk=clk->next_in_list)
    {
        for (edge=0; edge<2; edge++)
        {
            if (clk->data.clock.edges_used[edge])
            {
                // For clock_will_fire just need to record which functions to call
                // For a clock preclock function, inputs will already have been propagated, as will state, so only need to do 'next_state' functions - can fire log events too
                output( handle, 0, "/*f c_%s::preclock_%s_%s\n", module->output_name, edge_name[edge], clk->name );
                output( handle, 0, "*/\n");
                output( handle, 0, "t_sl_error_level c_%s::preclock_%s_%s( void )\n", module->output_name, edge_name[edge], clk->name );
                output( handle, 0, "{\n");
                output( handle, 1, "memcpy( &next_%s_%s_state, &%s_%s_state, sizeof(%s_%s_state) );\n", edge_name[edge], clk->name, edge_name[edge], clk->name, edge_name[edge], clk->name);

                // Output code for this clock for this module - effects next state only
                for (code_block = module->code_blocks; code_block; code_block=code_block->next_in_list)
                {
                    output_simulation_methods_code_block( model, output, handle, code_block, clk, edge, NULL );
                }

                // Preclock submodules using this clock
                for (module_instance=module->module_instances; module_instance; module_instance=module_instance->next_in_list)
                {
                    if (model->reference_set_includes( &module_instance->dependencies, clk, edge ))
                    {
                        for (clock_port=module_instance->clocks; clock_port; clock_port=clock_port->next_in_list)
                        {
                            if (clock_port->local_clock_signal==clk)
                            {
                                output( handle, 1, "engine->submodule_call_preclock( instance_%s.%s__clock_handle, %d );\n", module_instance->name, clock_port->port_name, edge==md_edge_pos );
                            }
                        }
                    }
                }

                // Determine clock gate enables for every gated version of this clock
                {
                    t_md_signal *clk2;
                    for (clk2=module->clocks; clk2; clk2=clk2->next_in_list)
                    {
                        if (clk2->data.clock.clock_ref == clk)
                        {
                            if (clk2->data.clock.edges_used[edge])
                            {
                                output( handle, 1, "clock_enable__%s_%s = ", edge_name[edge], clk2->name );
                                if (clk2->data.clock.gate_state)
                                {
                                    output( handle, -1, "(%s_%s_state.%s==%d);\n",
                                            edge_name[clk2->data.clock.gate_state->edge], clk2->data.clock.gate_state->clock_ref->name, clk2->data.clock.gate_state->name,
                                            clk2->data.clock.gate_level );
                                }
                                else
                                {
                                    output( handle, -1, "(combinatorials.%s==%d);\n", clk2->data.clock.gate_signal->name, clk2->data.clock.gate_level);
                                }
                            }
                        }
                    }

                // Call gated clocks 'preclock' functions
                {
                    t_md_signal *clk2;
                    for (clk2=module->clocks; clk2; clk2=clk2->next_in_list)
                    {
                        if (clk2->data.clock.clock_ref == clk)
                        {
                            if (clk2->data.clock.edges_used[edge])
                            {
                                output( handle, 1, "if (clock_enable__%s_%s)\n", edge_name[edge], clk2->name );
                                output( handle, 2, "preclock_%s_%s();\n", edge_name[edge], clk2->name );
                            }
                        }
                    }
                }


                }

                output( handle, 1, "return error_level_okay;\n");
                output( handle, 0, "}\n");
                output( handle, 0, "\n");

                output( handle, 0, "/*f c_%s::clock_%s_%s\n", module->output_name, edge_name[edge], clk->name );
                output( handle, 0, "*/\n");
                output( handle, 0, "t_sl_error_level c_%s::clock_%s_%s( void )\n", module->output_name, edge_name[edge], clk->name );
                output( handle, 0, "{\n");
                output( handle, 1, "memcpy( &%s_%s_state, &next_%s_%s_state, sizeof(%s_%s_state) );\n", edge_name[edge], clk->name, edge_name[edge], clk->name, edge_name[edge], clk->name);

                // Call submodules clock functions if they use this clock directly
                for (module_instance=module->module_instances; module_instance; module_instance=module_instance->next_in_list)
                {
                    if (model->reference_set_includes( &module_instance->dependencies, clk, edge ))
                    {
                        for (clock_port=module_instance->clocks; clock_port; clock_port=clock_port->next_in_list)
                        {
                            if (clock_port->local_clock_signal==clk)
                            {
                                output( handle, 1, "engine->submodule_call_clock( instance_%s.%s__clock_handle, %d );\n", module_instance->name, clock_port->port_name, edge==md_edge_pos );
                                if (module_instance->module_definition)
                                {
                                    t_md_module_instance_output_port *output_port;
                                    for (output_port=module_instance->outputs; output_port; output_port=output_port->next_in_list)
                                    {
                                        if (output_port->lvar->instance->driven_in_parts)
                                        {
                                            output_simulation_methods_port_net_assignment( model, output, handle, NULL, 1, module_instance, output_port->lvar, output_port->module_port_instance );
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                output( handle, 0, "\n");

                // Call gated clocks 'clock' functions
                {
                    t_md_signal *clk2;
                    for (clk2=module->clocks; clk2; clk2=clk2->next_in_list)
                    {
                        if (clk2->data.clock.clock_ref == clk)
                        {
                            if (clk2->data.clock.edges_used[edge])
                            {
                                output( handle, 1, "if (clock_enable__%s_%s)\n", edge_name[edge], clk2->name );
                                output( handle, 2, "clock_%s_%s();\n", edge_name[edge], clk2->name );
                            }
                        }
                    }
                }

                output( handle, 1, "return error_level_okay;\n");
                output( handle, 0, "}\n");
                output( handle, 0, "\n");
            }
        }
    }

}

/*f output_initalization_functions
 */
static void output_initalization_functions( c_model_descriptor *model, t_md_output_fn output, void *handle )
{
    t_md_module *module;
    output( handle, 0, "/*a Initialization functions\n");
    output( handle, 0, "*/\n");
    output( handle, 0, "/*f %s__init\n", model->get_name() );
    output( handle, 0, "*/\n");
    output( handle, 0, "extern void %s__init( void )\n", model->get_name() );
    output( handle, 0, "{\n");
    for (module=model->module_list; module; module=module->next_in_list)
    {
        if (module->external)
            continue;
        output( handle, 1, "se_external_module_register( 1, \"%s\", %s_instance_fn );\n", module->output_name, module->output_name );
    }
    output( handle, 0, "}\n");
    output( handle, 0, "\n");
    output( handle, 0, "/*a Scripting support code\n");
    output( handle, 0, "*/\n");
    output( handle, 0, "/*f init%s\n", model->get_name() );
    output( handle, 0, "*/\n");
    output( handle, 0, "extern \"C\" void init%s( void )\n", model->get_name() );
    output( handle, 0, "{\n");
    output( handle, 1, "%s__init( );\n", model->get_name() );
    output( handle, 1, "scripting_init_module( \"%s\" );\n", model->get_name() );
    output( handle, 0, "}\n");
}

/*a External functions
 */
/*f target_c_output
 */
extern void target_c_output( c_model_descriptor *model, t_md_output_fn output_fn, void *output_handle, int include_assertions, int include_coverage, int include_stmt_coverage )
{
    t_md_module *module;

    output_header( model, output_fn, output_handle );
    output_defines( model, output_fn, output_handle, include_assertions, include_coverage, include_stmt_coverage );
    for (module=model->module_list; module; module=module->next_in_list)
    {
        if (module->external)
            continue;

        output_types( model, module, output_fn, output_handle, include_coverage, include_stmt_coverage );
        output_static_variables( model, module, output_fn, output_handle );
        output_wrapper_functions( model, module, output_fn, output_handle );
        output_constructors_destructors( model, module, output_fn, output_handle, include_coverage, include_stmt_coverage );
        output_simulation_methods( model, module, output_fn, output_handle );
    }
    output_initalization_functions( model, output_fn, output_handle );
}

/*a To do
  Output constants - whatever they may be!
  Values wider than 64 bits - a lot later
 */

/*a Editor preferences and notes
mode: c ***
c-basic-offset: 4 ***
c-default-style: (quote ((c-mode . "k&r") (c++-mode . "k&r"))) ***
outline-regexp: "/\\\*a\\\|[\t ]*\/\\\*[b-z][\t ]" ***
*/
