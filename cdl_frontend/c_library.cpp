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

/*a Includes
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <list>
#include <string>
#include <fstream>
#include "sl_debug.h"
#include "sl_general.h"
#include "c_cyclicity.h"
#include "c_library.h"

/*a Defines
 */

/*a Types
 */
/*a Useful functions
 */
/*f open_file_from_path */
static FILE *open_file_from_path(const char *path1, const char *path2, const char *filename, char **buffer, int *buffer_size)
{
    if (!(*buffer)) {
        *buffer_size = 8;
        *buffer = (char *)malloc(*buffer_size);
    }
    while (1) {
        int n;
        if (filename[0]=='/') {
            n = snprintf(*buffer, *buffer_size, "%s", filename );
        } else if ((path2) && (path2[0]=='/')) {
            n = snprintf(*buffer, *buffer_size, "%s/%s", path2, filename );
        } else if (path2) {
            n = snprintf(*buffer, *buffer_size, "%s/%s/%s", path1, path2, filename );
        } else {
            n = snprintf(*buffer, *buffer_size, "%s/%s", path1, filename );
        }
        if (n<*buffer_size-1) break;
        n *= 2;
        void *p = realloc((void *)(*buffer), n);
        if (!p) break;
        *buffer_size = n;
        *buffer = (char *)p;
    }
    if (!*buffer) return NULL;
    return fopen(*buffer, "r" );
}

/*f find_file_in_directories */
static FILE *find_file_in_directories(const char *root_pathname, std::list<const char *> directories, const std::string &filename, char **pathname)
{
    FILE *f;
    const char *c_filename = filename.c_str();
    char *buffer;
    int buffer_size;
    buffer = NULL;
    f = NULL;
    for (auto d:directories) {
        f = open_file_from_path(root_pathname, d, c_filename, &buffer, &buffer_size);
        SL_DEBUG( sl_debug_level_info, "Tried %s : %p", buffer, f );
        if (f) break;
    }

    if ((f) && (pathname)) {
        *pathname = buffer;
    } else {
        if (buffer) free(buffer);
    }
    return f;
}

/*a library class constructors and administration functions
 */
/*f c_library::c_library
 */
c_library::c_library(const char *library_name)
{
    this->library_name = sl_str_alloc_copy(library_name);
}

/*f c_library::~c_library
 */
c_library::~c_library()
{
    for (auto s: source_directories) {
        free((void *)s);
    }
    source_directories.clear();
    free((void *)library_name);
}

/*f c_library::add_source_directory
 */
void c_library::add_source_directory(const char *directory)
{
    source_directories.push_back(sl_str_alloc_copy(directory));
}

/*f c_library::open_filename
 */
FILE *c_library::open_filename(const char *root_pathname, const std::string &filename, char **pathname)
{
    return find_file_in_directories(root_pathname, source_directories, filename, pathname);
}

/*a library set class constructors and administration functions
 */
/*f c_library_set::c_library_set
 */
c_library_set::c_library_set( c_cyclicity *cyclicity )
{
     this->cyclicity = cyclicity;
     this->root_dirname = sl_str_alloc_copy(".");
}

/*f c_library_set::~c_library_set
 */
c_library_set::~c_library_set()
{
    for (auto s: include_directories) {
        free((void *)s);
    }
    for (auto l: libraries) {
        delete(l);
    }
    include_directories.clear();
}

/*f c_library_set::set_library_root
 */
void c_library_set::set_library_root(const char *dirname)
{
    if (root_dirname) free((void *)root_dirname);
    root_dirname = sl_str_alloc_copy(dirname);
}

/*f c_library_set::add_new_library
 */
c_library *c_library_set::add_new_library(const char *name)
{
    auto c=new c_library(name);
    libraries.push_back(c);
    return c;
}

/*f c_library_set::read_library_descriptor
 */
void c_library_set::read_library_descriptor(const char *filename)
{
    char *pathname;
    int buffer_size;
    c_library *current_library;
    pathname = NULL;
    auto f=open_file_from_path(root_dirname, NULL, filename, &pathname, &buffer_size);
    if (!f) {
        cyclicity->error->add_error( NULL, error_level_fatal, error_number_general_bad_filename, 0,
                                     error_arg_type_const_string, filename,
                                     error_arg_type_malloc_filename, "library description",
                                     error_arg_type_none );
        return;
    }
    fclose(f);

    std::ifstream library_desc(pathname, std::ifstream::in);
    std::string l;
    current_library = NULL;
    int n=1;
    while (std::getline(library_desc, l)) {
        char *cl = sl_str_alloc_copy(l.c_str());
        for (auto p=strtok(cl," "); p; p= strtok (NULL, " ")) {
            int l=strlen(p);
            if (l>0) {
                if (p[l-1]==':') {
                    p[l-1]=0;
                    current_library = add_new_library(p);
                } else if (current_library) {
                    current_library->add_source_directory(p);
                } else {
                    fprintf(stderr,"Bad token in library_desc %s at line %d char %d\n",p,n,(int)(p-cl));
                }
            }
        }
        free(cl);
        n++;
    }
}

/*f c_library_set::add_include_directory
 */
void c_library_set::add_include_directory(const char *directory)
{
    include_directories.push_back(sl_str_alloc_copy(directory));
}

/*f c_library_set::find_library
 */
c_library *c_library_set::find_library(const std::string &name, int start, int end)
{
    auto cname=name.substr(start,end).c_str();
    for (auto l: libraries) {
        if (!strcmp(cname,l->library_name)) return l;
    }
    return NULL;
}

/*f c_library_set::open_filename
 */
FILE *c_library_set::open_filename(const std::string &filename, char **pathname, void **library)
{
    SL_DEBUG( sl_debug_level_info, "Opening file %s", filename.c_str() );

    FILE *f;

    auto library_marker=filename.find("::", 0);
    if (library_marker!=std::string::npos) {
        auto filename_in_library = filename.substr(library_marker+2,std::string::npos);
        auto l = find_library(filename, 0, library_marker);
        SL_DEBUG(sl_debug_level_info, "Library : %p", l );
        if (library) {*library=l;}
        if (l) {
            return l->open_filename(root_dirname, filename_in_library, pathname);
        } else { // If library is not in the directory, lib::blah should be in lib/blah
            auto library_name = filename.substr(0, library_marker);
            char *buffer;
            int buffer_size;
            buffer = NULL;
            f = open_file_from_path(root_dirname, library_name.c_str(), filename_in_library.c_str(), &buffer, &buffer_size);
            if ((f) && (pathname)) {
                *pathname = buffer;
            } else {
                if (buffer) free(buffer);
            }
            return f;
        }
    }

    if (library && (*library)) {
        SL_DEBUG(sl_debug_level_info, "Using library %p for include without library", *library);
        c_library *l = *((c_library **)library);
        return l->open_filename(root_dirname, filename, pathname);
    } else {
        SL_DEBUG(sl_debug_level_info, "Using cwd for include without library");
        f = fopen(filename.c_str(), "r" );
        if (f) {
            if (pathname) {
                *pathname = sl_str_alloc_copy(filename.c_str());
            }
            return f;
        }
    }
    SL_DEBUG(sl_debug_level_info, "Searching include directories for include without library");
    return find_file_in_directories(NULL, include_directories, filename, pathname);
}
/*a Editor preferences and notes
mode: c ***
c-basic-offset: 4 ***
c-default-style: (quote ((c-mode . "k&r") (c++-mode . "k&r"))) ***
outline-regexp: "/\\\*a\\\|[\t ]*\/\\\*[b-z][\t ]" ***
*/


