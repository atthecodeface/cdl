/*a Copyright
  
  This file 'eh_scripting_python.cpp' copyright Gavin J Stark 2003, 2004
  
  This is free software; you can redistribute it and/or modify it however you wish,
  with no obligations
  
  This software is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even implied warranty of MERCHANTABILITY
  or FITNESS FOR A PARTICULAR PURPOSE.
*/

/*a Includes
 */
#include <stdio.h>
#include <stdlib.h>
#include <Python.h>
#include "eh_scripting.h"

/*a Statics
 */
/*v no_methods
 */
static PyMethodDef no_methods[] =
{
    {NULL, NULL, 0, NULL}
};

/*a Python code
 */
/*f scripting_init_module
 */
#if PY_MAJOR_VERSION >= 3
    static struct PyModuleDef moduledef = {
        PyModuleDef_HEAD_INIT,
        "",     /* m_name */
        "No documentation",  /* m_doc */
        -1,                  /* m_size */
        no_methods,    /* m_methods */
        NULL,                /* m_reload */
        NULL,                /* m_traverse */
        NULL,                /* m_clear */
        NULL,                /* m_free */
    };
#endif

extern void scripting_init_module( const char *script_module_name )
{
#if PY_MAJOR_VERSION >= 3
    moduledef.m_name = script_module_name;
    (void) PyModule_Create(&moduledef);
#else
     Py_InitModule( (char *)script_module_name, no_methods );
#endif
}

/*a Editor preferences and notes
mode: c ***
c-basic-offset: 4 ***
c-default-style: (quote ((c-mode . "k&r") (c++-mode . "k&r"))) ***
outline-regexp: "/\\\*a\\\|[\t ]*\/\\\*[b-z][\t ]" ***
*/



