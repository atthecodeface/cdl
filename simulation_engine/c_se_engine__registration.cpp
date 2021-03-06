/*a Copyright
  
  This file 'c_se_engine__registration.cpp' copyright Gavin J Stark 2003, 2004
  
  This is free software; you can redistribute it and/or modify it under
  the terms of the GNU Lesser General Public License as published by the Free Software
  Foundation, version 2.1.
  
  This software is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even implied warranty of MERCHANTABILITY
  or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License
  for more details.
*/

/*a Includes
 */
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <stdarg.h>
#include "sl_debug.h"
#include "sl_exec_file.h"
#include "se_errors.h"
#include "se_engine_function.h"
#include "c_se_engine.h"
#include "c_se_engine__internal_types.h"

/*a Defines
 */
#if 0
#define WHERE_I_AM {fprintf(stderr,"%s:%s:%d\n",__FILE__,__func__,__LINE__ );}
#else
#define WHERE_I_AM {}
#endif
#define EMINAME(h) (((t_engine_module_instance *)h)->name)

/*a Types
 */
/*t t_engine_state_desc_chain
 */
typedef struct t_engine_state_desc_chain
{
     struct t_engine_state_desc_chain *next_in_list;
     t_engine_state_desc data;
} t_engine_state_desc_chain;

/*t t_register_sl_exec_file_data
 */
typedef struct t_register_sl_exec_file_data
{
     c_engine *engine;
     t_engine_module_instance *module_instance;
     const char *name;
     t_engine_state_desc_chain *state_desc_chain;
     t_engine_state_desc_chain *last_state_desc_chain;
     int number_state_desc;
} t_register_sl_exec_file_data;

/*t t_sim_reg_ef_lib
 */
typedef struct t_sim_reg_ef_lib
{
    struct t_sl_exec_file_data *file_data;
    c_engine *engine;
    void *engine_handle;
    struct t_sim_reg_ef_message_object *messages;
} t_sim_reg_ef_lib;

/*t t_sim_reg_ef_message_object
 */
typedef struct t_sim_reg_ef_message_object
{
    struct t_sim_reg_ef_message_object *next_in_list;
    t_sim_reg_ef_lib *ef_lib;
    t_se_message message;
    const char *name;
} t_sim_reg_ef_message_object;

/*a Function declarations
 */
static t_sl_error_level ef_method_eval_message_send_int( t_sl_exec_file_cmd_cb *cmd_cb, void *object_handle, t_sl_exec_file_object_desc *object_desc, t_sl_exec_file_method *method );
static t_sl_error_level ef_method_eval_message_send_value( t_sl_exec_file_cmd_cb *cmd_cb, void *object_handle, t_sl_exec_file_object_desc *object_desc, t_sl_exec_file_method *method );
static t_sl_error_level ef_method_eval_message_get_int( t_sl_exec_file_cmd_cb *cmd_cb, void *object_handle, t_sl_exec_file_object_desc *object_desc, t_sl_exec_file_method *method );
static t_sl_error_level ef_method_eval_message_get_value( t_sl_exec_file_cmd_cb *cmd_cb, void *object_handle, t_sl_exec_file_object_desc *object_desc, t_sl_exec_file_method *method );
static t_sl_error_level ef_method_eval_message_get_string( t_sl_exec_file_cmd_cb *cmd_cb, void *object_handle, t_sl_exec_file_object_desc *object_desc, t_sl_exec_file_method *method );
static t_sl_error_level ef_method_eval_message_response( t_sl_exec_file_cmd_cb *cmd_cb, void *object_handle, t_sl_exec_file_object_desc *object_desc, t_sl_exec_file_method *method );
static t_sl_error_level ef_method_eval_message_text( t_sl_exec_file_cmd_cb *cmd_cb, void *object_handle, t_sl_exec_file_object_desc *object_desc, t_sl_exec_file_method *method );

/*a Statics
 */
/*v sim_file_cmds
 */
static t_sl_exec_file_cmd sim_file_cmds[] =
{
     {0,        1, "!sim_message", "s", "sim_message <name>"},
     SL_EXEC_FILE_CMD_NONE
};

/*v sl_vcd_file_obj_methods - Exec file object methods
 */
