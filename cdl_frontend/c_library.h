/*a Copyright
  
  This file 'c_library.h' copyright Gavin J Stark 2020
  
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
#ifdef __INC_C_LIBRARY
#else
#define __INC_C_LIBRARY

/*a Includes
 */
#include <list>
#include <array>
#include <string>

/*a Types
 */
/*t	c_library
 */
class c_library
{
public:
    c_library(const char *library_name);
    ~c_library();

    void add_source_directory( const char *directory );
    FILE *open_filename( const char *filename, char **pathname );

private:
    const char *library_name;
    std::list<const char *> source_directories;
};

/*t	c_library_set
 */
class c_library_set
{
public:
    c_library_set(class c_cyclicity *cyclicity);
    ~c_library_set();

    void read_library_descriptor( const char *filename );
    void add_include_directory(const char *directory);
    FILE *open_filename( const char *filename, char **pathname );

private:
    class c_cyclicity *cyclicity;
    std::list<c_library *>  libraries;
    std::list<const char *> include_directories;
};

/*a Wrapper
 */
#endif
