/*a Copyright
  
  This file 'md_target_cdl_header.cpp' copyright Gavin J Stark 2003-2020
  
  This program is free software; you can redistribute it and/or modify it under
  the terms of the GNU General Public License as published by the Free Software
  Foundation, version 2.0.
  
  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even implied warranty of MERCHANTABILITY
  or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
  for more details.
*/

/*a Includes
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "be_errors.h"
#include "cdl_version.h"
#include "md_target_cdl_header.h"
#include "md_output_markers.h"
#include "c_model_descriptor.h"

/*a Output functions
 */
/*f string_type_name
 */
static const char *string_type_name( t_md_type_instance *instance, const char *name )
{
    static char buffer[256];
    buffer[0] = 0;
    if (instance->type==md_type_instance_type_structure) {
        sprintf(buffer, "%s %s", instance->type_def.data.type_def->name, name);
    } else {
        if (instance->type_def.data.width>=2) {
            sprintf(buffer, "bit [%2d] %s", instance->type_def.data.width, name);
        } else {
            sprintf(buffer, "bit     %s", name);
        }
    }
    return buffer;
}

/*f output_ports_nets_clocks
 */
void c_md_target_cdlh::output_ports_nets_clocks(t_md_module *module, int include_all_clocks)
{
    int indent;
    int comma_newline;

    indent=0;
    comma_newline = 0;
    output( indent, "/*m Module %s (from %s)\n", module->name, module->external?"CDL extern":"CDL module definition" );
    output( indent, "*/\n" );
    output( indent, "extern module %s(\n", module->name );

    /*b Output clocks
     */ 
    for (auto clk=module->clocks; clk; clk=clk->next_in_list) {
        if (include_all_clocks || (!clk->data.clock.clock_ref)) { // Not a gated clock, i.e. a root clock
            if (include_all_clocks || clk->data.clock.edges_used[0] || clk->data.clock.edges_used[1]) {
                if (comma_newline) {output( -1, ",\n" );}
                output( indent, "clock %s", clk->name );
                comma_newline = 1;
            }
        }
    }

    /*b Output input ports
     */ 
    for (auto signal=module->inputs; signal; signal=signal->next_in_list) {
        if (comma_newline) {output( -1, ",\n" );}
        output( indent, "input %s", string_type_name(signal->instance,signal->name));
        comma_newline = 1;
    }

    /*b Output output ports
     */
    for (auto signal=module->outputs; signal; signal=signal->next_in_list) {
        /*b Careful with output, make sure to account for last line before the closing paren.
         *  otherwise, there will be a dangling comma.
         */
        if (comma_newline) {output( -1, ",\n" );}
        output( indent, "output %s", string_type_name(signal->instance,signal->name) );
        comma_newline = 1;
    }

    /*b Finish header, start body
     */
    output( -1, "\n");
    output( indent, ")\n" );
    output( 0, "{\n");
    indent++;

    /*b Output combinatorial inputs/output ports
     */ 
    for (auto signal=module->inputs; signal; signal=signal->next_in_list) {
        if (signal->data.input.used_combinatorially) {
            output( indent, "timing comb input %s;\n", signal->name);
        }
    }
    for (auto signal=module->outputs; signal; signal=signal->next_in_list) {
        if (signal->data.output.derived_combinatorially ) {
            output( indent, "timing comb output %s;\n", signal->name);
        }
    }

    /*b Output timings to/from clocks for external modules
     */ 
    if (module->external) {
        for (auto clk=module->clocks; clk; clk=clk->next_in_list) {
            for (auto signal=module->inputs; signal; signal=signal->next_in_list) {
                t_md_reference_iter iter;
                t_md_reference *reference;
                model->reference_set_iterate_start( &signal->data.input.clocks_used_on, &iter );
                while ((reference = model->reference_set_iterate(&iter))!=NULL) {
                    auto clk2 = reference->data.signal;
                    if (clk2 == clk) {
                        output( indent, "timing to %s clock %s %s;\n", (reference->edge)?"falling":"rising", clk->name, signal->name);
                        break;
                    }
                }
            }
            for (auto signal=module->outputs; signal; signal=signal->next_in_list) {
                t_md_reference_iter iter;
                t_md_reference *reference;
                model->reference_set_iterate_start( &signal->data.output.clocks_derived_from, &iter );
                while ((reference = model->reference_set_iterate(&iter))!=NULL) {
                    auto clk2 = reference->data.signal;
                    if (clk2 == clk) {
                        output( indent, "timing from %s clock %s %s;\n", (reference->edge)?"falling":"rising", clk->name, signal->name);
                        break;
                    }
                }
            }
        }
    }

    /*b Output timings to/from clocks for non-external modules
     */ 
    if (!module->external) {
        for (auto clk=module->clocks; clk; clk=clk->next_in_list){
            if (!clk->data.clock.clock_ref) { // Not a gated clock, i.e. a root clock
                for (auto edge=0; edge<2; edge++) {
                    /*b Check all inputs for the clock and edge
                     */
                    for (auto signal=module->inputs; signal; signal=signal->next_in_list) {
                        int used_on_clock_edge = 0;
                        for (int i=0; !used_on_clock_edge && (i<signal->instance_iter->number_children); i++) {
                            auto instance = signal->instance_iter->children[i];
                            for (auto clk2=module->clocks; clk2 && !used_on_clock_edge; clk2=clk2?clk2->next_in_list:NULL) {
                                if ((clk2==clk) || (clk2->data.clock.root_clock_ref==clk)) {
                                    if (model->reference_set_includes( &instance->dependents, clk2, edge )) {
                                        used_on_clock_edge = 1;
                                    }
                                }
                            }
                        }
                        if (used_on_clock_edge) {
                            output( indent, "timing to %s clock %s %s;\n", (edge==md_edge_pos)?"rising":"falling", clk->name, signal->name);
                        }
                    }

                    /*b Check all outputs for the clock and edge
                     */
                    for (auto signal=module->outputs; signal; signal=signal->next_in_list) {
                        int derived_from_clock_edge = 0;
                        if (signal->data.output.register_ref) {
                            auto reg = signal->data.output.register_ref;
                            if ((reg->clock_ref->data.clock.root_clock_ref == clk) && (reg->edge==edge)) {
                                for (int i=0; (!derived_from_clock_edge) && (i<reg->instance_iter->number_children); i++) {
                                    derived_from_clock_edge = 1;
                                }
                            }
                        }
                        if (signal->data.output.combinatorial_ref) {
                            for (int i=0; (!derived_from_clock_edge) && (i<signal->data.output.combinatorial_ref->instance_iter->number_children); i++) {
                                t_md_reference_iter iter;
                                t_md_reference *reference;
                                model->reference_set_iterate_start( &signal->data.output.clocks_derived_from, &iter ); // For every clock that the prototype says the output is derived from, map back to clock name, go to top of clock gate tree, and say that generates it
                                while ((!derived_from_clock_edge) && (reference = model->reference_set_iterate(&iter))!=NULL) {
                                    auto clk2 = reference->data.signal;
                                    if ((clk2->data.clock.root_clock_ref==clk) && (edge==reference->edge)) {
                                        derived_from_clock_edge=1;
                                    }
                                }
                            }
                        }
                        if (signal->data.output.net_ref) {
                            for (int i=0; i<signal->data.output.net_ref->instance_iter->number_children; i++) {
                                t_md_reference_iter iter;
                                t_md_reference *reference;
                                model->reference_set_iterate_start( &signal->data.output.clocks_derived_from, &iter ); // For every clock that the prototype says the output is derived from, map back to clock name, go to top of clock gate tree, and say that generates it
                                while ((!derived_from_clock_edge) && (reference = model->reference_set_iterate(&iter))!=NULL) {
                                    auto clk2 = reference->data.signal;
                                    if ((clk2->data.clock.root_clock_ref==clk) && (edge==reference->edge)) {
                                        derived_from_clock_edge = 1;
                                    }
                                }
                            }
                        }
                        if (derived_from_clock_edge) {
                            output(indent, "timing from %s clock %s %s;\n", (edge==md_edge_pos)?"rising":"falling", clk->name, signal->name);
                        }
                    }
                }
            }
        }
    }

    /*b End body
     */
    indent--;
    output(0, "}\n");

    /*b All done
     */ 
}

/*a Public methods - output_cdlh_model
 */
/*f c_md_target_cdlh::output_cdlh_model
 */
void c_md_target_cdlh::output_cdlh_model(void)
{
    for (auto module=model->module_list; module; module=module->next_in_list) {
        output_ports_nets_clocks(module, module->external);
    }
}

/*a Editor preferences and notes
mode: c ***
c-basic-offset: 4 ***
c-default-style: (quote ((c-mode . "k&r") (c++-mode . "k&r"))) ***
outline-regexp: "/\\\*a\\\|[\t ]*\/\\\*[b-z][\t ]" ***
*/

