extern PyTypeObject py_engine_PyTypeObject_frame;
/*t t_py_engine_PyObject
 */
typedef struct {
     PyObject_HEAD
     c_sl_error *error;
     c_engine *engine;
     t_sl_option_list env_options;
} t_py_engine_PyObject;

/*v py_engine_PyTypeObject_frame
 */
EXTERN void py_engine_dealloc( PyObject *self );
EXTERN int py_engine_print( PyObject *self, FILE *f, int unknown );
EXTERN PyObject *py_engine_repr( PyObject *self );
EXTERN PyObject *py_engine_str( PyObject *self );
EXTERN PyObject *py_engine_new( PyObject* self, PyObject* args );
EXTERN PyObject *py_engine_debug( PyObject* self, PyObject* args, PyObject *kwds );
EXTERN PyMethodDef engine_methods[];

