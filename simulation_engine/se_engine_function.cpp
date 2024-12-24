/*a Copyright
  
  This file 'se_engine_function.cpp' copyright Gavin J Stark 2003, 2004
  
  This is free software; you can redistribute it and/or modify it under
  the terms of the GNU Lesser General Public License as published by the Free Software
  Foundation, version 2.1.
  
  This software is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even implied warranty of MERCHANTABILITY
  or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License
  for more details.
*/

/*a Outline
  Models register with this base engine when in cycle simulation mode
  They register by first declaring themselves, and getting a handle in return
  They are then instantiated by this base engine, at which point:
    they may attach themselves to a clock, and specify a reset, preclock, clock and combinatorial functions
    they may register input and output signals
    they may specify which signals depend/are generated on what clocks or combinatorially
    they may declare state that may be interrogated

  The base engine can then have global buses/signals instantiated, and this wires things up
  Inputs to modules are implemented by setting an 'int **' in the module to point to an 'int *' which is an output of another module.
  Inputs, outputs and global signals all have a bit length (size) which must be specified.

 */

/*a Includes
 */
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <stdarg.h>
#include "sl_debug.h"
#include "sl_timer.h"
#include "se_engine_function.h"

/*a Defines
 */
#if 0
#define WHERE_I_AM(x) {fprintf(stderr,"%s:%s:%d:%p\n",__FILE__,__func__,__LINE__,x );}
#else
#define WHERE_I_AM(x) {}
#endif

/*a Types */
/*t t_engine_function_list
 */
typedef struct t_engine_function_list
{
    struct t_engine_function_list *next_in_list;
    struct t_engine_function *signal;
    union {
        t_se_engine_std_function       callback_void_fn;
        t_se_engine_int_std_function   callback_int_fn;
        t_se_engine_voidp_std_function callback_voidp_fn;
    };
    t_sl_timer timer; // For profiling - time spent in the callback
    int invocation_count; // For profiling - number of times callback has been invoked
} t_engine_function_list;

/*a Signal reference function add
 */
/*f se_engine_signal_reference_add
 */
extern void se_engine_signal_reference_add( t_engine_signal_reference **ref_list_ptr, t_engine_signal *signal )
{
     t_engine_signal_reference *efr;

     efr = (t_engine_signal_reference *)malloc(sizeof(t_engine_signal_reference));
     efr->next_in_list = *ref_list_ptr;
     *ref_list_ptr = efr;
     efr->signal = signal;
}

/*a Engine function external functions
 */
/*f se_engine_function_free_functions
 */
extern void se_engine_function_free_functions( t_engine_function *list )
{
     t_engine_function *efn, *next_efn;

     for (efn = list; efn; efn=next_efn )
     {
          next_efn = efn->next_in_list;
          if (efn->name)
          {
               free(efn->name);
          }
          delete (efn);
     }
}

/*f se_engine_function_add_function
 */
extern t_engine_function *se_engine_function_add_function( t_engine_module_instance *emi, t_engine_function **efn_list, const char *name )
{
     t_engine_function *efn;

     efn = new t_engine_function();
     efn->next_in_list = *efn_list;
     *efn_list = efn;
     efn->module_instance = emi;
     efn->name = name?sl_str_alloc_copy(name) : NULL;
     return efn;
}

/*f se_engine_function_find_function
 */
extern t_engine_function *se_engine_function_find_function( t_engine_function *efn_list, const char *name )
{
     t_engine_function *efn;

     for (efn=efn_list; efn; efn=efn->next_in_list)
     {
          if ((efn->name) && (!strcmp(efn->name,name)))
          {
               return efn;
          }
     }
     return NULL;
}

/*a Engine function reference external functions
 */
/*f se_engine_function_references_free
 */
extern void se_engine_function_references_free( t_engine_function_reference *list )
{
     t_engine_function_reference *efr, *next_efr;

     for (efr = list; efr; efr=next_efr )
     {
          next_efr = efr->next_in_list;
          free( efr );
     }
}

/*f se_engine_function_references_add
 */
extern void se_engine_function_references_add( t_engine_function_reference **ref_list_ptr, t_engine_function *efn )
{
     t_engine_function_reference *efr;

     efr = (t_engine_function_reference *)malloc(sizeof(t_engine_function_reference));
     efr->next_in_list = *ref_list_ptr;
     *ref_list_ptr = efr;
     efr->signal = efn;
}

/*a Engine function reference external functions
 */
/*f se_engine_function_call_add
 */
extern t_engine_function_list *se_engine_function_call_add( t_engine_function_list **list_ptr )
{
     t_engine_function_list *efl, **efl_prev;

     for (efl_prev = list_ptr; (*efl_prev); efl_prev = &((*efl_prev)->next_in_list) );

     efl = (t_engine_function_list *)calloc(1, sizeof(t_engine_function_list));
     // efl = new(t_engine_function_list);
     efl->next_in_list = NULL;
     efl->signal = NULL;
     efl->invocation_count = 0;
     SL_TIMER_INIT(efl->timer);
     *efl_prev = efl;
     return efl;
}

