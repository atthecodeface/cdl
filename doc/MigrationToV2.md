# CDL Version 2.0

CDL version 2.0 is the April/May 2020 development.

The major changes are:

* No backward-incompatible changes to CDL source code

* Support for libraries in CDL using "<lib>::" in includes

* Python support for 3.6+ *INSTEAD* of 2.7

* Simulation engine reworked - requires changes to C models

* Removed the 'model_list' description in favour of Python
  descriptions of CDL models, C models, C sources etc in libaries

# CDL language changes

CDL is a stepping stone towards HGL (pronounce Higgle) - a hardware
generation language. As such, CDL is not likely to change much.

However, to effectively support large designs, and learning from the
large-scale commercial designs already implemented in CDL, some
enhancements are beneficial.

The only change as yet is the support for 'libraries' and 'force
include'.

## Libraries

When CDL 1.4 looks for a header file because of an 'include
"<file.h>"' statement, it looks in the current directory and then
along a list of include paths.

CDL 2.0 does the same; however, it will look in the directory of the
include file *first*, as the 'current directory', rather than the OS
'current working directory'. This was always meant to be the defined
behaviour.

If the include is of the form '<library>::<filename>' - i.e. it
contains a '::', then CDL 2.0 will look for the file within the
specified library. The question then is, how does CDL know what a
library is and where it sits in the file system? For this it uses a
library description file

### Library description file

A library description file is a mapping from library name to
directories. It is created by the *cdl_desc.py* tool, which uses
*library_description.py* files in CDL design directories. The format
is internal to the CDL toolchain, but currently consists of lines that
are either '<libraryname>:' or '<path>'.

# Python 3

CDL predates Python3 by a number of years; hence it was written with
Python2 as a target.

CDLv2, though, is Python3 based.

Test code in Python requires transforming using 2to3

# Simulation model reworking

CDL 1.4 C++ models rely on callbacks using a "void *" handle.

CDL 2.0 C++ models use std::function callbacks.

This reduces the complexity of invoking modules, and reduces the C++
boilerplate code required in a model design.

The most obvious place where this comes up is in the registration of a
model, in its constructor.

Modern code is of the form:

```
    engine->register_delete_function(engine_handle, [this](){delete(this);} );
    engine->register_prepreclock_fn( engine_handle, [this](){this->prepreclock();} );
    engine->register_clock_fns( engine_handle, "clk", [this](){this->preclock();}, [this](){this->clock();} );
    engine->register_message_function( engine_handle, [this](t_se_message *m){this->message(m);});
    engine->register_comb_fn(engine_handle, [this](void){this->comb();});
    engine->register_reset_function(engine_handle, [this](int pass){this->reset(pass);} );
```

The most critical item is that registering of a clock (and its
functions) *MUST* be performed in a single call. (In CDL 1.4 the
preclock and clock functions could be registered separately.)

Furthermore, the module has a prepreclock function; individual clocks
do not (this was always the case, but CDL 1.4 had some spurious API
calls which would have seemed to suggest that they did).
# library_description instead of model_list

CDL 1.4 used a 'model_list' file that described the modules and source
code that needed to be built for a simulation. It was driven around a
monolithic design concept, not a library setup. The original script to
convert this in to a Makefile was a PHP program, which for CDL 1.4 had
been converted to a very primitive Python program.

CDL 2.0 has deprecated 'model_list' files.

CDL 2.0 uses *library_description.py* files to describe libraries,
which contain collections of models - be they CDL, C++, C, or
whatever.

## Library_description.py files

The basic concept behind a library_description.py file is
that it contains a single subclass of the cdl_desc.Library, which
defines the library that is described in the file.

It then contains a number of subclasses of cdl_desc.Modules. Each
subclass is expected to have a list of *modules*; these modules will
be the contents of the library. The use of more than one
cdl_desc.Modules subclass is to provide explicit grouping on behalf of
the user, not for the CDL library system itself.

A library may contain subclasses of cdl_desc.Executables - these are
tools that are also described by the library. CDL 1.4 did not support
these.

The library_description.py file is located in what cdl_desc would term
the 'library root directory'

### cdl_desc.Library

The subclass of cdl_desc.Library has only one relevant property: its
*name*. This provides cdl_desc with the CDL library name described by
the library_description.py file

### cdl_desc.Modules

A subclass of cdl_desc.Modules has a few important properties:

* export_dirs - a list of strings that are (relative to the library
  root directory) the directories that provide CDL include files
  (e.g. for include "<library>::<file>") for this library.

* libraries - a dictionary of "library name" to library options,
  providing the dependencies of this library on other
  libraries. Currently the options must be *True*. The theory is that
  the options will eventually provide some optional compilation
  capability.

* modules - a list of cdl_desc.Module subclass instances, which are
  the modules provided by the library. Note, though, that
  cdl_desc.Module is *NEVER* instanced itself; these instead will be
  cdl_desc.CdlModule, cdl_desc.CModel, or cdl_desc.CSrc.

### cdl_desc.Executables

A subclass of cdl_desc.Executables has a name property that provides
the eventual name of the executable. It then consists of a number of
srcs; note, though, that it is linked against the C++ output for the
whole of the library, so other sources in other cdl_desc.Modules can be
linked in too. The sources described in the executable *are not*
linked in to the C++ library provided by the module.

The relevant properties are then:

* name - name of the executable

* srcs - list of cdl_desc.CSrc instances that, along with any othe
CSrcs in the library, form the executable