static t_sl_exec_file_method sl_message_object_methods[] =
{
    {"send_int",   'i',  2, "siiiiiiii",  "send_int(<module instance>,<message number>,<args>*) - send message with data of ints to instance given by name, keep results in the message object", ef_method_eval_message_send_int },
    {"send_value", 'i',  2, "siiiiiiii",  "send_values(<module instance>,<message number>,<args>*) - send message with data of int64s to instance given by name, keep results in the message object", ef_method_eval_message_send_value },
    {"get_int",    'i',  1, "i",  "get_int(offset)    - gets n'th int in the message", ef_method_eval_message_get_int },
    {"get_value",  'i',  1, "i",  "get_value(offset)  - gets n'th value in the message", ef_method_eval_message_get_value },
    {"get_string", 's',  1, "i",  "get_string(offset) - gets n'th string in the message", ef_method_eval_message_get_string },
    {"response", 'i',  1, "i",   "response(dummy)   - get response value from last message", ef_method_eval_message_response },
    {"text",     's',  1, "i",   "text(dummy)       - get message text", ef_method_eval_message_text },
    SL_EXEC_FILE_METHOD_NONE
};

/*a Module, signal, clock, state registration methods - called by modules instances at their instantiation
 */
/*f c_engine::register_delete_function
 */
void c_engine::register_delete_function( void *engine_handle, t_se_engine_std_function delete_fn)
{
     auto emi = (t_engine_module_instance *)engine_handle;
     emi->delete_cb.add(delete_fn);
}

/*f c_engine::register_reset_function
 */
void c_engine::register_reset_function( void *engine_handle, t_se_engine_int_std_function reset_fn)
{
     auto emi = (t_engine_module_instance *)engine_handle;
     emi->reset_cb.add(reset_fn);
}

/*f c_engine::register_prepreclock_fn
 */
void c_engine::register_prepreclock_fn( void *engine_handle, t_se_engine_std_function prepreclock_fn )
{
     auto emi = (t_engine_module_instance *)engine_handle;
     emi->prepreclock_cb.add(prepreclock_fn);
}

/*f c_engine::register_propagate_fn
 */
void c_engine::register_propagate_fn( void *engine_handle, t_se_engine_std_function propagate_fn )
{
     auto emi = (t_engine_module_instance *)engine_handle;
     emi->propagate_cb.add(propagate_fn);
}

/*f c_engine::register_delete_function - DEPRECATED
 */
void c_engine::register_delete_function( void *engine_handle, void *handle, t_engine_callback_fn  delete_fn )
{
    DEPRECATED(EMINAME(engine_handle),"std::function instead of void* and callbacks");
    register_delete_function(engine_handle, [delete_fn, handle](void)->t_sl_error_level{return (*delete_fn)(handle);});
}

/*f c_engine::register_reset_function - DEPRECATED
 */
void c_engine::register_reset_function( void *engine_handle, void *handle, t_engine_callback_arg_fn  reset_fn )
{
    DEPRECATED(EMINAME(engine_handle),"std::function instead of void* and callbacks");
    register_reset_function(engine_handle, [reset_fn, handle](int p)->t_sl_error_level{return (*reset_fn)(handle, p);});
}

/*f c_engine::register_input_signal
 */
void c_engine::register_input_signal( void *engine_handle, const char *name, int size, t_se_signal_value **value_ptr_ptr, int may_be_unconnected )
{
     t_engine_module_instance *emi;
     t_engine_function *efn;

     emi = (t_engine_module_instance *)engine_handle;

     efn = se_engine_function_add_function( emi, &emi->input_list, name );
     efn->data.input.size = size;
     efn->data.input.value_ptr_ptr = value_ptr_ptr;
     *efn->data.input.value_ptr_ptr = NULL;
     efn->data.input.may_be_unconnected = may_be_unconnected;
     efn->data.input.driven_by = NULL;
     efn->data.input.used_by_clocks = NULL;
     efn->data.input.combinatorial = 0;
     efn->data.input.connected_to = NULL;
}

/*f c_engine::register_output_signal
 */
void c_engine::register_output_signal( void *engine_handle, const char *name, int size, t_se_signal_value *value_ptr )
{
     t_engine_module_instance *emi;
     t_engine_function *efn;

     emi = (t_engine_module_instance *)engine_handle;

     efn = se_engine_function_add_function( emi, &emi->output_list, name );
     efn->data.output.size = size;
     efn->data.output.value_ptr = value_ptr;
     efn->data.output.drives = NULL;
     efn->data.output.generated_by_clock = NULL;
     efn->data.output.combinatorial = 0;
     efn->data.output.has_clocked_state_desc = -1; // Have not checked it it has a clocked_state_desc yet
}

/*f c_engine::register_clock_fns - all 4
 */
