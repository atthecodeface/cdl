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
    FILE *open_filename(const char *root_pathname, const std::string &filename, char **pathname);
    const char *library_name;

private:
    std::list<const char *> source_directories;
};

/*t	c_library_set
 */
class c_library_set
{
public:
    c_library_set(class c_cyclicity *cyclicity);
    ~c_library_set();

    void set_library_root( const char *dirname );
    void read_library_descriptor( const char *filename );
    void add_include_directory(const char *directory);
    c_library *add_new_library(const char *name);
    c_library *find_library(const std::string &name, int start, int len);
    /* open a file from a string filename, using library search path
     *library is the library to start looking if the file has no library specifier
     Put found pathname in *pathname (if pathname!=NULL), and library file is found in in
     *library (if not library!=NULL)
     */
    FILE *open_filename(const std::string &filename, char **pathname, void **library );

private:
    class c_cyclicity *cyclicity;
    const char *root_dirname;
    std::list<c_library *>  libraries;
    std::list<const char *> include_directories;
};

/*a Wrapper
 */
#endif
