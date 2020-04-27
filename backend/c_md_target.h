/*a Copyright
  
  This file 'c_md_target.h' copyright Gavin J Stark 2020
  
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
#ifdef __INC_C_MD_TARGET
#else
#define __INC_C_MD_TARGET

#include <list>
#include <string>
#include <functional>
#include "c_model_descriptor.h"
#include <stdarg.h>

/*c c_md_target */
class c_md_target {
protected:
    class c_model_descriptor *model;
    t_md_output_fn output_fn;
    void *output_handle;
    t_md_options *options;
private:
    char *string_buffer=NULL;
    int string_buffer_size=256;
public:
    c_md_target(class c_model_descriptor *model, t_md_output_fn output_fn, void *output_handle);
    ~c_md_target();
    char *string_printf(const char *format, va_list ap);
    std::string make_string(const char *format, ...);
    void output(int indent, const char *format, ...);
    
};
/*a Wrapper
 */
#endif