void c_engine::register_clock_fns( void *engine_handle,
                                   const char *clock_name,
                                   t_se_engine_std_function pos_pclk_fn,
                                   t_se_engine_std_function pos_clk_fn,
                                   t_se_engine_std_function neg_pclk_fn,
                                   t_se_engine_std_function neg_clk_fn )
{
     t_engine_module_instance *emi;
     t_engine_function *efn;

     emi = (t_engine_module_instance *)engine_handle;

     efn = se_engine_function_add_function( emi, &emi->clock_fn_list, clock_name );
     efn->data.clock.posedge_preclock_fn = pos_pclk_fn;
     efn->data.clock.posedge_clock_fn    = pos_clk_fn;
     efn->data.clock.negedge_preclock_fn = neg_pclk_fn;
     efn->data.clock.negedge_clock_fn    = neg_clk_fn;
     efn->data.clock.driven_by = NULL;
}

/*f c_engine::register_clock_fns - just posedge
 */
void c_engine::register_clock_fns( void *engine_handle,
                                   const char *clock_name,
                                   t_se_engine_std_function pos_pclk_fn,
                                   t_se_engine_std_function pos_clk_fn )
{
    register_clock_fns(engine_handle, clock_name, pos_pclk_fn, pos_clk_fn, t_se_engine_std_function(), t_se_engine_std_function());
}

/*f c_engine::register_comb_fn
 */
void c_engine::register_comb_fn( void *engine_handle, t_se_engine_std_function comb_fn )
{
     auto emi = (t_engine_module_instance *)engine_handle;
     emi->comb_cb.add(comb_fn);
}

/*f c_engine::register_message_function
 */
void c_engine::register_message_function( void *engine_handle, t_se_engine_msg_std_function message_fn )
{
    auto emi = (t_engine_module_instance *)engine_handle;
    emi->message_cb.add(message_fn);
}

/*f c_engine::register_clock_fns - DEPRECATED
 */
void c_engine::register_clock_fns( void *engine_handle, void *handle, const char *clock_name, t_engine_callback_fn posedge_preclock_fn, t_engine_callback_fn posedge_clock_fn, t_engine_callback_fn negedge_preclock_fn, t_engine_callback_fn negedge_clock_fn )
{
    DEPRECATED(EMINAME(engine_handle),"std::function instead of void* and callbacks, and declare all functions for a clock in a single call");
    auto none = t_se_engine_std_function();
    auto pos_pclk_fn = posedge_preclock_fn ? ([handle,posedge_preclock_fn](void)->t_sl_error_level{return (*posedge_preclock_fn)(handle);}) : none;
    auto pos_clk_fn  = posedge_clock_fn    ? ([handle,posedge_clock_fn]   (void)->t_sl_error_level{return (*posedge_clock_fn)   (handle);}) : none;
    auto neg_pclk_fn = negedge_preclock_fn ? ([handle,negedge_preclock_fn](void)->t_sl_error_level{return (*negedge_preclock_fn)(handle);}) : none;
    auto neg_clk_fn  = negedge_clock_fn    ? ([handle,negedge_clock_fn]   (void)->t_sl_error_level{return (*negedge_clock_fn)   (handle);}) : none;
    return register_clock_fns(engine_handle, clock_name, pos_pclk_fn, pos_clk_fn, neg_pclk_fn, neg_clk_fn );
}

/*f c_engine::register_clock_fns - DEPRECATED FATAL
 */
void c_engine::register_clock_fns( void *engine_handle, void *handle, const char *clock_name, t_engine_callback_fn preclock_fn, t_engine_callback_fn clock_fn )
{
    DEPRECATED(EMINAME(engine_handle),"FATAL: std::function instead of void* and callbacks, and declare all functions for a clock in a single call");
}

/*f c_engine::register_preclock_fns - DEPRECATED FATAL
 */
void c_engine::register_preclock_fns( void *engine_handle, void *handle, const char *clock_name, t_engine_callback_fn posedge_preclock_fn, t_engine_callback_fn negedge_preclock_fn )
{
    DEPRECATED(EMINAME(engine_handle),"FATAL: std::function instead of void* and callbacks, and declare all functions for a clock in a single call");
}

/*f c_engine::register_clock_fn - DEPRECATED FATAL once registered with one of the above, set an individual function
 */
int c_engine::register_clock_fn( void *engine_handle, void *handle, const char *clock_name, t_engine_sim_function_type type, t_engine_callback_fn x_clock_fn )
{
    DEPRECATED(EMINAME(engine_handle),"FATAL: std::function instead of void* and callbacks, and declare all functions for a clock in a single call");
    return 0;
}

