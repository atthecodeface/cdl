/*a Copyright
  
  This file 'c_se_engine__simulation.cpp' copyright Gavin J Stark 2003, 2004
  
  This is free software; you can redistribute it and/or modify it under
  the terms of the GNU Lesser General Public License as published by the Free Software
  Foundation, version 2.1.
  
  This software is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even implied warranty of MERCHANTABILITY
  or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License
  for more details.
*/

/*a Documentation
  Toplevel CDL modules - those whose functions are invoked from the engine simulator - have a defined set of methods

  1) prepreclock
  Called once, to indicate one ore more simultaneous clock edges are about to occur.
  Most modules with set a 'captured inputs' indicator to False

  2) preclock
  Called one or more times; once per clock that fires
  All inputs to the module are valid whenever this is called.
  Inputs can be captured on only the first called if the module's 'captured inputs' indicator is false, and it is then set
  For modules with multiple clocks that could actually be fully synchronous, the 'next state' for each clock CAN be calculated here
  An alternative is to record all the 'preclock' function calls that happen since the last 'prepreclock' function call

  3) clock
  Called one or more times; once per clock that fires
  For a single clock module, this module can implement the 'next state' function simply.
  For a module with multiple clocks, the 'recorded preclocked fns' indicate which clocks have to be activated; the first
  call of the clock method can invoke all the relevant clock functions.
  After the 'clock' method is completed ALL outputs of the module that depend on state alone MUST be valid; all outputs
  that are combinatorial on inputs MUST be valid given the captured input state (the state at preclock)
  Hence for a non-combinatorial module the outputs are fully valid; internal wire values need not be

  4) comb
  Called ONLY for combinatorial modules
  Inputs are valid on entry
  ALL outputs must be valid on exit

  5) propagate
  Called ONLY for waveform updates
  All inputs are valid on entry
  All internal wires must be made valid; there should be no effect on outputs (since it must only be invoked after 'comb' has been invoked).


  More formally:

  prepreclock
    predicated on: nothing
    
  preclock
    predicated on: inputs valid, prepreclock must have been invoked
    must: capture ensure all inputs are captured
    
  clock
    predicated on: preclock must have been invoked for all clocks about to occur
    must: implement 'next state functions; propagate state changes to outputs based on captured inputs

  comb
    predicated on: inputs valid
    must: capture inputs; make all combinatorial outputs valid

  propagate
    predicated on: clock and then comb have been called; inputs valid
    must: capture inputs; propagate input and state to all internal signals



  Now, consider a module with submodules.
  We will assume module 'M' with submodules 'A', 'B' and 'C'
  'A' has some combinatorial inputs to outputs
  'A' also has some clocked logic dependent on an input that is wired (in M) to one of its outputs - i.e. its inputs depend on its outputs...
  'B' is purely combinatorial
  'C' is purely clocked

  M.prepreclock
    predicated on: nothing
    sets M.inputs_captured=False
    
  M.preclock
    predicated on: M.inputs valid, M.prepreclock has occurred
    must: if (!M.inputs_captured) then capture inputs, M.inputs_captured=True
    
  M.clock
    predicated on: M.preclock must have been invoked for all clocks about to occur
       hence M.inputs_captured=True, and M.inputs are captured in M
    must:
       Ensure A.inputs, C.inputs and dependencies are valid
        To do this, note M.state is valid; non-comb A.outputs, C.outputs are assumed valid
        Propagate from valid signals through combinatorial logic to get all combs valid
        Will require A.comb, B.comb to be invoked
      At this point A.inputs and C.inputs used for clocked logic must be valid
      Prepreclock A, C
      Preclock A, C for all clock edges
      Do next-state for M for all specified clock edges
      Clock A, C
        (C.outputs are valid; non-comb A.outputs are valid)
      Ensure M.outputs and dependencies are valid

  M.comb
    predicated on: M.inputs valid
    must:
      Capture M.inputs
      Ensure M.outputs and dependencies are valid

  M.propagate
    predicated on: clock and then comb have been called; M.inputs valid
    must:
      Capture M.inputs
      Ensure all internal signals are valid
      A.propagate, C.propagate

 */
/*a Includes
 */
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <stdarg.h>
#include "sl_general.h"
#include "sl_debug.h"
#include "sl_exec_file.h"
#include "sl_token.h"
#include "sl_ef_lib_event.h"
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

/*a Types
 */
/*t wait_cb_arg_*
 */
enum
{
    wait_cb_arg_lib_data,
    wait_cb_arg_input,
    wait_cb_arg_value,
    wait_cb_arg_expect_value,
    wait_cb_arg_timeout,
};

/*t t_sim_ef_lib_input
 */
typedef struct t_sim_ef_lib_input
{
    struct t_sim_ef_lib_data *lib_data;
    char *name;
    int width;
    t_se_signal_value *data;
    t_se_signal_value value;
} t_sim_ef_lib_input;

/*t t_sim_ef_lib_output
 */
typedef struct t_sim_ef_lib_output
{
    struct t_sim_ef_lib_data *lib_data;
    char *name;
    int width;
    t_se_signal_value next_data;
    t_se_signal_value data;
} t_sim_ef_lib_output;

/*t t_sim_ef_lib_event
 */
typedef struct t_sim_ef_lib_event
{
    struct t_sim_ef_lib_event *next_in_list;
    struct t_sim_ef_lib_data *lib_data;
    t_sim_ef_lib_input *input;
    int timeout;
    int expect_value; // 1 if the value is to be expected; 0 if it should differ
    t_sl_uint64 value;
} t_sim_ef_lib_event;

/*t t_sim_ef_lib_data
 */
typedef struct t_sim_ef_lib_data
{
    c_engine *engine;
    int num_inputs;
    int num_outputs;
    t_sl_uint64 cycle;
    t_sl_exec_file_lib_desc lib_desc;
    t_sim_ef_lib_input *inputs;
    t_sim_ef_lib_output *outputs;
} t_sim_ef_lib_data;

/*t t_se_engine_simulation_callback
 */
typedef struct t_se_engine_simulation_callback
{
     struct t_se_engine_simulation_callback *next_in_list;
     t_se_engine_simulation_callback_fn callback;
     void *handle;
     void *handle_b;
} t_se_engine_simulation_callback;

/*t t_monitor_display_callback_data
 */
typedef struct t_monitor_display_callback_data
{
     struct t_monitor_display_callback_data *next_in_list;
     class c_engine *engine;
     struct t_sl_exec_file_data *exec_file_data;
     t_sl_exec_file_value *args;
     int line_number;
} t_monitor_display_callback_data;

/*a Static function declarations
 */
static t_sl_exec_file_eval_fn ef_fn_eval_cycle;
static t_sl_exec_file_eval_fn ef_fn_eval_global_cycle;
static t_sl_exec_file_eval_fn ef_fn_eval_global_signal_value;
static t_sl_exec_file_eval_fn ef_fn_eval_global_signal_value_string;

/*a Statics
 */
/*v cmd_*
 */
enum
{
    cmd_global_monitor_event,
    cmd_bfm_wait,
};

/*v fn_*
 */
enum {
    fn_cycle,
    fn_global_cycle,
    fn_global_signal_value,
    fn_global_signal_value_string,
};

/*v sim_file_cmds
 */
static t_sl_exec_file_cmd sim_file_cmds[] =
{
     {cmd_global_monitor_event,          2, "global_monitor_event", "ss", "  global_monitor_event <global signal> <event>"},
     {cmd_bfm_wait,                      1, "bfm_wait", "i", "bfm_wait <integer>"},
     {sl_exec_file_cmd_none, 0, NULL, NULL, NULL }
};

/*v sim_file_fns
 */
static t_sl_exec_file_fn sim_file_fns[] =
{
    {fn_cycle,                       "bfm_cycle",            'i', "", "bfm_cycle()", ef_fn_eval_cycle },
     {fn_global_cycle,               "global_cycle",         'i', "", "global_cycle()", ef_fn_eval_global_cycle },
     {fn_global_signal_value,        "global_signal_value",  'i', "s", "global_signal_value( signal )", ef_fn_eval_global_signal_value },
     {fn_global_signal_value_string, "global_signal_value_string",  's', "s", "global_signal_value_string( signal )", ef_fn_eval_global_signal_value_string },
     {sl_exec_file_fn_none, NULL,     0,   NULL, NULL },
};

