/*a Copyright
  
  This file 'c_lexical_analyzer.cpp' copyright Gavin J Stark 2003, 2004
  
  This program is free software; you can redistribute it and/or modify it under
  the terms of the GNU General Public License as published by the Free Software
  Foundation, version 2.0.
  
  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even implied warranty of MERCHANTABILITY
  or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
  for more details.
*/

/*a To do
To do:

*/

/*a Includes
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <list>
#include "sl_debug.h"
#include "sl_general.h"
#include "c_library.h"

/*a Defines
 */

/*a Types
 */
/*a library class constructors and administration functions
 */
/*f c_library::c_library
 */
c_library::c_library(const char *library_name)
{
    this->library_name = library_name;
}

/*f c_library::~c_library
 */
c_library::~c_library()
{
    for (auto s: source_directories) {
        free((void *)s);
    }
}

/*f c_library_set::c_library_set
 */
c_library_set::c_library_set( c_cyclicity *cyclicity )
{
     this->cyclicity = cyclicity;
}

/*f c_library_set::~c_library_set
 */
c_library_set::~c_library_set()
{
}

/*f c_library_set::add_include_directory
 */
void c_library_set::add_include_directory(const char *directory)
{
    include_directories.push_back(sl_str_alloc_copy(directory));
}

/*f c_library_set::open_filename
 */
FILE *c_library_set::open_filename(const char *filename, char **pathname)
{
    SL_DEBUG( sl_debug_level_info, "Opening file %s", filename );

    FILE *f;
    char buffer[512];

    f = fopen( filename, "r" );
    if (f) {
        if (pathname) {
            *pathname = sl_str_alloc_copy(filename);
        }
        return f;
    }

    for (auto d:include_directories) {
        snprintf( buffer, 512, "%s/%s", d, filename );
        buffer[511] = 0;
        f = fopen( buffer, "r" );
        SL_DEBUG( sl_debug_level_info, "Tried %s : %p", buffer, f );
        if (f) {
            if (pathname) {
                *pathname = sl_str_alloc_copy(buffer);
            }
            return f;
        }
    }
    return NULL;
}

/*a Editor preferences and notes
mode: c ***
c-basic-offset: 4 ***
c-default-style: (quote ((c-mode . "k&r") (c++-mode . "k&r"))) ***
outline-regexp: "/\\\*a\\\|[\t ]*\/\\\*[b-z][\t ]" ***
*/