/*f c_engine::register_prepreclock_fn - DEPRECATED
 */
void c_engine::register_prepreclock_fn( void *engine_handle, void *handle, t_engine_callback_fn prepreclock_fn )
{
    DEPRECATED(EMINAME(engine_handle),"std::function instead of void* and callbacks, and declare all functions for a clock in a single call");
    auto fn = ([handle,prepreclock_fn](void)->t_sl_error_level{return (*prepreclock_fn)(handle);});
    return register_prepreclock_fn(engine_handle, fn );
}

/*f c_engine::register_propagate_fn - DEPRECATED
 */
void c_engine::register_propagate_fn( void *engine_handle, void *handle, t_engine_callback_fn propagate_fn )
{
    DEPRECATED(EMINAME(engine_handle),"std::function instead of void* and callbacks, and declare all functions for a clock in a single call");
    auto fn = ([handle,propagate_fn](void)->t_sl_error_level{return (*propagate_fn)(handle);});
    return register_propagate_fn(engine_handle, fn );
}

/*f c_engine::register_comb_fn - DEPRECATED
 */
void c_engine::register_comb_fn( void *engine_handle, void *handle, t_engine_callback_fn comb_fn )
{
    DEPRECATED(EMINAME(engine_handle),"std::function instead of void* and callbacks; comb also needs to support groups of inputs and outputs");
    auto fn = ([handle,comb_fn](void)->t_sl_error_level{return (*comb_fn)(handle);});
    return register_comb_fn(engine_handle, fn );
}

/*f c_engine::register_message_function - DEPRECATED
 */
void c_engine::register_message_function( void *engine_handle, void *handle, t_engine_callback_argp_fn message_fn )
{
    DEPRECATED(EMINAME(engine_handle),"std::function instead of void* and callbacks");
    auto fn = ([handle,message_fn](t_se_message *m)->void{(*message_fn)(handle, (void *)m);});
    return register_message_function(engine_handle, fn );
}

/*f c_engine::register_input_used_on_clock
 */
void c_engine::register_input_used_on_clock( void *engine_handle, const char *name, const char *clock_name, int posedge )
{
     t_engine_module_instance *emi;
     t_engine_function *efn_sig, *efn_clk;

     emi = (t_engine_module_instance *)engine_handle;

     efn_sig = se_engine_function_find_function( emi->input_list, name );
     efn_clk = se_engine_function_find_function( emi->clock_fn_list, clock_name );
     if ( (!efn_sig) || (!efn_clk) )
     {
          add_error( (void *)emi->name, error_level_serious, error_number_se_unknown_clock_or_signal, error_id_se_register_input_used_on_clock,
                            error_arg_type_malloc_string, emi->name,
                            error_arg_type_malloc_string, name,
                            error_arg_type_malloc_string, clock_name,
                            error_arg_type_none );
     }
     se_engine_function_references_add( &efn_sig->data.input.used_by_clocks, efn_clk );
}

/*f c_engine::register_output_generated_on_clock
 */
void c_engine::register_output_generated_on_clock( void *engine_handle, const char *name, const char *clock_name, int posedge )
{
     t_engine_module_instance *emi;
     t_engine_function *efn_sig, *efn_clk;

     emi = (t_engine_module_instance *)engine_handle;

     efn_sig = se_engine_function_find_function( emi->output_list, name );
     efn_clk = se_engine_function_find_function( emi->clock_fn_list, clock_name );
     if ( (!efn_sig) || (!efn_clk) )
     {
          add_error( (void *)emi->name, error_level_serious, error_number_se_unknown_clock_or_signal, error_id_se_register_output_generated_on_clock,
                            error_arg_type_malloc_string, emi->name,
                            error_arg_type_malloc_string, name,
                            error_arg_type_malloc_string, clock_name,
                            error_arg_type_none );
     }
     if (0 && efn_sig->data.output.generated_by_clock) // GJS Oct 2012 - we do not care about this unless we have toplevel combs, which we should disallow
     {
          add_error( (void *)emi->name, error_level_serious, error_number_se_multiple_source_clocks, error_id_se_register_output_generated_on_clock,
                            error_arg_type_malloc_string, name,
                            error_arg_type_malloc_string, efn_clk->name,
                            error_arg_type_malloc_string, efn_sig->data.output.generated_by_clock->name,
                            error_arg_type_none );
     }
     efn_sig->data.output.generated_by_clock = efn_clk;
}