/*v ef_bfm_support_object_methods - Exec file bfm_support object methods
 */
static t_sl_exec_file_method ef_bfm_support_object_methods[] =
{
    SL_EXEC_FILE_METHOD_NONE
};

/*v ef_input_object_methods - Exec file object methods
 */
static t_sl_exec_file_method_fn ef_method_eval_input_wait_for_value;
static t_sl_exec_file_method_fn ef_method_eval_input_wait_for_change;
static t_sl_exec_file_method_fn ef_method_eval_input_value;
static t_sl_exec_file_method_fn ef_method_eval_input_width;
static t_sl_exec_file_method ef_input_object_methods[] =
{
    {"value",            'i', 0, "",  "value() - return the value of a signal", ef_method_eval_input_value, NULL },
    {"width",            'i', 0, "",  "width() - return the width of a signal", ef_method_eval_input_width, NULL },
    {"wait_for_value",    0, 1, "ii",  "wait_for_value(<value>[,<timeout>]) - wait for an input to reach a specified value with an optional timeout", ef_method_eval_input_wait_for_value, NULL },
    {"wait_for_change",   0, 1, "i",   "wait_for_change([<timeout>]) - wait for an input to change with an optional timeout", ef_method_eval_input_wait_for_change, NULL },
    SL_EXEC_FILE_METHOD_NONE
};

/*v ef_output_object_methods - Exec file object methods
 */
static t_sl_exec_file_method_fn ef_method_eval_output_reset;
static t_sl_exec_file_method_fn ef_method_eval_output_drive;
static t_sl_exec_file_method_fn ef_method_eval_output_width;
static t_sl_exec_file_method ef_output_object_methods[] =
{
    {"drive",            0, 1, "i",  "drive(<value>) - drive an output off the clock edge", ef_method_eval_output_drive, NULL },
    {"reset",            0, 1, "i",  "reset(<value) - drive an output immediately - for use in initial code", ef_method_eval_output_reset, NULL },
    {"width",            'i', 0, "",  "width() - return the width of a signal", ef_method_eval_output_width, NULL },
    SL_EXEC_FILE_METHOD_NONE
};

/*a Cycle simulation exec_file enhancement functions and methods
 */
/*f ef_output_object_free */
static t_sl_error_level ef_output_object_free(t_sl_exec_file_object_cb *obj_cb)
{
    // fprintf(stderr,"Free output name %p\n",obj_cb->object_desc->name);
    // fprintf(stderr,"Free output name %s\n",obj_cb->object_desc->name);
    free((void *)obj_cb->object_desc->name);
    return error_level_okay;
}

/*f ef_input_object_free */
static t_sl_error_level ef_input_object_free(t_sl_exec_file_object_cb *obj_cb)
{
    // fprintf(stderr,"Free input name %p\n",obj_cb->object_desc->name);
    // fprintf(stderr,"Free input name %s\n",obj_cb->object_desc->name);
    free((void *)obj_cb->object_desc->name);
    return error_level_okay;
}

/*f ef_input_object_event_callback
 */
static int ef_input_object_event_callback( t_sl_exec_file_wait_cb *wait_cb )
{
//    t_sim_ef_lib_event *lib_event = (t_sim_ef_lib_event *)event;
    t_sim_ef_lib_input *input;
    t_sim_ef_lib_data *lib_data;
    lib_data = (t_sim_ef_lib_data *)wait_cb->args[ wait_cb_arg_lib_data ].pointer;
    input = (t_sim_ef_lib_input *)wait_cb->args[ wait_cb_arg_input ].pointer;
    int fired;

    WHERE_I_AM;

    fired = 0;
    if (input)
    {
        int equal;
        equal = (input->value == wait_cb->args[wait_cb_arg_value].uint64);
        if (equal && wait_cb->args[wait_cb_arg_expect_value].uint64) fired=1;
        if (!equal && !wait_cb->args[wait_cb_arg_expect_value].uint64) fired=1;
    }

    if ( (wait_cb->args[wait_cb_arg_timeout].uint64!=-1ULL) &&
         (wait_cb->args[wait_cb_arg_timeout].uint64<=lib_data->cycle) )
    {
        fired = 1;
    }

    return fired;
}

/*f static exec_file_cmd_handler
 */
static t_sl_error_level exec_file_cmd_handler( struct t_sl_exec_file_cmd_cb *cmd_cb, void *handle )
{
    t_sim_ef_lib_data *lib_data;
    WHERE_I_AM;
    lib_data = (t_sim_ef_lib_data *)(handle);
    if (!lib_data->engine->simulation_handle_exec_file_command( cmd_cb ))
        return error_level_serious;
    return error_level_okay;
}

/*f ef_method_eval_input_wait_for_value
 */
static t_sl_error_level ef_method_eval_input_wait_for_value( t_sl_exec_file_cmd_cb *cmd_cb, void *object_handle, t_sl_exec_file_object_desc *object_desc, t_sl_exec_file_method *method )
{
    t_sim_ef_lib_input *input;
    t_sim_ef_lib_data *lib_data;
    WHERE_I_AM;
    input = (t_sim_ef_lib_input *)(object_desc->handle);
    lib_data = input->lib_data;

    if (input->value!=sl_exec_file_eval_fn_get_argument_integer( cmd_cb->file_data, cmd_cb->args, 0 ))
    {
        t_sl_exec_file_wait_cb wait_cb;

        wait_cb.args[ wait_cb_arg_lib_data ].pointer = (void *)lib_data;
        wait_cb.args[ wait_cb_arg_input ].pointer = (void *)input;
        wait_cb.args[ wait_cb_arg_value ].uint64 = sl_exec_file_eval_fn_get_argument_integer( cmd_cb->file_data, cmd_cb->args, 0 );
        wait_cb.args[ wait_cb_arg_expect_value ].uint64 = 1;
        wait_cb.args[ wait_cb_arg_timeout ].uint64 = -1ULL;
        if (cmd_cb->num_args>1)
        {
            wait_cb.args[ wait_cb_arg_timeout ].uint64 = sl_exec_file_eval_fn_get_argument_integer( cmd_cb->file_data, cmd_cb->args, 1 );
            if (wait_cb.args[ wait_cb_arg_timeout ].uint64 != -1ULL)
            {
                wait_cb.args[ wait_cb_arg_timeout ].uint64 += lib_data->cycle;
            }
        }
        sl_exec_file_thread_wait_on_callback( cmd_cb, ef_input_object_event_callback, &wait_cb );

    }
    return error_level_okay;
}

/*f ef_method_eval_input_wait_for_change
 */
static t_sl_error_level ef_method_eval_input_wait_for_change( t_sl_exec_file_cmd_cb *cmd_cb, void *object_handle, t_sl_exec_file_object_desc *object_desc, t_sl_exec_file_method *method )
{
    t_sim_ef_lib_input *input;
    t_sim_ef_lib_data *lib_data;
    WHERE_I_AM;
    input = (t_sim_ef_lib_input *)(object_desc->handle);
    lib_data = input->lib_data;

    t_sl_exec_file_wait_cb wait_cb;

    wait_cb.args[ wait_cb_arg_lib_data ].pointer = (void *)lib_data;
    wait_cb.args[ wait_cb_arg_input ].pointer = (void *)input;
    wait_cb.args[ wait_cb_arg_value ].uint64 = input->value;
    wait_cb.args[ wait_cb_arg_expect_value ].uint64 = 0;
    wait_cb.args[ wait_cb_arg_timeout ].uint64 = -1ULL;
    if (cmd_cb->num_args>0)
    {
        wait_cb.args[ wait_cb_arg_timeout ].uint64 = sl_exec_file_eval_fn_get_argument_integer( cmd_cb->file_data, cmd_cb->args, 0 );
        if (wait_cb.args[ wait_cb_arg_timeout ].uint64 != -1ULL)
        {
            wait_cb.args[ wait_cb_arg_timeout ].uint64 += lib_data->cycle;
        }
    }
    sl_exec_file_thread_wait_on_callback( cmd_cb, ef_input_object_event_callback, &wait_cb );
    return error_level_okay;
}

/*f ef_method_eval_input_value
 */
