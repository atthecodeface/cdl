/*a Copyright

  This file 'eh_py_engine.cpp' copyright Gavin J Stark 2003, 2004, 2012

  This is free software; you can redistribute it and/or modify it however you wish,
  with no obligations

  This software is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even implied warranty of MERCHANTABILITY
  or FITNESS FOR A PARTICULAR PURPOSE.
*/

/*a Includes
 */
#include <Python.h>
#include <stdlib.h>
#include <stdio.h>

#define EXTERN extern
#define c_sl_error void
#define c_engine void
#define t_sl_option_list void *
#include "eh_py_engine.h"

/*a Defines
 */

/*a Stuff for header file
 */
/*v Our frame */
PyTypeObject py_engine_PyTypeObject_frame = {
    PyVarObject_HEAD_INIT(NULL,0)
    .tp_name      = "Engine", // for printing
    .tp_basicsize = sizeof( t_py_engine_PyObject ), // basic size
    .tp_new       = py_engine_new,     /*tp_new*/
    .tp_dealloc   = py_engine_dealloc, /*tp_dealloc*/
    .tp_print     = py_engine_print,   /*tp_print*/
    .tp_repr      = py_engine_repr,          /*tp_repr*/
	.tp_str       = py_engine_str, /*tp_str */
    .tp_getattro  = PyObject_GenericGetAttr,
    .tp_methods   = engine_methods,
    .tp_flags     = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /*tp_flags*/
};

/*a Statics for py_engine module
 */
/*v py_engine_methods - Methods of the py_engine Module
 */
static PyMethodDef py_engine_methods[] =
{
    {"debug",  (PyCFunction)py_engine_debug, METH_VARARGS|METH_KEYWORDS, "Enable debugging and set level."},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};

/*a C code for py_engine
 */
#if PY_MAJOR_VERSION >= 3
    static struct PyModuleDef moduledef = {
        PyModuleDef_HEAD_INIT,
        .m_name="py_engine",     /* m_name */
        .m_doc="Python interface to CDL simulation engine",  /* m_doc */
        .m_size=-1,                    /* m_size - does not support subinterpreters (hence -1) */
        .m_methods=py_engine_methods,   /* m_methods */
    };
#endif

extern PyObject *eh_c_py_init_engine(PyObject *m);
extern PyObject *PyInit_py_engine( void )
{
    PyObject *m;
#if PY_MAJOR_VERSION >= 3
    m = PyModule_Create(&moduledef);
#else
    m = Py_InitModule3("py_engine", py_engine_methods, "Python interface to CDL simulation engine" );
#endif

    if (PyType_Ready(&py_engine_PyTypeObject_frame)<0) { return NULL; }

    Py_INCREF(&py_engine_PyTypeObject_frame);
    if (PyModule_AddObject(m, "engine", (PyObject *) &py_engine_PyTypeObject_frame) < 0) {
        Py_DECREF(&py_engine_PyTypeObject_frame);
        Py_DECREF(m);
        return NULL;
    }

    return eh_c_py_init_engine(m);
}