/*f c_engine::register_comb_input
 */
void c_engine::register_comb_input( void *engine_handle, const char *name )
{
     t_engine_module_instance *emi;
     t_engine_function *efn_sig;

     emi = (t_engine_module_instance *)engine_handle;

     efn_sig = se_engine_function_find_function( emi->input_list, name );
     if (!efn_sig)
     {
          add_error( (void *)emi->name, error_level_serious, error_number_se_unknown_input, error_id_se_register_comb_input,
                            error_arg_type_malloc_string, name,
                            error_arg_type_none );
     }
     efn_sig->data.input.combinatorial = 1;
}

/*f c_engine::register_comb_output
 */
void c_engine::register_comb_output( void *engine_handle, const char *name )
{
     t_engine_module_instance *emi;
     t_engine_function *efn_sig;

     emi = (t_engine_module_instance *)engine_handle;

     efn_sig = se_engine_function_find_function( emi->output_list, name );
     if (!efn_sig)
     {
          add_error( (void *)emi->name, error_level_serious, error_number_se_unknown_output, error_id_se_register_comb_output,
                            error_arg_type_malloc_string, name,
                            error_arg_type_none );
     }
     efn_sig->data.output.combinatorial = 1;
}

/*f c_engine::register_state_desc
  prefix is used by sl_exec_file when registering extra state - so effectively if there is a prefix then the state is <prefix>.<state>
  desc_type is 0 for mallocked (must copy), no indirect ptrs
  desc_type is 1 for static (no need to copy), no indirect ptrs
  desc_type is 2 for mallocked (must copy), all ptrs indirect
  desc_type is 3 for static (no need to copy), all ptrs indirect
  desc_type +4 if it is state that is off 'registers'; i.e. recovering this in checkpoints and then propagating should bring other state up to date
 */
void c_engine::register_state_desc( void *engine_handle, int desc_type, t_engine_state_desc *state_desc, void *data, const char *prefix )
{
     int i, num_state;
     t_engine_state_desc_list *sdl;
     t_engine_module_instance *emi;
     emi = (t_engine_module_instance *)engine_handle;

     WHERE_I_AM;
     if (!emi)
          return;

     //fprintf(stderr, "Registering state prefix %s state %s\n", prefix, state_desc[0].name );
     SL_DEBUG(sl_debug_level_info, "c_engine::register_state_desc", "Registering state descriptions prefix %s first state %s", prefix?prefix:"<no prefix>", state_desc[0].name?state_desc[0].name:"<no state!>" ) ;

     WHERE_I_AM;
     for (i=0; state_desc[i].type!=engine_state_desc_type_none; i++);
     num_state = i;
     if (desc_type & 1)
     {
     WHERE_I_AM;
          sdl = (t_engine_state_desc_list *)malloc(sizeof(t_engine_state_desc_list));
          sdl->state_desc = state_desc;
     }
     else
     {
     WHERE_I_AM;
          sdl = (t_engine_state_desc_list *)malloc(sizeof(t_engine_state_desc_list) + num_state*sizeof(t_engine_state_desc));
          sdl->state_desc = (t_engine_state_desc *)(&(sdl[1]));
          memcpy( sdl->state_desc, state_desc, num_state * sizeof(t_engine_state_desc) );
     }
     WHERE_I_AM;
     sdl->next_in_list = emi->state_desc_list;
     emi->state_desc_list = sdl;
     sdl->data_base_ptr = data;
     sdl->num_state = i;
     sdl->prefix = sl_str_alloc_copy( prefix );
     sdl->data_indirected = ((desc_type&2)!=0);
     sdl->data_clocked = ((desc_type&4)!=0);
     WHERE_I_AM;
}

/*a Exec file enhancements
 */
/*f se_engine_register_sl_exec_file_register_state
 */