static t_sl_error_level ef_method_eval_input_value( t_sl_exec_file_cmd_cb *cmd_cb, void *object_handle, t_sl_exec_file_object_desc *object_desc, t_sl_exec_file_method *method )
{
    t_sim_ef_lib_input *input;
    WHERE_I_AM;
    input = (t_sim_ef_lib_input *)(object_desc->handle);

    //fprintf(stderr,"%5d%20s:%lld\n",0,input->name, input->value);
    if (!sl_exec_file_eval_fn_set_result( cmd_cb->file_data, input->value))
        return error_level_fatal;
    return error_level_okay;
}

/*f ef_method_eval_input_width
 */
static t_sl_error_level ef_method_eval_input_width( t_sl_exec_file_cmd_cb *cmd_cb, void *object_handle, t_sl_exec_file_object_desc *object_desc, t_sl_exec_file_method *method )
{
    t_sim_ef_lib_input *input;
    WHERE_I_AM;
    input = (t_sim_ef_lib_input *)(object_desc->handle);

    //fprintf(stderr,"%5d%20s:%lld\n",0,input->name, input->value);
    if (!sl_exec_file_eval_fn_set_result( cmd_cb->file_data, (t_sl_uint64)(input->width)))
        return error_level_fatal;
    return error_level_okay;
}

/*f ef_method_eval_output_width
 */
static t_sl_error_level ef_method_eval_output_width( t_sl_exec_file_cmd_cb *cmd_cb, void *object_handle, t_sl_exec_file_object_desc *object_desc, t_sl_exec_file_method *method )
{
    t_sim_ef_lib_output *output;
    WHERE_I_AM;
    output = (t_sim_ef_lib_output *)(object_desc->handle);

    //fprintf(stderr,"%5d%20s:%lld\n",0,output->name, output->value);
    if (!sl_exec_file_eval_fn_set_result( cmd_cb->file_data, (t_sl_uint64)(output->width)))
        return error_level_fatal;
    return error_level_okay;
}

/*f ef_method_eval_output_reset
 */
static t_sl_error_level ef_method_eval_output_reset( t_sl_exec_file_cmd_cb *cmd_cb, void *object_handle, t_sl_exec_file_object_desc *object_desc, t_sl_exec_file_method *method )
{
    t_sim_ef_lib_output *output;
    WHERE_I_AM;
    output = (t_sim_ef_lib_output *)(object_desc->handle);

    output->next_data = sl_exec_file_eval_fn_get_argument_integer( cmd_cb->file_data, cmd_cb->args, 0 );
    output->data = sl_exec_file_eval_fn_get_argument_integer( cmd_cb->file_data, cmd_cb->args, 0 ); // reset has immediate effect
    return error_level_okay;
}

/*f ef_method_eval_output_drive
 */
static t_sl_error_level ef_method_eval_output_drive( t_sl_exec_file_cmd_cb *cmd_cb, void *object_handle, t_sl_exec_file_object_desc *object_desc, t_sl_exec_file_method *method )
{
    t_sim_ef_lib_output *output;
    WHERE_I_AM;
    output = (t_sim_ef_lib_output *)(object_desc->handle);

    output->next_data = sl_exec_file_eval_fn_get_argument_integer( cmd_cb->file_data, cmd_cb->args, 0 );
    return error_level_okay;
}

/*f ef_bfm_support_library_free */
static t_sl_error_level ef_bfm_support_library_free(t_sl_exec_file_lib_cb *lib_cb)
{
    auto lib_data = (t_sim_ef_lib_data *)(lib_cb->lib_desc->handle);
    // fprintf(stderr,"Free library - must free input and outputs names from lib_data\n");
    for (int i=0; i<lib_data->num_inputs; i++) {
        if (lib_data->inputs[i].name) free((void *)(lib_data->inputs[i].name));
    }
    for (int i=0; i<lib_data->num_outputs; i++) {
        if (lib_data->outputs[i].name) free((void *)(lib_data->outputs[i].name));
    }
    free(lib_data);
    return error_level_okay;
}

/*f ef_bfm_support_object_reset
 */
static t_sl_error_level ef_bfm_support_object_reset( t_sl_exec_file_object_cb *obj_cb )
{
    t_sim_ef_lib_data *lib_data;
    lib_data = (t_sim_ef_lib_data *)(obj_cb->object_desc->handle);
    int i;
    for (i=0; i<lib_data->num_inputs; i++)
    {
    }
    for (i=0; i<lib_data->num_outputs; i++)
    {
        lib_data->outputs[i].data = 0;
        lib_data->outputs[i].next_data = 0;
    }
    lib_data->cycle = 0;
    return error_level_okay;
}

/*f ef_bfm_support_object_message_handler
 */
static t_sl_error_level ef_bfm_support_object_message_handler( t_sl_exec_file_object_cb *obj_cb )
{
    t_sim_ef_lib_data *lib_data;
    lib_data = (t_sim_ef_lib_data *)(obj_cb->object_desc->handle);

    SL_DEBUG( sl_debug_level_verbose_info, "BFM support test harness message %s", obj_cb->data.message.message );
    if (!strcmp(obj_cb->data.message.message,"preclock"))
    {
        int i;
        for (i=0; i<lib_data->num_inputs; i++)
        {
            lib_data->inputs[i].value = lib_data->inputs[i].data[0];
            //fprintf(stderr,"%5d:%20s:%lld\n",lib_data->cycle,lib_data->inputs[i].name, lib_data->inputs[i].value);
        }
        for (i=0; i<lib_data->num_outputs; i++)
        {
            lib_data->outputs[i].next_data = lib_data->outputs[i].data;
        }
        return error_level_okay;
    }

    if (!strcmp(obj_cb->data.message.message,"clock"))
    {
        int i;
        for (i=0; i<lib_data->num_outputs; i++)
            lib_data->outputs[i].data = lib_data->outputs[i].next_data;
        lib_data->cycle++;
    }
    return error_level_serious;
}

/*f c_engine::simulation_add_exec_file_enhancements
  Add inputs/outputs to a BFM (internal or external) such as the test_harness, based on options
  Relies on the BFM having an sl_exec_file
  Python-script BFMs do not
 */
