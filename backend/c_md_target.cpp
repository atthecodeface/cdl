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

#include <list>
#include <string>
#include <functional>
#include <stdarg.h>
#include "c_md_target.h"
c_md_target::c_md_target(class c_model_descriptor *model, t_md_output_fn output_fn, void *output_handle, t_md_options *options)
{
    this->model = model;
    this->output_fn = output_fn;
    this->output_handle = output_handle;
    this->options = options;
}
c_md_target::~c_md_target()
{
}
#include <stdlib.h>
#include <stdio.h>
char *c_md_target::string_printf(const char *format, va_list ap)
{
    if (string_buffer==NULL) { string_buffer = (char *)malloc(string_buffer_size); }
    int n = vsnprintf(string_buffer, string_buffer_size, format, ap);
    if (n>=string_buffer_size-1) {
        string_buffer_size = n*2;
        free(string_buffer);
        string_buffer = NULL;
    }
    return string_buffer;
}
std::string c_md_target::make_string(const char *format, ...)
{
    va_list ap;
    char *s;
    do {
        va_start( ap, format );
        s = string_printf(format, ap);
        va_end(ap);
    } while (s==NULL);
    return std::string(s);
}
void c_md_target::output(int indent, const char *format, ...)
{
    va_list ap;
    char *s;
    do {
        va_start( ap, format );
        s = string_printf(format, ap);
        va_end(ap);
    } while (s==NULL);
    output_fn(output_handle, indent, "%s", s);
}