static void se_engine_register_sl_exec_file_register_state( void *handle, const char *instance, const char *state_name, int type, int *data_ptr, int width, ... )
{
    t_register_sl_exec_file_data *rsefd;
    t_engine_state_desc_chain *sdc;

    WHERE_I_AM;
    va_list ap;
    va_start( ap, width );

    WHERE_I_AM;
    rsefd = (t_register_sl_exec_file_data *)handle;
    if (!rsefd->name)
    {
        rsefd->name = instance;
    }

    sdc = (t_engine_state_desc_chain *)malloc( sizeof(t_engine_state_desc_chain) );
    if (rsefd->last_state_desc_chain)
    {
        rsefd->last_state_desc_chain->next_in_list=sdc;
    }
    else
    {
        rsefd->state_desc_chain=sdc;
    }
    WHERE_I_AM;
    sdc->next_in_list = NULL;
    rsefd->last_state_desc_chain=sdc;
    rsefd->number_state_desc++;
    sdc->data.name = (char *)state_name;
    WHERE_I_AM;
    switch (type)
    {
    case 0:
        sdc->data.type = engine_state_desc_type_bits;
        sdc->data.offset = 0;
        sdc->data.args[0] = width;
        sdc->data.ptr = data_ptr;
        break;
    case 1:
        sdc->data.type = engine_state_desc_type_array;
        sdc->data.offset = 0;
        sdc->data.args[0] = width;
        sdc->data.args[1] = va_arg(ap,int);
        sdc->data.ptr = data_ptr;
        break;
    default:
        break;
    }
    WHERE_I_AM;
    //fprintf(stderr, "Registered state %s:%s\n", rsefd->name, sdc->data.name );
    va_end(ap);
    WHERE_I_AM;
}

/*f se_engine_register_sl_exec_file_register_state_complete
 */
static void se_engine_register_sl_exec_file_register_state_complete( void *handle )
{
     t_register_sl_exec_file_data *rsefd;
     int i;
     t_engine_state_desc *state_desc;
     t_engine_state_desc_chain *sdc;

     WHERE_I_AM;
     rsefd = (t_register_sl_exec_file_data *)handle;
     //fprintf(stderr, "FREEING %p\n", rsefd );

     state_desc = (t_engine_state_desc *)malloc(sizeof(t_engine_state_desc)*(rsefd->number_state_desc+1));
     for (i=0, sdc=rsefd->state_desc_chain; sdc; sdc=sdc->next_in_list, i++)
     {
          state_desc[i] = sdc->data;
          //fprintf(stderr, "se_engine_register_sl_exec_file_register_state_complete:State desc %d : %s\n", i, state_desc[i].name );
     }
     state_desc[i].type = engine_state_desc_type_none;
     state_desc[i].name = NULL;

     WHERE_I_AM;
     rsefd->engine->register_state_desc( (void *)rsefd->module_instance, 0, state_desc, NULL, rsefd->name );
     while (rsefd->state_desc_chain)
     {
          sdc = rsefd->state_desc_chain;
          rsefd->state_desc_chain = sdc->next_in_list;
          free(sdc);
     }
     WHERE_I_AM;
     free(rsefd);
     free(state_desc);
}

/*f static exec_file_cmd_handler
 */
static t_sl_error_level exec_file_cmd_handler( struct t_sl_exec_file_cmd_cb *cmd_cb, void *handle )
{
    t_sim_reg_ef_lib *efl;
    efl = (t_sim_reg_ef_lib *)handle;
    if (!efl->engine->register_handle_exec_file_command( handle, cmd_cb ))
        return error_level_serious;
    return error_level_okay;
}

/*f c_engine::register_add_exec_file_enhancements
 */
int c_engine::register_add_exec_file_enhancements( struct t_sl_exec_file_data *file_data, void *engine_handle )
{
    t_register_sl_exec_file_data *rsefd;
    t_sl_exec_file_lib_desc lib_desc;
    t_sim_reg_ef_lib *efl;

    if (engine_handle)
    {
        WHERE_I_AM;
        rsefd = (t_register_sl_exec_file_data *) malloc(sizeof(t_register_sl_exec_file_data));
        if (rsefd)
        {
            rsefd->engine = this;
            rsefd->module_instance = (t_engine_module_instance *)engine_handle;
            rsefd->name = NULL;
            rsefd->state_desc_chain = NULL;
            rsefd->last_state_desc_chain = NULL;
            rsefd->number_state_desc=0;
            sl_exec_file_set_state_registration( file_data, se_engine_register_sl_exec_file_register_state, se_engine_register_sl_exec_file_register_state_complete, (void *)rsefd );
        }
    }

    efl = (t_sim_reg_ef_lib *)malloc(sizeof(t_sim_reg_ef_lib));
    efl->file_data = file_data;
    efl->engine = this;
    efl->engine_handle = engine_handle;
    efl->messages = NULL;
    lib_desc.version = sl_ef_lib_version_cmdcb;
    lib_desc.library_name = "cdlsim_reg";
    lib_desc.handle = (void *) efl;
    lib_desc.cmd_handler = exec_file_cmd_handler;
    lib_desc.file_cmds = sim_file_cmds;
    lib_desc.file_fns = NULL;
    lib_desc.free_fn = sl_exec_file_lib_free_handle;
    return sl_exec_file_add_library( file_data, &lib_desc );
}