int c_engine::simulation_add_exec_file_enhancements( struct t_sl_exec_file_data *file_data, void *engine_handle, const char *clock, int posedge )
{
    int result;
    t_sim_ef_lib_data *lib_data;
    const char *signal_prefix;
    char *input_string;
    char **inputs;
    int *input_widths;
    int num_inputs;
    char *output_string;
    char **outputs;
    int *output_widths;
    int num_outputs;
    int i, j;

    if (!file_data)
        return 0;

    result = 1;
    lib_data = NULL;
    inputs = NULL;
    input_widths = NULL;
    outputs = NULL;
    output_widths = NULL;
    num_inputs = 0;
    num_outputs = 0;
    output_string = NULL;
    input_string = NULL;
    signal_prefix = NULL;

    if (engine_handle && clock)
    {
        signal_prefix = get_option_string( engine_handle, "signal_object_prefix", "" );
        input_string = sl_str_alloc_copy(get_option_string( engine_handle, "inputs", "" ));
        output_string = sl_str_alloc_copy(get_option_string( engine_handle, "outputs", "" ));

        inputs = sl_tokenize_line( input_string, &num_inputs );
        input_widths = (int *)malloc(sizeof(int)*num_inputs);
        for (i=0; i<num_inputs; i++)
        {
            input_widths[i] = 1;
            for (j=0; inputs[i][j] && (inputs[i][j]!='['); j++);
            if (inputs[i][j])
            {
                inputs[i][j]=0;
                if (!sl_integer_from_token( inputs[i]+j+1, &input_widths[i]))
                {
                    fprintf(stderr,"NNE:integer in width of arg '%s' to BFM support was not an integer at all %s\n", inputs[i], inputs[i]+j+1);
                    result = 0;
                    input_widths[i]=1;
                }
                if ((input_widths[i]>64) || (input_widths[i]<1))
                {
                    fprintf(stderr,"NNE:bad width of arg '%s' to BFM support - needs to be between 1 and 64\n", inputs[i]);
                    result = 0;
                    input_widths[i] = 1;
                }
            }
        }

        outputs = sl_tokenize_line( output_string, &num_outputs );
        output_widths = (int *)malloc(sizeof(int)*num_outputs);
        for (i=0; i<num_outputs; i++)
        {
            output_widths[i] = 1;
            for (j=0; outputs[i][j] && (outputs[i][j]!='['); j++);
            if (outputs[i][j])
            {
                outputs[i][j]=0;
                if (!sl_integer_from_token( outputs[i]+j+1, &output_widths[i]))
                {
                    fprintf(stderr,"NNE:integer in width of arg '%s' to test harness was not an integer at all %s\n", outputs[i], outputs[i]+j+1);
                    output_widths[i] = 1;
                }
                if ((output_widths[i]>64) || (output_widths[i]<1))
                {
                    fprintf(stderr,"NNE:bad width of arg '%s' to test harness - needs to be between 1 and 64\n", outputs[i]);
                    output_widths[i] = 1;
                }
            }
        }
    }

    lib_data = (t_sim_ef_lib_data *)malloc(sizeof(t_sim_ef_lib_data)+sizeof(t_sim_ef_lib_input)*num_inputs+sizeof(t_sim_ef_lib_output)*num_outputs);
    if (lib_data)
    {
        lib_data->num_inputs = num_inputs;
        lib_data->num_outputs = num_outputs;
        lib_data->inputs = (t_sim_ef_lib_input *)(lib_data+1);
        lib_data->outputs = (t_sim_ef_lib_output *)(lib_data->inputs+num_inputs);
        for (i=0; i<num_inputs; i++)
        {
            t_sl_exec_file_object_desc object_desc;
            char buffer[512];

            lib_data->inputs[i].lib_data = lib_data;
            lib_data->inputs[i].name = sl_str_alloc_copy( inputs[i] );
            lib_data->inputs[i].width = input_widths[i];
            register_input_signal( engine_handle, inputs[i], input_widths[i], &lib_data->inputs[i].data );
            register_input_used_on_clock( engine_handle, inputs[i], clock, posedge );

            memset(&object_desc,0,sizeof(object_desc));
            object_desc.version = sl_ef_object_version_checkpoint_restore;
            snprintf( buffer, sizeof(buffer), "%s%s", signal_prefix, inputs[i] );
            object_desc.name = sl_str_alloc_copy(buffer);
            // fprintf(stderr,"Malloc input name %p %s\n",object_desc.name, object_desc.name);
            object_desc.handle = (void *)&(lib_data->inputs[i]);
            object_desc.methods = ef_input_object_methods;
            object_desc.free_fn = ef_input_object_free;
            sl_exec_file_add_object_instance( file_data, &object_desc );
        }
        for (i=0; i<num_outputs; i++)
        {
            t_sl_exec_file_object_desc object_desc;
            char buffer[512];

            lib_data->outputs[i].lib_data = lib_data;
            lib_data->outputs[i].name = sl_str_alloc_copy( outputs[i] );
            lib_data->outputs[i].width = output_widths[i];
            lib_data->outputs[i].data = 0;
            lib_data->outputs[i].next_data = 0;
            register_output_signal( engine_handle, outputs[i], output_widths[i], &lib_data->outputs[i].data );
            register_output_generated_on_clock( engine_handle, outputs[i], clock, posedge );
            // fprintf(stderr, "Added signal %s at %p data now 0x%08x\n", outputs[i], &lib_data->outputs[i].data, lib_data->outputs[i].data );

            memset(&object_desc,0,sizeof(object_desc));
            object_desc.version = sl_ef_object_version_checkpoint_restore;
            snprintf( buffer, sizeof(buffer), "%s%s", signal_prefix, outputs[i] );
            object_desc.name = sl_str_alloc_copy(buffer);
            // fprintf(stderr,"Malloc output name %p %s\n",object_desc.name, object_desc.name);
            object_desc.handle = (void *)&(lib_data->outputs[i]);
            object_desc.methods = ef_output_object_methods;
            object_desc.free_fn = ef_output_object_free;
            sl_exec_file_add_object_instance( file_data, &object_desc );
        }
        if (engine_handle && clock)
        {
            const char *ef_completion_prefix;
            t_sl_exec_file_completion *completion;
            completion = sl_exec_file_completion( file_data );
            ef_completion_prefix = get_option_string( engine_handle, "ef_completion_prefix", "<none>" );
            if (strcmp(ef_completion_prefix,"<none>"))
            {
                char buffer[256];

                snprintf( buffer, sizeof(buffer), "%sfinished", ef_completion_prefix );
                register_output_signal( engine_handle, buffer, 1, &(completion->finished) );
                register_output_generated_on_clock( engine_handle, buffer, clock, posedge );

                snprintf( buffer, sizeof(buffer), "%spassed", ef_completion_prefix );
                register_output_signal( engine_handle, buffer, 1, &(completion->passed) );
                register_output_generated_on_clock( engine_handle, buffer, clock, posedge );

                snprintf( buffer, sizeof(buffer), "%sfailed", ef_completion_prefix );
                register_output_signal( engine_handle, buffer, 1, &(completion->failed) );
                register_output_generated_on_clock( engine_handle, buffer, clock, posedge );

                snprintf( buffer, sizeof(buffer), "%sreturn_code", ef_completion_prefix );
                register_output_signal( engine_handle, buffer, 64, &(completion->return_code) );
                register_output_generated_on_clock( engine_handle, buffer, clock, posedge );
            }
        }
    }
    if (lib_data)
    {
        lib_data->engine = this;
        lib_data->lib_desc.version = sl_ef_lib_version_cmdcb;
        lib_data->lib_desc.library_name = "cdlsim_sim";
        lib_data->lib_desc.handle = (void *) lib_data;
        lib_data->lib_desc.cmd_handler = exec_file_cmd_handler;
        lib_data->lib_desc.file_cmds = sim_file_cmds;
        lib_data->lib_desc.file_fns = sim_file_fns;
        lib_data->lib_desc.free_fn = ef_bfm_support_library_free;
        result = sl_exec_file_add_library( file_data, &lib_data->lib_desc );

        t_sl_exec_file_object_desc object_desc;
        memset(&object_desc,0,sizeof(object_desc));
        object_desc.version = sl_ef_object_version_checkpoint_restore;
        object_desc.name = "bfm_exec_file_support";
        object_desc.handle = (void *)lib_data;
        object_desc.message_handler = ef_bfm_support_object_message_handler;
        object_desc.reset_fn = ef_bfm_support_object_reset;
        object_desc.methods = ef_bfm_support_object_methods;
        object_desc.free_fn = NULL;
        sl_exec_file_add_object_instance( file_data, &object_desc );
    }

    if (engine_handle && clock)
    {
        free(input_string);
        free(output_string);
    }
    if (inputs) free(inputs);
    if (input_widths) free(input_widths);
    if (outputs) free(outputs);
    if (output_widths) free(output_widths);
    return result;
}

/*f monitor_event_callback
 */
static void monitor_event_callback( void *handle, void *handle_b )
{
     
     

     WHERE_I_AM;
     //t_sl_exec_file_data *file_data = (t_sl_exec_file_data *)handle;
     t_sl_ef_lib_event_ptr event = (t_sl_ef_lib_event_ptr) handle_b;
     sl_ef_lib_event_fire( event );
}

#if 0
/*f monitor_display_callback
 */
static void monitor_display_callback( void *handle, void *handle_b )
{
     t_monitor_display_callback_data *data;
     char *text;

     data = (t_monitor_display_callback_data *)handle;
     sl_exec_file_evaluate_arguments( data->exec_file_data, "monitor_display", data->line_number, data->args+1, SL_EXEC_FILE_MAX_CMD_ARGS-1 );
     text = sl_exec_file_vprintf( data->exec_file_data, data->args+1, SL_EXEC_FILE_MAX_CMD_ARGS-1 );

     data->engine->add_message( (void *)"simulation",
                                                 error_level_info,
                                                 error_number_sl_message, error_id_sl_exec_file_get_next_cmd,
                                                 error_arg_type_malloc_string, text,
                                                 error_arg_type_malloc_filename, sl_exec_file_filename(data->exec_file_data),
                                                 error_arg_type_line_number, data->line_number,
                                                 error_arg_type_none );
     free(text);
}
#endif

/*f c_engine::simulation_handle_exec_file_command
  returns 0 if it did not handle
  returns 1 if it handled it
 */
