/*a Copyright
  
  This file 'se_external_module.cpp' copyright Gavin J Stark 2003, 2004
  
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
#include <list>
#include "sl_debug.h"
#include "se_external_module.h"

/*a Defines
 */

/*a Types
 */
/*t t_engine_module
 */
typedef struct t_engine_module
{
    struct t_engine_module *next_module;
    struct t_engine_module *next_module_of_same_name;
    char *name;
    void *handle;
    const char *implementation_name;
    t_se_instantiation_fn instantiation_fn;
} t_engine_module;

/*a Statics
 */
/*v registered_module_list
 */
static std::list<t_engine_module *> *registered_module_list;

/*a External functions
 */
/*f se_external_module_find
 */
extern void *se_external_module_find( const char *name )
{
    return se_external_module_find( name, NULL );
}

/*f se_external_module_find
 */
extern void *se_external_module_find( const char *name, const char *implementation_name )
{
    SL_DEBUG(sl_debug_level_verbose_info, "se_external_module_find", "Looking for module type '%s'", name ) ;
    for (auto &em:*registered_module_list) {
        if (!strcmp(em->name, name)) {
            while (1) {
                if ((em->implementation_name==NULL) && (implementation_name==NULL)) {
                    //fprintf(stderr,"Found NULL implementation for module type '%s'\n", name );
                    return (void *)em;
                }
                if (em->implementation_name && implementation_name && !strcmp(implementation_name, em->implementation_name)) {
                    //fprintf(stderr,"Found implementation '%s' for module type '%s'\n", implementation_name, name );
                    return (void *)em;
                }
                if (em->next_module_of_same_name==NULL) {
                    if (implementation_name!=NULL) {
                        fprintf(stderr,"WARNING: Failed to find implementation '%s' for module type '%s' - using last added\n", implementation_name, name );
                    } else {
                        //fprintf(stderr,"Using last implementation for module type '%s', no particular implementation requested\n", name );
                    }
                    return (void *)em;
                }
                em = em->next_module_of_same_name;
            }
        }
    }
    SL_DEBUG(sl_debug_level_verbose_info, "se_external_module_find", "Failed to find module type '%s'", name ) ;
    return NULL;
}

/*f se_external_module_name(handle)
 */
extern const char *se_external_module_name( void *handle )
{
    auto em = (t_engine_module *)handle;
    return em->name;
}

/*f se_external_module_name(int)
 */
extern const char *se_external_module_name( int n )
{
    for (auto &em:*registered_module_list){
        if (n==0) return em->name;
        n--;
    };
    return NULL;
}

/*f se_external_module_register
  register a module, checking the version number of the registration call first.
  return a handle for use with future instantiation calls, or NULL for failure.
 */
extern void se_external_module_register( int registration_version, const char *name, t_se_instantiation_fn instantiation_fn )
{
    se_external_module_register( registration_version, name, instantiation_fn, NULL );
}

/*f se_external_module_register
  register a module, checking the version number of the registration call first.
  return a handle for use with future instantiation calls, or NULL for failure.
 */
extern void se_external_module_register( int registration_version, const char *name, t_se_instantiation_fn instantiation_fn, const char *implementation_name )
{
    SL_DEBUG(sl_debug_level_info, "se_external_module_register", "Registering module type '%s'", name ) ;
    if (registration_version!=1) {fprintf(stderr,"Registration_Version must be 1 for se_external_module_register\n");}

    auto prev_em = (t_engine_module *)se_external_module_find(name, NULL);
    if (prev_em) {
        while (prev_em->next_module_of_same_name) {
            prev_em = prev_em->next_module_of_same_name;
        }
    }

    auto em = (t_engine_module *)malloc(sizeof(t_engine_module));
    em->name = sl_str_alloc_copy( name );
    if (implementation_name!=NULL) implementation_name=sl_str_alloc_copy(implementation_name);
    em->implementation_name = implementation_name;
    em->instantiation_fn = instantiation_fn;
    em->next_module_of_same_name = NULL;

    if (prev_em) {
        prev_em->next_module_of_same_name = em;
    } else {
        registered_module_list->push_back(em);
    }
    return;
}

/*f se_external_module_instantiate
 */
extern t_sl_error_level se_external_module_instantiate( void *handle, c_engine *engine, void *instantiation_handle )
{
    auto em = (t_engine_module *)handle;
    return em->instantiation_fn( engine, instantiation_handle );
}

/*f deregister_all_implementations
  deregister all implementations of a module
 */
static void deregister_all_implementations(t_engine_module *em)
{
    SL_DEBUG(sl_debug_level_info, "engine_deregister_module", "Deregistering module type '%s'", em->name );
    while (em!=NULL) {
        auto next_em = em->next_module_of_same_name;
        if (em->implementation_name) free((void *)em->implementation_name);
        free(em->name);
        free(em);
        em = next_em;
    }
}

/*f se_external_module_deregister_all
 */
extern void se_external_module_deregister_all( void )
{
    for (auto &em:*registered_module_list) {
        deregister_all_implementations(em);
    }
    registered_module_list->clear();
}

/*f se_external_module_init
 */
extern void se_external_module_init( void )
{
    registered_module_list = new std::list<t_engine_module *>();
}


/*a Editor preferences and notes
mode: c ***
c-basic-offset: 4 ***
c-default-style: (quote ((c-mode . "k&r") (c++-mode . "k&r"))) ***
outline-regexp: "/\\\*a\\\|[\t ]*\/\\\*[b-z][\t ]" ***
*/