/*f c_engine::register_handle_exec_file_command
  returns 0 if it did not handle
  returns 1 if it handled it
 */
int c_engine::register_handle_exec_file_command( void *handle, struct t_sl_exec_file_cmd_cb *cmd_cb )
{
    t_sl_exec_file_object_desc object_desc;
    t_sim_reg_ef_message_object *msg;
    t_sim_reg_ef_lib *efl = (t_sim_reg_ef_lib *)handle;

    switch (cmd_cb->cmd)
    {
    case 0:
        msg = (t_sim_reg_ef_message_object *)malloc(sizeof(t_sim_reg_ef_message_object));
        msg->next_in_list = efl->messages;
        efl->messages = msg;
        msg->ef_lib = efl;
        msg->name = sl_str_alloc_copy(sl_exec_file_eval_fn_get_argument_string( cmd_cb->file_data, cmd_cb->args, 0 ));
        memset(&object_desc,0,sizeof(object_desc));
        object_desc.version = sl_ef_object_version_checkpoint_restore;
        object_desc.name = msg->name;
        object_desc.handle = (void *)msg;
        object_desc.methods = sl_message_object_methods;
        sl_exec_file_add_object_instance( cmd_cb->file_data, &object_desc );
        return 1;
    }
     return 0;
}

/*f ef_method_eval_message_send_int
 */
static t_sl_error_level ef_method_eval_message_send_int( t_sl_exec_file_cmd_cb *cmd_cb, void *object_handle, t_sl_exec_file_object_desc *object_desc, t_sl_exec_file_method *method )
{
    t_sim_reg_ef_message_object *msg;
    void *handle;
    const char *instance_name;
    int reason;
    int result;
    unsigned int i;

    msg = (t_sim_reg_ef_message_object *)object_desc->handle;

    instance_name = sl_exec_file_eval_fn_get_argument_string( cmd_cb->file_data, cmd_cb->args, 0 );
    reason        = sl_exec_file_eval_fn_get_argument_integer( cmd_cb->file_data, cmd_cb->args, 1 );
    for (i=0; ((int)i<cmd_cb->num_args-2) && (i<sizeof(msg->message.data.ints)/sizeof(int)); i++)
    {
        msg->message.data.ints[i] = sl_exec_file_eval_fn_get_argument_integer( cmd_cb->file_data, cmd_cb->args, i+2 );
    }

    handle = msg->ef_lib->engine->find_module_instance( instance_name );
    if (!handle)
    {
        fprintf(stderr,"Could not find module '%s'\n",instance_name);
        return error_level_fatal;
    }
    msg->message.reason = reason;
    msg->message.response_type = se_message_response_type_none;
    result = msg->ef_lib->engine->module_instance_send_message( handle, &(msg->message) );

    if (!sl_exec_file_eval_fn_set_result( cmd_cb->file_data, (t_sl_uint64) (result) ))
        return error_level_fatal;
    return error_level_okay;
}

/*f ef_method_eval_message_send_value
 */
static t_sl_error_level ef_method_eval_message_send_value( t_sl_exec_file_cmd_cb *cmd_cb, void *object_handle, t_sl_exec_file_object_desc *object_desc, t_sl_exec_file_method *method )
{
    t_sim_reg_ef_message_object *msg;
    void *handle;
    const char *instance_name;
    int reason;
    int result;
    unsigned int i;

    msg = (t_sim_reg_ef_message_object *)object_desc->handle;

    instance_name = sl_exec_file_eval_fn_get_argument_string( cmd_cb->file_data, cmd_cb->args, 0 );
    reason        = sl_exec_file_eval_fn_get_argument_integer( cmd_cb->file_data, cmd_cb->args, 1 );
    for (i=0; ((int)i<cmd_cb->num_args-2) && (i<sizeof(msg->message.data.values)/sizeof(t_se_signal_value)); i++)
    {
        msg->message.data.values[i] = sl_exec_file_eval_fn_get_argument_integer( cmd_cb->file_data, cmd_cb->args, i+2 );
    }

    handle = msg->ef_lib->engine->find_module_instance( instance_name );
    if (!handle)
    {
        fprintf(stderr,"Could not find module '%s'\n",instance_name);
        return error_level_fatal;
    }
    msg->message.reason = reason;
    msg->message.response_type = se_message_response_type_none;
    result = msg->ef_lib->engine->module_instance_send_message( handle, &(msg->message) );

    if (!sl_exec_file_eval_fn_set_result( cmd_cb->file_data, (t_sl_uint64) (result) ))
        return error_level_fatal;
    return error_level_okay;
}