int c_engine::simulation_handle_exec_file_command( struct t_sl_exec_file_cmd_cb *cmd_cb )
{
    WHERE_I_AM;

    switch (cmd_cb->cmd)
    {
    case cmd_bfm_wait:
    {
        int timeout;
        WHERE_I_AM;
        timeout = sl_exec_file_eval_fn_get_argument_integer( cmd_cb->file_data, cmd_cb->args, 0 );
        WHERE_I_AM;
        if (timeout>0)
        {
        WHERE_I_AM;
            t_sim_ef_lib_data *lib_data;
            lib_data = ((t_sim_ef_lib_data *)(cmd_cb->lib_desc->handle));
        WHERE_I_AM;

            t_sl_exec_file_wait_cb wait_cb;
        WHERE_I_AM;

            wait_cb.args[ wait_cb_arg_lib_data ].pointer = (void *)lib_data;
            wait_cb.args[ wait_cb_arg_input ].pointer = NULL;
            wait_cb.args[ wait_cb_arg_value ].uint64 = 0;
            wait_cb.args[ wait_cb_arg_expect_value ].uint64 = 0;
            wait_cb.args[ wait_cb_arg_timeout ].uint64 = lib_data->cycle+timeout;
        WHERE_I_AM;
            sl_exec_file_thread_wait_on_callback( cmd_cb, ef_input_object_event_callback, &wait_cb );
        WHERE_I_AM;
        }
        WHERE_I_AM;
        return 1;
    }
    case cmd_global_monitor_event:
    {
        WHERE_I_AM;
        t_sl_ef_lib_event_ptr event;
        event = NULL;
        sl_exec_file_send_message_to_object( cmd_cb->file_data,
                                             sl_exec_file_eval_fn_get_argument_string( cmd_cb->file_data, cmd_cb->args, 1 ),
                                             "event_handle", (void *)&event );
        if (event)
        {
            add_monitor_callback( sl_exec_file_eval_fn_get_argument_string( cmd_cb->file_data, cmd_cb->args, 0 ),
                                  monitor_event_callback,
                                  (void *)cmd_cb->file_data,
                                  (void *)event );
        }
        WHERE_I_AM;
        return 1;
    }
    default:
        break;
    }
    WHERE_I_AM;
    return 0;
}

/*a Exec file evaluation functions
 */
/*f ef_fn_eval_cycle
 */
static int ef_fn_eval_cycle( void *handle, t_sl_exec_file_data *file_data, t_sl_exec_file_value *args )
{
    t_sim_ef_lib_data *lib_data;
    WHERE_I_AM;
    lib_data = (t_sim_ef_lib_data *)(handle);

     sl_exec_file_eval_fn_set_result( file_data, (t_sl_uint64)(lib_data->cycle) );
     return 1;
}

/*f ef_fn_eval_global_cycle
 */
static int ef_fn_eval_global_cycle( void *handle, t_sl_exec_file_data *file_data, t_sl_exec_file_value *args )
{
    t_sim_ef_lib_data *lib_data;
    WHERE_I_AM;
    lib_data = (t_sim_ef_lib_data *)(handle);

     sl_exec_file_eval_fn_set_result( file_data, (t_sl_uint64)(lib_data->engine->cycle()) );
     return 1;
}

/*f ef_fn_eval_global_signal_value
 */
static int ef_fn_eval_global_signal_value( void *handle, t_sl_exec_file_data *file_data, t_sl_exec_file_value *args )
{
    t_sim_ef_lib_data *lib_data;
    WHERE_I_AM;
    lib_data = (t_sim_ef_lib_data *)(handle);

    c_engine *engine;
    t_se_interrogation_handle entity;
    t_engine_state_desc_type type;
    t_se_signal_value *datas[4];
    int sizes[4];

    engine = lib_data->engine;
    entity = engine->find_entity( sl_exec_file_eval_fn_get_argument_string( file_data, args, 0 ) );
    type = engine->interrogate_get_data_sizes_and_type( entity, datas, sizes );
    engine->interrogation_handle_free( entity );

    switch (type)
    {
    case engine_state_desc_type_bits:
    case engine_state_desc_type_fsm:
        if (sizes[0]<=64)
        {
            return sl_exec_file_eval_fn_set_result( file_data, datas[0][0] );
        }
        break;
    default:
        break;
    }
    return 0;
}

/*f ef_fn_eval_global_signal_value_string
 */
static int ef_fn_eval_global_signal_value_string( void *handle, t_sl_exec_file_data *file_data, t_sl_exec_file_value *args )
{
    t_sim_ef_lib_data *lib_data;
    WHERE_I_AM;
    lib_data = (t_sim_ef_lib_data *)(handle);

     c_engine *engine;
     char buffer[1024];
     t_se_interrogation_handle ih;

     engine = lib_data->engine;
     ih = engine->find_entity( sl_exec_file_eval_fn_get_argument_string( file_data, args, 0 ) );
     if (!engine->interrogate_get_entity_value_string( ih, buffer, sizeof(buffer) ))
         return 0;
     engine->interrogation_handle_free( ih );

     return sl_exec_file_eval_fn_set_result( file_data, buffer, 1 );
}

/*a Cycle simulation operation methods
 */
/*f c_engine::build_schedule
  for each clock
    for both edges (posedge, negedge)
      set all global signals valid, unchanged
      list preclock and clock fns to call, setting any signals generated on an edge to be changed
      mark all comb fns' outputs that depend on changed/invalid inputs as invalid, repeating until no more signals effected
      list all comb fns with invalid outputs that depend on changed valid inputs, marking their outputs as valid, repeating until no more comb fns added. This list needs to be forward (i.e. non-reverse) ordered.
      At this point all signals that changed are marked as valid and changed; for all module instances that have changed signals as inputs, add the propagate inputs functions (if any) to the list for the clock.
 */