/*f se_engine_function_call_add
 */
extern void se_engine_function_call_add( t_engine_function_list **list_ptr, t_engine_function_reference *efr, t_engine_callback_fn callback_fn )
{
    DEPRECATED("se_engine_function_call_add","fn efr handle - MUST BE REMOVED - signal no longer has a handle");
    // auto efl = se_engine_function_call_add( list_ptr, efr->signal->handle, callback_fn );
    // efl->signal = efr->signal;
}

/*f se_engine_function_call_add
 */
extern t_engine_function_list *se_engine_function_call_add( t_engine_function_list **list_ptr, void *handle, t_engine_callback_fn callback_fn )
{
    DEPRECATED("se_engine_function_call_add","fn void handle");
    auto *efl = se_engine_function_call_add(list_ptr);
    efl->callback_void_fn = [handle, callback_fn](void)->t_sl_error_level{return (*callback_fn)(handle);};
    return efl;
}

/*f se_engine_function_call_add - int
 */
extern t_engine_function_list *se_engine_function_call_add( t_engine_function_list **list_ptr, void *handle, t_engine_callback_arg_fn callback_fn )
{
    DEPRECATED("se_engine_function_call_add","fn int handle");
    auto *efl = se_engine_function_call_add(list_ptr);
    efl->callback_int_fn = [handle, callback_fn](int x)->t_sl_error_level{return (*callback_fn)(handle, x);};
    return efl;
}

/*f se_engine_function_call_add - voidp
 */
extern t_engine_function_list *se_engine_function_call_add( t_engine_function_list **list_ptr, void *handle, t_engine_callback_argp_fn callback_fn )
{
    DEPRECATED("se_engine_function_call_add","fn voidp handle");
    auto *efl = se_engine_function_call_add(list_ptr);
    efl->callback_voidp_fn = [handle, callback_fn](void *p)->t_sl_error_level{return (*callback_fn)(handle, p);};
    return efl;
}

/*f se_engine_function_call_invoke_all
 */
extern void se_engine_function_call_invoke_all( t_engine_function_list *list )
{
    t_engine_function_list *efl;
    for (efl=list; efl; efl=efl->next_in_list)
    {
        SL_TIMER_ENTRY(efl->timer);
        efl->invocation_count++;
        WHERE_I_AM(efl->handle);
        efl->callback_void_fn();
        SL_TIMER_EXIT(efl->timer);
    }
}

/*f se_engine_function_call_invoke_all_arg
 */
extern void se_engine_function_call_invoke_all_arg( t_engine_function_list *list, int arg )
{
    t_engine_function_list *efl;
    for (efl=list; efl; efl=efl->next_in_list)
    {
        SL_TIMER_ENTRY(efl->timer);
        efl->invocation_count++;
        WHERE_I_AM(efl->handle);
        efl->callback_int_fn(arg);
        SL_TIMER_EXIT(efl->timer);
    }
}

/*f se_engine_function_call_invoke_all_argp
 */
extern void se_engine_function_call_invoke_all_argp( t_engine_function_list *list, void *arg )
{
    t_engine_function_list *efl;
    for (efl=list; efl; efl=efl->next_in_list)
    {
        SL_TIMER_ENTRY(efl->timer);
        efl->invocation_count++;
        WHERE_I_AM(efl->handle);
        efl->callback_voidp_fn(arg);
        SL_TIMER_EXIT(efl->timer);
    }
}

/*f se_engine_function_call_display_stats_all
 */
extern void se_engine_function_call_display_stats_all( FILE *f, t_engine_function_list *list )
{
    t_engine_function_list *efl;
    for (efl=list; efl; efl=efl->next_in_list)
    {
        fprintf( f, "EFL module %s clock %s invoked %d times for a total time of %lf usecs\n", efl->signal->module_instance->full_name, efl->signal->name, efl->invocation_count, SL_TIMER_VALUE_US(efl->timer));
    }
}

/*f se_engine_function_call_free
 */
extern void se_engine_function_call_free( t_engine_function_list *list_ptr )
{
     t_engine_function_list *efl, *next_efl;

     for (efl = list_ptr; efl; efl=next_efl )
     {
          next_efl = efl->next_in_list;
          free( efl );
     }
}

/*a Editor preferences and notes
mode: c ***
c-basic-offset: 4 ***
c-default-style: (quote ((c-mode . "k&r") (c++-mode . "k&r"))) ***
outline-regexp: "/\\\*a\\\|[\t ]*\/\\\*[b-z][\t ]" ***
*/