/*f ef_method_eval_message_response
 */
static t_sl_error_level ef_method_eval_message_response( t_sl_exec_file_cmd_cb *cmd_cb, void *object_handle, t_sl_exec_file_object_desc *object_desc, t_sl_exec_file_method *method )
{
    t_sim_reg_ef_message_object *msg;
    int result;

    msg = (t_sim_reg_ef_message_object *)object_desc->handle;
    if (msg->message.response_type == se_message_response_type_none)
        result = -1;
    else
        result = (int)(msg->message.response);
    if (!sl_exec_file_eval_fn_set_result( cmd_cb->file_data, (t_sl_uint64) (result) ))
        return error_level_fatal;
    return error_level_okay;
}

/*f ef_method_eval_message_text
 */
static t_sl_error_level ef_method_eval_message_text( t_sl_exec_file_cmd_cb *cmd_cb, void *object_handle, t_sl_exec_file_object_desc *object_desc, t_sl_exec_file_method *method )
{
    t_sim_reg_ef_message_object *msg;
    const char *result;

    msg = (t_sim_reg_ef_message_object *)object_desc->handle;
    if (msg->message.response_type == se_message_response_type_text)
        result = msg->message.data.text;
    else
        result = "<Bad or no response>";
    if (!sl_exec_file_eval_fn_set_result( cmd_cb->file_data, result, 1))
        return error_level_fatal;
    return error_level_okay;
}

/*f ef_method_eval_message_get_int
 */
static t_sl_error_level ef_method_eval_message_get_int( t_sl_exec_file_cmd_cb *cmd_cb, void *object_handle, t_sl_exec_file_object_desc *object_desc, t_sl_exec_file_method *method )
{
    t_sim_reg_ef_message_object *msg;
    int offset;

    msg = (t_sim_reg_ef_message_object *)object_desc->handle;

    offset = sl_exec_file_eval_fn_get_argument_integer( cmd_cb->file_data, cmd_cb->args, 0 );
    if (offset<0) offset=0;
    if (offset>7) offset=7;
    if (!sl_exec_file_eval_fn_set_result( cmd_cb->file_data, (t_sl_uint64) (msg->message.data.ints[offset]) ))
        return error_level_fatal;
    return error_level_okay;
}

/*f ef_method_eval_message_get_value
 */
static t_sl_error_level ef_method_eval_message_get_value( t_sl_exec_file_cmd_cb *cmd_cb, void *object_handle, t_sl_exec_file_object_desc *object_desc, t_sl_exec_file_method *method )
{
    t_sim_reg_ef_message_object *msg;
    int offset;

    msg = (t_sim_reg_ef_message_object *)object_desc->handle;

    offset = sl_exec_file_eval_fn_get_argument_integer( cmd_cb->file_data, cmd_cb->args, 0 );
    if (offset<0) offset=0;
    if (offset>3) offset=3;
    if (!sl_exec_file_eval_fn_set_result( cmd_cb->file_data, (t_sl_uint64) (msg->message.data.values[offset]) ))
        return error_level_fatal;
    return error_level_okay;
}

/*f ef_method_eval_message_get_string
 */
static t_sl_error_level ef_method_eval_message_get_string( t_sl_exec_file_cmd_cb *cmd_cb, void *object_handle, t_sl_exec_file_object_desc *object_desc, t_sl_exec_file_method *method )
{
    t_sim_reg_ef_message_object *msg;
    int offset;

    msg = (t_sim_reg_ef_message_object *)object_desc->handle;

    offset = sl_exec_file_eval_fn_get_argument_integer( cmd_cb->file_data, cmd_cb->args, 0 );
    if (offset<0) offset=0;
    if (offset>3) offset=3;
    if (!sl_exec_file_eval_fn_set_result( cmd_cb->file_data, (const char *)(msg->message.data.ptrs[offset]), 1 ))
        return error_level_fatal;
    return error_level_okay;
}

/*a Editor preferences and notes
mode: c ***
c-basic-offset: 4 ***
c-default-style: (quote ((c-mode . "k&r") (c++-mode . "k&r"))) ***
outline-regexp: "/\\\*a\\\|[\t ]*\/\\\*[b-z][\t ]" ***
*/