t_sl_error_level c_engine::build_schedule( void )
{
    t_engine_clock *clk;
    int posedge;
    int cont, check, modules_to_check;
    t_engine_function *emi_sig;
    t_engine_signal *sig;
    t_engine_module_instance *emi;

    /*b Run through all the clocks
     */
    for (clk=global_clock_list; clk; clk=clk->next_in_list)
    {
        //fprintf(stderr,"********************************************************************************\nBuilding schedule for clock %s\n",clk->global_name);

        /*b Generate schedule remainder values and length of clock cycle
         */
        clk->cycle_length = clk->high_cycles + clk->low_cycles;
        if (clk->cycle_length) {
            clk->posedge_remainder = clk->delay % clk->cycle_length;
            clk->negedge_remainder = (clk->delay + clk->high_cycles) % clk->cycle_length;
        }

        /*b Generate function lists to call on negedge and posedge of the clock
         */
        for (posedge=0; posedge<2; posedge++) {
            /*b Mark all global signals valid and unchanged (as if just before the clock edge)
             */
            for (sig=global_signal_list; sig; sig=sig->next_in_list) {
                sig->changed = 0;
                sig->valid = 1;
            }

            /*b Check every use of the clock in the system (i.e. module clock inputs)
             */
            for (auto &efr:clk->clocks_list) {
                auto efrc = &efr->data.clock;

                /*b Add posedge/negedge preclock/clock functions if they exist, and mark any globals which derive from outputs generated by the clock edge as changed
                 */
                // This is a greedy add for prepreclock - the same emi may be added more than once if it has two clocks that trigger on the same edge
                auto emi = efr->module_instance;
                clk->prepreclock_set.push_back(&(emi->prepreclock_cb));
                if (posedge) {
                    if (efrc->posedge_preclock_fn) {
                        SL_DEBUG( sl_debug_level_info, "adding posedge preclock '%s.%s' fn delay %d remainder %d", emi->name, efr->name, clk->delay, clk->posedge_remainder);
                        clk->posedge.preclock.add(efrc->posedge_preclock_fn);
                    }
                    if (efrc->posedge_clock_fn) {
                        SL_DEBUG( sl_debug_level_info, "adding posedge clock '%s.%s' fn delay %d remainder %d", emi->name, efr->name, clk->delay, clk->posedge_remainder);
                        clk->posedge.clock.add(efrc->posedge_clock_fn);
                    }
                } else { // !posedge
                    if (efrc->negedge_preclock_fn) {
                        SL_DEBUG( sl_debug_level_info, "adding negedge preclock '%s.%s' fn delay %d remainder %d", emi->name, efr->name, clk->delay, clk->negedge_remainder);
                        clk->negedge.preclock.add(efrc->negedge_preclock_fn);
                    }
                    if (efrc->negedge_clock_fn) {
                        SL_DEBUG( sl_debug_level_info, "adding negedge clock '%s.%s' fn delay %d remainder %d", emi->name, efr->name, clk->delay, clk->negedge_remainder);
                        clk->negedge.clock.add(efrc->negedge_clock_fn);
                    }
                }
                for (emi_sig=emi->output_list; emi_sig; emi_sig=emi_sig->next_in_list)
                {
                    if ( (emi_sig->data.output.generated_by_clock == efr) &&
                         (emi_sig->data.output.drives) )
                    {
                        t_engine_signal_reference *sig_ref;
                        t_engine_signal *sig;
                        for (sig_ref = emi_sig->data.output.drives; sig_ref; sig_ref=sig_ref->next_in_list)
                        {
                            sig = sig_ref->signal;
                            sig->changed = 1;
                            SL_DEBUG( sl_debug_level_verbose_info, "global signal '%s' (output '%s') changed by clock", sig->global_name, emi_sig->name );
                        }
                    }
                }
            }

            /*b propagate changed and invalid inputs of comb fns as invalid outputs (not necessarily changed yet), through chains of combinatorial modules
             */
            //fprintf(stderr,"Propagating changed and invalid inputs of combs\n");
            cont = 1;
            while (cont) {
                cont = 0;
                for (emi=module_instance_list; emi; emi=emi->next_instance) { // Run through all instances that have a combinatorial component
                    if ((!emi->parent_instance) && (!emi->comb_cb.empty())) {
                        check = 0; // Find out if the global driver of any input to the instance that is used combinatorially is not yet valid or has changed; if so, set check to 1
                        for (emi_sig = emi->input_list; (!check) && emi_sig; emi_sig=emi_sig->next_in_list) {
                            if (emi_sig->data.input.driven_by) {
                                //fprintf(stderr,"check input %s:%s:comb %d:valid %d:changed %d\n",emi->full_name,emi_sig->name,emi_sig->data.input.combinatorial,emi_sig->data.input.driven_by->valid,emi_sig->data.input.driven_by->changed);
                                SL_DEBUG( sl_debug_level_verbose_info, "try to check module '%s', input '%s', global '%s' (v %d c %d)", emi->name, emi_sig->name, emi_sig->data.input.driven_by->global_name, emi_sig->data.input.driven_by->valid, emi_sig->data.input.driven_by->changed );
                                if ( (emi_sig->data.input.combinatorial) &&
                                     ((!emi_sig->data.input.driven_by->valid) || (emi_sig->data.input.driven_by->changed)) )
                                {
                                    check=1;
                                    SL_DEBUG( sl_debug_level_verbose_info, "need to check module '%s' as input '%s' is tied to something that may have changed", emi->name, emi_sig->name );
                                }
                            }
                        }
                        //fprintf(stderr,"propagate invalids %s %d\n",emi->full_name,check);
                        if (check) // There is a combinatorial component to this instance whose inputs have changed or are invalid, so mark the globals the outputs drive as invalid
                        {
                            for (emi_sig = emi->output_list; emi_sig; emi_sig=emi_sig->next_in_list)
                            {
                                //fprintf(stderr,"check output is valid %s:%s:comb %d:valid %d\n",emi->full_name,emi_sig->name,emi_sig->data.output.combinatorial,emi_sig->data.output.drives?emi_sig->data.output.drives->signal->valid:-1);
                                if ( (emi_sig->data.output.combinatorial) &&
                                     (emi_sig->data.output.drives) &&
                                     (emi_sig->data.output.drives->signal->valid) ) // All the globals driven by the output should be valid if any is; we do this test to determine if we should assert 'cont', i.e. changes have been made
                                {
                                    //fprintf(stderr,"make invalid %s:%s\n",emi->full_name,emi_sig->name);
                                    t_engine_signal_reference *sig_ref;
                                    t_engine_signal *sig;
                                    for (sig_ref = emi_sig->data.output.drives; sig_ref; sig_ref=sig_ref->next_in_list)
                                    {
                                        sig = sig_ref->signal;
                                        sig->valid = 0;
                                    }
                                    cont=1;
                                }
                            }
                        }
                    }
                }
            }

            /*b list all comb fns with an invalid output that depend on VALID inputs, marking their outputs as changed and valid, repeating until no more comb fns added. This list needs to be forward (i.e. non-reverse) ordered.
             */
            cont = 1;
            while (cont) {
                cont = 0;
                modules_to_check = 0;
                for (emi=module_instance_list; emi; emi=emi->next_instance) { // For all module instances with a combinatorial component
                    if ((!emi->parent_instance) && (!emi->comb_cb.empty())) {
                        check = 0; // Determine if any of its outputs are not valid; assert check if 1 (otherwise the instance does not need handling)
                        for (emi_sig = emi->output_list; (!check) && emi_sig; emi_sig=emi_sig->next_in_list) {
                            //fprintf(stderr,"comb check %s:%s:comb %d:valid %d\n",emi->full_name,emi_sig->name,emi_sig->data.output.combinatorial,emi_sig->data.output.drives?emi_sig->data.output.drives->signal->valid:-1);
                            if ( (emi_sig->data.output.combinatorial) &&
                                 (emi_sig->data.output.drives) &&
                                 (!emi_sig->data.output.drives->signal->valid) ) { // All globals driven by this output should have the same validity, so we use the first in the list
                                check=1;
                            }
                        }
                        if (!check) {
                            continue;
                        }
                        modules_to_check++;
                        check = 1; // Determine if all the combinatorially-used globally driven inputs are now valid; set to zero if not
                        for (emi_sig = emi->input_list; (check) && emi_sig; emi_sig=emi_sig->next_in_list) {
                            if ( (emi_sig->data.input.combinatorial) &&
                                 (emi_sig->data.input.driven_by) ) {
                                if ( !emi_sig->data.input.driven_by->valid ) {
                                    check=0;
                                }
                            }
                        }
                        if (check) { // So some combinatorial outputs are not valid but all combinatorial inputs are; schedule the combinatorial function for this module and drive its outputs valid and changed
                            if (posedge) {
                                SL_DEBUG( sl_debug_level_info, "adding posedge comb '%s' fn", emi->name );
                                for (auto &x:emi->comb_cb) {
                                    clk->posedge.comb.add(x);
                                }
                            } else {
                                SL_DEBUG( sl_debug_level_info, "adding negedge comb '%s' fn", emi->name );
                                for (auto &x:emi->comb_cb) {
                                    clk->negedge.comb.add(x);
                                }
                            }
                            for (emi_sig = emi->output_list; emi_sig; emi_sig=emi_sig->next_in_list) {
                                if ( (emi_sig->data.output.combinatorial) &&
                                     (emi_sig->data.output.drives) &&
                                     (!emi_sig->data.output.drives->signal->valid) ) { // All globals driven by this output have the same validity, so we can test with just the first
                                    //fprintf(stderr,"make valid changed %s:%s\n",emi->full_name,emi_sig->name);
                                    t_engine_signal_reference *sig_ref;
                                    t_engine_signal *sig;
                                    for (sig_ref = emi_sig->data.output.drives; sig_ref; sig_ref=sig_ref->next_in_list) {
                                        sig = sig_ref->signal;
                                        sig->valid = 1;
                                        sig->changed = 1;
                                    }
                                }
                            }
                            cont = 1;
                        }
                    }
                }
            }

            /*b Now list all the input propagation functions for global modules that have CHANGED global signals as inputs
             */
            for (emi=module_instance_list; emi; emi=emi->next_instance) { // For all module instances with a propagation issue
                if ((!emi->parent_instance) && (!emi->propagate_cb.empty())) {
                    for (emi_sig = emi->input_list; emi_sig; emi_sig=emi_sig->next_in_list) {
                        if ( (emi_sig->data.input.driven_by) &&
                             (emi_sig->data.input.driven_by->changed) )
                            break;
                    }
                    if ((emi_sig) || 1) {
                        if (posedge) {
                            SL_DEBUG( sl_debug_level_info, "adding input propagation fn for module %s", emi->name );
                            for (auto &x:emi->propagate_cb) {
                                clk->posedge.propagate.add(x);
                            }
                        } else {
                            SL_DEBUG( sl_debug_level_info, "adding input propagation fn for module %s", emi->name );
                            for (auto &x:emi->propagate_cb) {
                                clk->negedge.propagate.add(x);
                            }
                        }
                    }
                }
            }
        }
    }
    return error_level_okay;
}

/*f c_engine::add_monitor_callback
 */
struct t_se_engine_monitor *c_engine::add_monitor_callback( const char *entity_name, t_se_engine_monitor_callback_fn callback, void *handle, void *handle_b )
{
     t_se_engine_monitor *monitor;
     t_se_interrogation_handle entity;
     t_engine_state_desc_type type;
     t_se_signal_value *data;
     int int_size;
     t_se_signal_value *datas[4];
     int sizes[4];

     entity = find_entity( entity_name );
     type = interrogate_get_data_sizes_and_type( entity, datas, sizes );

     int_size = 0;
     data = NULL;
     switch (type)
     {
     case engine_state_desc_type_bits:
     case engine_state_desc_type_fsm:
          data = datas[0];
          int_size = (sizes[0]+31)/32;
          break;
     default:
          break;
     }
     if (!data)
     {
          interrogation_handle_free( entity );
          return NULL;
     }

     monitor = (t_se_engine_monitor *)malloc(sizeof(t_se_engine_monitor)+int_size*sizeof(int));
     if (!monitor)
          return NULL;
     monitor->next_in_list = monitors;
     monitors = monitor;
     monitor->entity = entity;
     monitor->callback = callback;
     monitor->handle = handle;
     monitor->handle_b = handle_b;
     monitor->reset = 1;
     monitor->entity_data = (int *)data;
     monitor->int_size = int_size;
     return monitor;
}

/*f c_engine::simulation_add_callback
 */
struct t_se_engine_simulation_callback *c_engine::simulation_add_callback( t_se_engine_simulation_callback_fn callback, void *handle, void *handle_b )
{
     t_se_engine_simulation_callback *scb;

     scb = (t_se_engine_simulation_callback *)malloc(sizeof(t_se_engine_simulation_callback));
     if (!scb)
          return NULL;
     scb->next_in_list = simulation_callbacks;
     simulation_callbacks = scb;
     scb->callback = callback;
     scb->handle = handle;
     scb->handle_b = handle_b;
     return scb;
}

/*f c_engine::simulation_free_callback
 */
void c_engine::simulation_free_callback( struct t_se_engine_simulation_callback *scb )
{
     t_se_engine_simulation_callback **last_scb;

     last_scb = &simulation_callbacks;
     while ((*last_scb) && (*last_scb != scb))
     {
          last_scb = &((*last_scb)->next_in_list);
     }
     if (*last_scb)
     {
          *last_scb = scb->next_in_list;
     }
     free(scb);
}

/*f c_engine::reset_state
 */
void c_engine::reset_state( void )
{
    int i;
    t_engine_module_instance *emi;
    t_engine_clock *clk;
    t_se_engine_monitor *monitor;
    t_se_engine_simulation_callback *scb;

    /*b Reset internal state
     */
    cycle_number = 0;

    /*b Reset module instance state
      This is a two pass process
      In the first pass, all inputs to modules are assumed INVALID, and so must not be used.
      All outputs from modules MUST be valid after this first pass
      In the second pass, all inputs to modules are assumed VALID, and so may be used.
     */
    for (i=0; i<2; i++) {
        for (emi=module_instance_list; emi; emi=emi->next_instance ) {
            if (emi->parent_instance) continue; // Don't do submodules - they should be reset by their parents
            SL_DEBUG( sl_debug_level_info, "calling reset of %s", emi->name); 
            emi->reset_cb.invoke_all(i); // First pass for each is purely internal state, second allows for inputs to be used
        }
    }

    /*b For each clock assume both edges have occurred, and call the correct set of combinatorial functions
     */
    for (clk=global_clock_list; clk; clk=clk->next_in_list) {
        clk->posedge.comb.invoke_all();
        clk->negedge.comb.invoke_all();
    }

    /*b Reset all monitors
     */
    for (monitor = monitors; monitor; monitor=monitor->next_in_list)
    {
        monitor->reset = 0;
        memcpy(monitor->data, monitor->entity_data, sizeof(int)*monitor->int_size );
    }

    /*b Call all simulation callbacks
      */
     for (scb=simulation_callbacks; scb; scb=scb->next_in_list)
     {
          scb->callback( scb->handle, scb->handle_b );
     }

}

/*f c_engine::simulation_invoke_callbacks
 */
int c_engine::simulation_invoke_callbacks( void )
{
    t_se_engine_simulation_callback *scb;

    /*b Call all simulation callbacks
     */
    for (scb=simulation_callbacks; scb; scb=scb->next_in_list)
    {
        scb->callback( scb->handle, scb->handle_b );
    }

    return 1;
}

/*f c_engine::simulation_set_cycle
 */
void c_engine::simulation_set_cycle( int n )
{
    cycle_number = n;
}

/*f c_engine::step_cycles
  We assume the simulation is in an unknown state on entry
  This means that all clocked (cycle accurate) state is consistent
  But that any combinatorial (pre-register stuff) is potentially inconsistent
  To get the whole thing consistent, we need to run the combinatorial and preclock functions for everything

  Once consistent, we need only:
    1. Preclock an edge
    2. Clock the edge
    3. Resolve any combinatorials based on outputs based on that edge

  For
 */
t_sl_error_level c_engine::step_cycles( int cycles )
{
     t_engine_clock *clk;
     t_se_engine_monitor *monitor;
     t_se_engine_simulation_callback *scb;
     int i;
     int edge_occurred;
     int abort;

     /*b Debug
      */
     SL_DEBUG( sl_debug_level_info, "cycle at start of step is %d, stepping %d", cycle_number, cycles ) ;

     /*b Make simulation consistent
      */
     for (clk=global_clock_list; clk; clk=clk->next_in_list) {
        clk->posedge.comb.invoke_all();
        clk->negedge.comb.invoke_all();
     }
     for (clk=global_clock_list; clk; clk=clk->next_in_list) {
         for (auto &x:clk->prepreclock_set) { x->invoke_all(); }
     }
     for (clk=global_clock_list; clk; clk=clk->next_in_list)
     {     
        clk->posedge.propagate.invoke_all();
        clk->negedge.propagate.invoke_all();
     }

     /*b Loop through all the cycles
      */
     abort=0;
     for ( ; (cycles>0) && !abort; cycles-- )
     {

         /*b Debug
          */
         SL_DEBUG( sl_debug_level_verbose_info, "******************** cycle %d ********************", cycle_number ) ;

         /*b Run through all the clocks, determining if we are a posedge, negedge, or no edge on this cycle
          */
         edge_occurred = 0;
         for (clk=global_clock_list; clk; clk=clk->next_in_list) {
             clk->edge = 0;
             if (clk->cycle_length) {
                 if (cycle_number >= clk->delay) {
                     if ((cycle_number % clk->cycle_length)==clk->posedge_remainder) {
                         clk->edge = 1;
                         clk->next_value = 1;
                         edge_occurred = 1;
                     }
                     if ((cycle_number % clk->cycle_length)==clk->negedge_remainder) {
                         clk->edge = -1;
                         clk->next_value = 0;
                         edge_occurred = 1;
                     }
                 }
             }
         }

         /*b For each clock with an edge, call the correct set of prepreclock functions
          */
         for (clk=global_clock_list; clk; clk=clk->next_in_list) {
             if (clk->edge!=0) {
                 SL_DEBUG( sl_debug_level_verbose_info, "Preclock global clock %s %d",clk->global_name, clk->edge );
                 for (auto &x:clk->prepreclock_set) { x->invoke_all(); }
             }
         }

         /*b For each clock with an edge, call the correct set of preclock functions
          */
         for (clk=global_clock_list; clk; clk=clk->next_in_list) {
             if (clk->edge==1) { clk->posedge.preclock.invoke_all(); }
             else if (clk->edge==-1) { clk->negedge.preclock.invoke_all(); }
         }

         /*b For each clock with an edge, call the correct set of clock functions
          */
         for (clk=global_clock_list; clk; clk=clk->next_in_list)
         {
             if (clk->edge==1) { clk->posedge.clock.invoke_all(); }
             else if (clk->edge==-1) { clk->negedge.clock.invoke_all(); }
             clk->value = clk->next_value;
         }

         /*b For each clock with an edge, call the correct set of combinatorial functions
          */
         for (clk=global_clock_list; clk; clk=clk->next_in_list) {
             if (clk->edge==1) { clk->posedge.comb.invoke_all(); }
             else if (clk->edge==-1) { clk->negedge.comb.invoke_all(); }
         }

         /*b If an edge occurred and monitors or callbacks exist, then propagate inputs in modules that require it
           This is necessary for modules with submodules, where the inputs to submodules will not
           yet be valid as they may depend on other top level modules combinatorial outpts, but the
           submodule has not yet been called.
           This is resolved in normal simulation within the preclock edge functions, but for monitors
           and waveforms etc this propagation needs to be performed prior to the use of the inputs
         */
         if (1 && (edge_occurred && (monitors || simulation_callbacks))) {
             //fprintf(stderr,"Calling monitors %p\n",simulation_callbacks);
             for (clk=global_clock_list; clk; clk=clk->next_in_list) {
                 if (clk->edge==1) { clk->posedge.propagate.invoke_all(); }
                 else if (clk->edge==-1) { clk->negedge.propagate.invoke_all(); }
             }
         }

         /*b Check all monitors if an edge occurred, and therefore if we did anything...
          */
         for (monitor = monitors; edge_occurred && monitor; monitor=monitor->next_in_list) {
             if (monitor->reset) {
                 monitor->reset=0;
                 memcpy( monitor->data, monitor->entity_data, sizeof(int)*monitor->int_size);
             } else {
                 for (i=0; i<monitor->int_size; i++) {
                     if (memcmp(monitor->data, monitor->entity_data, sizeof(int)*monitor->int_size )) {
                         monitor->callback( monitor->handle, monitor->handle_b );
                         memcpy(monitor->data, monitor->entity_data, sizeof(int)*monitor->int_size );
                         break;
                     }
                 }
             }
         }

         /*b Call all simulation callbacks if an edge occurred
          */
         for (scb=simulation_callbacks; edge_occurred && scb; scb=scb->next_in_list) {
             if (scb->callback( scb->handle, scb->handle_b )<0) {
                 abort=1;
             }
         }

         /*b Done the loop - increment cycle_number
          */
         cycle_number++;
     }

     /*b Make simulation consistent
      */
     for (clk=global_clock_list; clk; clk=clk->next_in_list)
     {     
         clk->posedge.comb.invoke_all();
         clk->negedge.comb.invoke_all();
     }

     /*b Return okay
      */
     return error_level_okay;
}

/*f c_engine::write_profile
 */
void c_engine::write_profile( FILE *f )
{
    t_engine_clock *clk;
    /*b Output profile
     */
    for (clk=global_clock_list; clk; clk=clk->next_in_list)
    {
        fprintf(f,"Posedge clock %s length %d\n", clk->global_name, clk->cycle_length ); // Its clocks_list is an efr of all the clocks bound to this global
        // se_engine_function_call_display_stats_all( f, clk->posedge.clock );
        fprintf(f,"Negedge clock %s length %d\n", clk->global_name, clk->cycle_length );
        // se_engine_function_call_display_stats_all( f, clk->negedge.clock );
    }

    t_engine_module_instance *emi;
    for (emi=module_instance_list; emi; emi=emi->next_instance )
    {
        fprintf( f, "%15lf us clk, %15lf us comb %15lf us prop submodule %s since reset\n",
                 SL_TIMER_VALUE_US(emi->timer_clk_fns),
                 SL_TIMER_VALUE_US(emi->timer_comb_fns),
                 SL_TIMER_VALUE_US(emi->timer_propagate_fns),
                 emi->full_name
            );
    }
}

/*f c_engine::cycle
 */
int c_engine::cycle( void )
{
     return cycle_number;
}

/*f c_engine::simulation_assist_prepreclock_instance - used by VPI
 */
void c_engine::simulation_assist_prepreclock_instance( void *engine_handle, int posedge )
{
    simulation_assist_prepreclock_instance( engine_handle, posedge, NULL );
}

/*f c_engine::simulation_assist_preclock_instance - used by VPI
 */
void c_engine::simulation_assist_preclock_instance( void *engine_handle, int posedge )
{
    simulation_assist_preclock_instance( engine_handle, posedge, NULL );
}

/*f c_engine::simulation_assist_clock_instance - used by VPI
 */
void c_engine::simulation_assist_clock_instance( void *engine_handle, int posedge )
{
    simulation_assist_clock_instance( engine_handle, posedge, NULL );
}

/*f c_engine::simulation_assist_prepreclock_instance - used by VPI
 */
void c_engine::simulation_assist_prepreclock_instance( void *engine_handle, int posedge, const char *clock_name )
{
    auto emi = (t_engine_module_instance *)engine_handle;
    emi->prepreclock_cb.invoke_all();
}

/*f c_engine::simulation_assist_preclock_instance
 */
void c_engine::simulation_assist_preclock_instance( void *engine_handle, int posedge, const char *clock_name )
{
    t_engine_module_instance *emi;
    t_engine_function *emi_sig;

    emi = (t_engine_module_instance *)engine_handle;
    for (emi_sig=emi->clock_fn_list;emi_sig;emi_sig=emi_sig->next_in_list) {
        if ((!clock_name) || (!strcmp(clock_name, emi_sig->name))) {
            auto emck = &emi_sig->data.clock;
            if (posedge) {
                if (emck->posedge_preclock_fn) { emck->posedge_preclock_fn(); }
            } else {
                if (emck->negedge_preclock_fn) { emck->negedge_preclock_fn(); }
            }
        }
    }
}

/*f c_engine::simulation_assist_clock_instance
 */
void c_engine::simulation_assist_clock_instance( void *engine_handle, int posedge, const char *clock_name )
{
    t_engine_module_instance *emi;
    t_engine_function *emi_sig;

    emi = (t_engine_module_instance *) engine_handle;
    for ( emi_sig=emi->clock_fn_list; emi_sig; emi_sig=emi_sig->next_in_list ) {
        if ((!clock_name) || (!strcmp(clock_name, emi_sig->name))) {
            auto emck = &emi_sig->data.clock;
            if (posedge) {
                if (emck->posedge_clock_fn) { emck->posedge_clock_fn(); }
            } else {
                if (emck->negedge_clock_fn) { emck->negedge_clock_fn(); }
            }
        }
    }
}

/*f c_engine::simulation_assist_comb_instance
  Only to be used in extremis - this is for other simulators, and generating waves for them
 */
void c_engine::simulation_assist_comb_instance( void *engine_handle)
{
    auto emi = (t_engine_module_instance *) engine_handle;
    emi->comb_cb.invoke_all();
}

/*f c_engine::simulation_assist_propagate_instance
  Only to be used in extremis - this is for other simulators, and generating waves for them
 */
void c_engine::simulation_assist_propagate_instance( void *engine_handle)
{
    auto emi = (t_engine_module_instance *) engine_handle;
    emi->propagate_cb.invoke_all();
}

/*f c_engine::simulation_assist_reset_instance
 */
void c_engine::simulation_assist_reset_instance( void *engine_handle, int pass )
{
    auto emi = (t_engine_module_instance *) engine_handle;
    emi->reset_cb.invoke_all(pass);
}

/*f c_engine::add_message
 */
t_sl_error_level c_engine::add_message( void *location,
                                        t_sl_error_level error_level,
                                        int error_number,
                                        int function_id,
                                        ... )
{
    va_list ap;
    va_start( ap, function_id );
    mutex_claim( engine_mutex_message );
    t_sl_error_level r = message->add_error( location, error_level, error_number, function_id, ap );
    mutex_release( engine_mutex_message );
    va_end(ap);
    return r;
}

/*f c_engine::add_error
 */
t_sl_error_level c_engine::add_error( void *location,
                                        t_sl_error_level error_level,
                                        int error_number,
                                        int function_id,
                                        ... )
{
    va_list ap;
    va_start( ap, function_id );
    mutex_claim( engine_mutex_message );
    t_sl_error_level r = error->add_error( location, error_level, error_number, function_id, ap );
    mutex_release( engine_mutex_message );
    va_end(ap);
    return r;
}

/*a Editor preferences and notes
mode: c ***
c-basic-offset: 4 ***
c-default-style: (quote ((c-mode . "k&r") (c++-mode . "k&r"))) ***
outline-regexp: "/\\\*a\\\|[\t ]*\/\\\*[b-z][\t ]" ***
*/

