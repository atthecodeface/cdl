#!/usr/bin/env python3
import sys
import os
import importlib
from pathlib import Path

#a Documentation
"""
A CDL 2.0 build is built from a collection of CDL libraries.
Each CDL library has a library_desc.py file that describes it.

A CDL library has the form:

> import cdl_desc
> from cdl_desc import CdlModule, CModel
> class Library(cdl_desc.Library):
>    name = "<library name>"
>    modules=cdl_desc.Modules.__subclasses__
>    pass
> class SomeModules(cdl_desc.Modules):
>    name = "<module set name>"
>    libraries = {"<required library>":True, "<optional library>":False, ...}
>    export_dirs = ["<header files directory relative to library_desc.py directory>", ...]
>    ...
>    pass
> ...

The Modules subclasses contain descriptions of sets of modules in the library

Using this information a build system can put together a Makefile for a library to create
verilog files, lists of verilog files, CDL C models, and compilation scripts to create C
libraries for C simulation.

The build system can also put together an outer Makefile that invokes sets of library Makefiles
given any required information such as the toplevel for a verilog build, or the test harness
C file for a verilator build. (CDL simulation builds do not require a 'toplevel', as they have a
run-time toplevel instantiation.)

"""

#a Classes used in library_desc.py files
#c Module - base class for module classes
class Module(object):
    """
    parent is a Modules subclass
    """
    model_name = None
    src_dir = None
    include_dir = None
    parent = None
    cpp_include_dirs = None
    inherit = ["src_dir", "include_dir"]
    def __init__(self, model_name, src_dir=None):
        self.model_name = model_name
        if src_dir is not None: self.src_dir=src_dir
        pass
    def validate(self):
        for k in self.inherit:
            if hasattr(self, k) and hasattr(self.parent,k):
                if getattr(self, k) is None:
                    setattr(self, k, getattr(self.parent,k))
                    pass
                pass
            pass
        pass
    def value_or_default(self, v, d):
        if v is not None: return v
        return d
    def set_parent(self, parent):
        self.parent = parent
        pass
    def set_attr_options(self, obj, options):
        for (k,v) in options.items():
            if not hasattr(obj, k):
                raise Exception("Option '%s' not known as an attribute"%k)
            setattr(obj,k,v)
            pass
        pass
    pass

#c CdlModule
"""
    --remap-implementation-name X=Y: changes implementation_name of module X to be Y - this permits many C models of the same module. Not used
    --remap-registered-name X=Y: changes just the name used for the C registration, not the output name as well (which rmn does). Not used
        if o=="vapi":
            options.append("--v_additional_port_include")
            options.append(v)
        if o=="vabi":
            options.append("--v_additional_body_include")
            options.append(v)
    options.append("--coverage-desc-file")
    options.append("${TARGET_DIR}/"+model_name+".map")

"""

class CdlModule(Module):
    class CdlOptions:
        assertions = False
        system_verilog_assertions = False
        displays = False
        coverage = False
        statements = False
        multithread = False
        def cdl_flags(self):
            """
            Return list of flags required from the properties
            """
            r = []
            if self.assertions:  r.append("--include-assertions")
            if self.system_verilog_assertions:  r.append("--sv-assertions")
            if self.displays:  r.append("--v_displays")
            if self.coverage:    r.append("--include-coverage")
            if self.statements:  r.append("--include-stmt-coverage")
            if self.multithread: r.append("--multithread")
            return r
        pass
    extra_cdlflags = None
    cdl_include_dirs = []
    constants = {}
    cdl_module_name = None
    inherit = Module.inherit[:] + ["cdl_include_dirs"]
    def __init__(self, model_name,
                 cdl_filename = None,
                 cpp_filename = None,
                 obj_filename = None,
                 verilog_filename = None,
                 cdl_include_dirs = None,
                 force_includes = [],
                 extra_cdlflags = None,
                 options = {},
                 constants = {}, # dictionary of constant name => value for compilation
                 types = {}, # dictionary of source type => desired type for compilation
                 instance_types = {}, # dictionary of source module type => desired type for compilation
                 cdl_module_name=None, # Name of module in CDL file to be mapped to model_name if None
                 **kwargs):
        Module.__init__(self, model_name, **kwargs)
        self.cdl_filename     = self.value_or_default(cdl_filename, model_name)
        self.cpp_filename     = self.value_or_default(cpp_filename, model_name)
        self.obj_filename     = self.value_or_default(obj_filename, model_name)
        self.verilog_filename = self.value_or_default(verilog_filename, model_name)
        self.cdl_include_dirs = self.value_or_default(cdl_include_dirs, self.cdl_include_dirs)
        self.extra_cdlflags   = self.value_or_default(extra_cdlflags, self.extra_cdlflags)
        self.force_includes   = force_includes
        self.cdl_module_name  = cdl_module_name
        self.constants        = constants
        self.types            = types
        self.instance_types   = instance_types
        self.cdl_options = self.CdlOptions()
        self.set_attr_options(self.cdl_options, options)
        pass
    def cdl_flags_string(self):
        """
        Return string of flags required from the properties
        """
        r = self.cdl_options.cdl_flags()
        if self.cdl_module_name is not None:
            r += ["--remap-module-name %s=%s"%(self.cdl_module_name, self.model_name)]
            pass
        for (n,v) in self.constants.items():
            r += ["--constant %s=%s"%(n,str(v))]
            pass
        for (n,v) in self.types.items():
            r += ["--type-remap %s=%s"%(n,str(v))]
            pass
        for (n,v) in self.instance_types.items():
            r += ["--remap-instance-type %s.%s=%s"%(self.model_name,n,str(v))]
            pass
        return " ".join(r)
    def write_makefile(self, write, library_name):
        """
        Write a makefile line for a cdl_template invocation
        """
        r = "$(eval $(call cdl_template,"
        cdl_include_dir_option = ""
        if self.include_dir is not None:
            cdl_include_dir_option += "--include-dir "+self.parent.get_path_str(self.include_dir)+" "
            pass
        if self.cdl_include_dirs is None: self.cdl_include_dirs=[]
        for i in self.cdl_include_dirs:
            cdl_include_dir_option += "--include-dir "+self.parent.get_path_str(i)+" "
            pass
        if self.force_includes is None: self.force_includes=[]
        for i in self.force_includes:
            cdl_include_dir_option += "--force-include "+i+" "
            pass
        cdl_template = [library_name,
                        self.parent.get_path_str(self.src_dir),
                        "${BUILD_DIR}",
                        self.cdl_filename+".cdl",
                        self.model_name,
                        self.cpp_filename+".cpp",
                        self.obj_filename+".o",
                        self.verilog_filename+".v",
                        "${CDL_EXTRA_FLAGS} "+self.cdl_flags_string()+" "+cdl_include_dir_option,
                        ]
        r += ",".join(cdl_template)
        r += "))"
        write(r)
        pass

#c CModel
class CModel(Module):
    cpp_defines = {}
    inherit = Module.inherit[:] + ["cpp_include_dirs"]
    def __init__(self, model_name,
                 cpp_filename = None,
                 obj_filename = None,
                 cpp_include_dirs = None,
                 cpp_defines = {},
                 **kwargs):
        Module.__init__(self, model_name, **kwargs)
        self.cpp_filename     = self.value_or_default(cpp_filename, model_name)
        self.obj_filename     = self.value_or_default(obj_filename, self.cpp_filename)
        self.cpp_include_dirs = self.value_or_default(cpp_include_dirs, self.cpp_include_dirs)
        self.cpp_defines      = self.value_or_default(cpp_defines,      self.cpp_defines)
        pass
    def write_makefile(self, write, library_name, executable=None):
        """
        Write a makefile line for a cpp_template invocation
        """
        r = "$(eval $(call cpp_template,"
        cpp_include_dir_option = ""
        if self.include_dir is not None:
            cpp_include_dir_option += "-I "+self.parent.get_path_str(self.include_dir)+" "
            pass
        if self.cpp_include_dirs is None: self.cpp_include_dirs=[]
        for i in self.cpp_include_dirs:
            cpp_include_dir_option += "-I "+self.parent.get_path_str(i)+" "
            pass
        cpp_defines_option = ""
        for (d,v) in self.cpp_defines.items():
            cpp_defines_option += "-D%s=%s"%(d,v)
            pass
        model_name_to_use = self.model_name
        if model_name_to_use is None: model_name_to_use="" # For C Source instead of CModel, really
        make_variable_to_use = executable
        if executable is None: make_variable_to_use="" # Add it to the library
        cpp_template = [library_name,
                        self.parent.get_path_str(self.src_dir),
                        "${BUILD_DIR}",
                        self.cpp_filename+".cpp",
                        model_name_to_use,
                        self.obj_filename+".o",
                        cpp_include_dir_option+cpp_defines_option,
                        make_variable_to_use
                        ]
        r += ",".join(cpp_template)
        r += "))"
        write(r)
        pass
    pass

#c CSrc
class CSrc(CModel):
    """
    Same as a C model except it has no 'model'...
    """
    def __init__(self, cpp_filename,
                 **kwargs):
        CModel.__init__(self, model_name=None, cpp_filename=cpp_filename, **kwargs)
        pass
    pass

#c CLibrary
class CLibrary(Module):
    #object = { "lib":model_object["args"][0],
    #           }
    #libs["c"].append( object )
    pass


#c BuildableGroup - parent class for Modules/Executables, which are subclassed in library_desc.py
class BuildableGroup(object):
    name = None
    def __init__(self, get_path):
        self.get_path = get_path
        pass
    @classmethod
    def new_subclasses(cls):
        l = []
        for m in cls.__subclasses__():
            if hasattr(m,"has_been_imported") and m.has_been_imported: continue
            l.append(m)
            m.has_been_imported = True
            pass
        return l
    def get_path_str(self, subpath):
        return str(self.get_path(subpath))
    pass

#c Modules - subclassed in library_desc.py files
class Modules(BuildableGroup):
    name = None
    src_dir = None
    include_dir = None
    modules = []
    libraries = {}
    export_dirs = []
    def __init__(self, **kwargs):
        BuildableGroup.__init__(self, **kwargs)
        for m in self.modules:
            m.set_parent(self)
            pass
        for m in self.modules:
            m.validate()
            pass
        pass
    def makefile_write_entries(self, write, library_name):
        for m in self.modules:
            m.write_makefile(write, library_name)
            pass
        pass
    pass

#c Executables - subclassed in library_desc.py files
class Executables(BuildableGroup):
    name = None
    src_dir = None
    include_dir = None
    cpp_include_dirs = []
    srcs = []
    libraries = {}
    def __init__(self, **kwargs):
        BuildableGroup.__init__(self, **kwargs)
        for m in self.srcs:
            m.set_parent(self)
            pass
        for m in self.srcs:
            m.validate()
            pass
        pass
    def write_makefile_entry(self, write, library_name):
        """
        Write a makefile line for an executable_template invocation
        """
        r = "$(eval $(call executable_template,"
        include_dir_option = ""
        if self.include_dir is not None:
            include_dir_option += "-I "+self.get_path_str(self.include_dir)+" "
            pass
        for i in self.cpp_include_dirs:
            include_dir_option += "-I "+self.get_path_str(i)+" "
            pass
        obj_names = []
        for s in self.srcs:
            obj_names.append(s.obj_filename)
            pass
        lib_names = [library_name]
        for s in self.libraries.keys():
            lib_names.append(s)
            pass
        executable_template = [library_name,
                               self.name,
                               "${BUILD_ROOT}",
                               "${BUILD_DIR}",
                               " ".join(obj_names),
                               " ".join(lib_names),
                               ""
                        ]
        r += ",".join(executable_template)
        r += "))"
        write(r)
        pass
    def makefile_write_entries(self, write, library_name):
        for m in self.srcs:
            m.write_makefile(write, library_name, executable=self.name)
            pass
        self.write_makefile_entry(write, library_name)
        pass
    pass

#c Library class - subclassed in library_desc.py files
class Library:
    def __init__(self, library_path):
        self.path = library_path
        self.modules = Modules.new_subclasses()
        self.executables = Executables.new_subclasses()
        pass
    def get_name(self):
        return self.name
    def iter_modules(self):
        for m in self.modules:
            yield m
            pass
        pass
    def iter_executables(self):
        for m in self.executables:
            yield m
            pass
        pass
    def get_makefile(self):
        return Makefile(self.module.library_name, self.module.modules(), src_root=self.library_directory, build_subdir=self.library_name)
    pass

#a Classes used here
#c Library exceptions
class LibraryLoaded(Exception):
    """
    Not really an error if we allow reloading the same file
    """
    pass
class DuplicateLibrary(Exception):
    def __init__(self, library_name, library_path, other_library_path):
        self.library_name = library_name
        self.library_path=library_path
        self.other_library_path=other_library_path
        pass
    def str(self):
        return "Duplicate library %s (at %s and %s)"%(self.library_name, str(self.library_path), str(self.other_library_path))
    pass
class LibraryNotFound(Exception):
    """
    Indicates a library_desc.py could not be found at library_path
    """
    def __init__(self, library_path):
        self.library_path = library_path
        pass
    def str(self):
        return "Library path %s is invalid or does not contain a library_desc.py file"%(self.library_path)
class UnknownLibrary(Exception):
    def __init__(self, library, library_required):
        self.library = library
        self.library_required = library_required
        pass
    def str(self):
        return "Library %s requires '%s' but that is unknown"%(self.library.get_name(), self.library_required)
class BadLibraryDescription(Exception):
    def __init__(self, library_name, reason):
        self.library_name = library_name
        self.reason = reason
        pass
    def str(self):
        return "%s: Bad library description: %s"%(self.library_name, self.reason)

#c ImportedLibrary class - for each library_desc.py that is loaded (and loading them)
class ImportedLibrary:
    #f __init__
    def __init__(self, library_path, imported_modules):
        """
        Import a library from specified path - it has to contain a library_desc.py file that is importable
        """
        module = None
        try:
            library_path = library_path.resolve(strict=True)
            pass
        except FileNotFoundError:
            raise LibraryNotFound(library_path)
        sys.path.insert(0, library_path.as_posix())
        try:
            module = importlib.import_module("library_desc")
            del sys.modules["library_desc"]
        except:
            raise
        sys.path.pop(0)
        (library, library_name, library_path) = self.validate_library_module(module, imported_modules)
        imported_modules[library_name] = self
        self.path      = library_path
        self.name      = library_name
        self.library   = library
        self.module_instances = []
        self.executable_instances = []
        self.find_dependencies()
        pass
    #f validate_library_module
    def validate_library_module(self, module, imported_modules):
        library_path = Path(module.__file__).parent
        if not hasattr(module, "Library"):
            raise BadLibraryDescription(library_path, "library_desc.py must contain a Library class derived from cdl_desc.Library")
        library = module.Library(library_path)
        library_name = library.get_name()
        if library_name in imported_modules:
            m = imported_modules[library_name]
            if m.path != library_path:
                raise DuplicateLibrary(library_name, library_path, m.path)
            raise LibraryLoaded
        for m in library.iter_modules():
            if type(m.name)!=str: raise BadLibraryDescription(library_name, "library_desc.py module name must be a string (but is %s)"%(str(type(m.name))))
            if type(m.libraries)!=dict: raise BadLibraryDescription(library_name, "library_desc.py module '%s' libraries must be a dict (but is %s)"%(m.name, str(type(m.libraries))))
            pass
        for e in library.iter_executables():
            if type(e.name)!=str: raise BadLibraryDescription(library_name, "library_desc.py executable must be a string (but is %s)"%(str(type(e.name))))
            if type(e.libraries)!=dict: raise BadLibraryDescription(library_name, "library_desc.py executable '%s' libraries must be a dict (but is %s)"%(e.name, str(type(e.libraries))))
            pass
        return (library, library_name, library_path)
    #f get_name
    def get_name(self): return self.name
    #f get_libraries
    def get_libraries(self, required=True):
        if required: return self.required_library_names
        return self.optional_library_names
    #f get_path
    def get_path(self, subpaths=None):
        path = self.path
        if subpaths is not None:
            if type(subpaths)==str: subpaths=[subpaths]
            for s in subpaths:
                path = Path(path, s)
                pass
            pass
        return path
    #f get_exported_paths
    def get_exported_paths(self, relative_to=None):
        e = set()
        for m in self.library.iter_modules():
            for l in m.export_dirs:
                e.add(l)
                pass
            pass
        exports = []
        for ed in e:
            p = Path(self.path,ed)
            if relative_to is not None:
                try: p=p.relative_to(relative_to)
                except: pass
                pass
            exports.append(p)
            pass
        return exports
    #f find_dependencies
    def find_dependencies(self):
        self.required_library_names = []
        self.optional_library_names = []
        for m in self.library.iter_modules():
            for (n,options) in m.libraries.items():
                if options is True:
                    self.required_library_names.append(n)
                    pass
                else:
                    raise Exception("Optional libraries not implemented yet")
                pass
            pass
        pass
    #f create_instances
    def create_instances(self):
        if self.module_instances != []: return
        self.module_instances = []
        for m in self.library.iter_modules():
            instance = m(get_path=self.get_path)
            self.module_instances.append(instance)
            pass
        self.executable_instances = []
        for e in self.library.iter_executables():
            instance = e(get_path=self.get_path)
            self.executable_instances.append(instance)
            pass
        pass
    #f makefile_write_header
    def makefile_write_header(self, write, build_path, library_description_path, relative_to):
        write("LIB_NAME=%s"%self.get_name())
        write("")
        write("include ${CDL_ROOT}/lib/cdl/cdl_templates.mk")
        write("")
        write("BUILD_DIR=%s"%str(build_path))
        write("LIB__${LIB_NAME}__MAKEFILE=${BUILD_DIR}/Makefile")
        write("CDL_FLAGS += --library-desc=%s --source-root=%s"%(library_description_path,relative_to))
        write("")
        pass
    #f makefile_write_footer
    def makefile_write_footer(self, write, library_name):
        write("$(eval $(call library_init_object_file,%s,${BUILD_DIR},lib_%s_init))"%(library_name, library_name))
        write("$(eval $(call cdl_library_template,%s,${BUILD_DIR}))"%(library_name))
        write("")
        pass
    #f create_makefile
    def create_makefile(self, library_name, build_path, library_description_path, relative_to):
        self.create_instances()
        with open(Path(build_path,"Makefile"),"w") as f:
            def write(s): print(s,file=f)
            self.makefile_write_header(write, build_path, library_description_path, relative_to)
            for m in self.module_instances:
                m.makefile_write_entries(write, library_name)
                pass
            for e in self.executable_instances:
                e.makefile_write_entries(write, library_name)
                pass
            self.makefile_write_footer(write, library_name)
            pass
        pass
    #f All done
    pass

#c ImportedLibrarySet class - set of imported libraries
class ImportedLibrarySet:
    #f __init__
    def __init__(self, library_paths_required):
        """
        Import all libraries from required
        """
        self.imported_libraries = {}
        self.required_libraries = []
        self.libraries_to_use = {}
        for path in library_paths_required:
            self.add_library_from_path(path, required=True)
            pass
        pass
    #f add_library_from_path
    def add_library_from_path(self, library_path, required=True):
        try:
            if not Path(library_path,"library_desc.py").is_file: raise LibraryNotFound(library_path)
            lib = ImportedLibrary(library_path, self.imported_libraries)
            if required: self.required_libraries.append(lib)
            pass
        except LibraryLoaded:
            pass
        except DuplicateLibrary:
            raise
        except BadLibraryDescription:
            raise
        except ImportError:
            if required: raise
            pass
        except:
            raise
        pass
    #f accumulate_library_and_dependencies
    def accumulate_library_and_dependencies(self, acc, library_name, include_optional=False):
        """
        add to acc this library and any dependencies it has
        """
        l = self.imported_libraries[library_name]
        if library_name in acc: return acc
        acc[library_name] = l
        
        dependency_names = l.get_libraries(required=True)
        # if include_optional: dependency_names += l.get_libraries(required=False)

        libraries_to_add = []
        for library_name in dependency_names:
            if library_name not in acc:
                if library_name not in self.imported_libraries:
                    raise UnknownLibrary(l, library_name)
                libraries_to_add.append(library_name)
                pass
            pass

        while libraries_to_add!=[]:
            l = libraries_to_add.pop()
            acc = self.accumulate_library_and_dependencies(acc, l, include_optional=False)
            pass
        return acc
    #f calculate_required_set
    def calculate_required_set(self):
        libraries_required = {}
        for l in self.required_libraries:
            libraries_required = self.accumulate_library_and_dependencies(libraries_required, l.get_name(), include_optional=False)
            pass
        self.libraries_to_use = libraries_required
        pass
    #f resolve
    def resolve(self, verbose=None):
        self.calculate_required_set()
        if verbose:
            for (n,l) in self.libraries_to_use.items():
                verbose("%s : %s\n"%(n, str(l.get_path())))
                pass
            pass
        pass
    #f iter_libraries
    def iter_libraries(self):
        """
        Iterate over libraries that are to be used
        """
        return self.libraries_to_use.items()
    #f get_makefile
    def get_makefile(self):
        return Makefile(self.module.library_name, self.module.modules(), src_root=self.library_directory, build_subdir=self.library_name)
    #f set_build_options
    def set_build_options(self, build_root, src_root):
        self.build_root = build_root
        self.src_root = src_root
        self.library_description_path = Path(build_root,"cdl_library_description")
        pass
    #f create_library_description_file
    def create_library_description_file(self):
        with self.library_description_path.open("w") as f:
            for (n,l) in self.iter_libraries():
                print("%s:"% n, file=f)
                for e in l.get_exported_paths(relative_to=self.src_root):
                    print("    %s"%e, file=f)
                    pass
                pass
            pass
        pass
    #f create_library_makefiles
    def create_library_makefiles(self):
        for (n,l) in self.iter_libraries():
            library_build_path = Path(self.build_root,n)
            library_build_path.mkdir(parents=False, exist_ok=True)
            l.create_makefile(n, library_build_path, library_description_path=self.library_description_path, relative_to=self.src_root)
            pass
        pass
    #f makefile_write_header
    def makefile_write_header(self, write):
        write("CDL_ROOT ?= set_cdl_root")
        write("include ${CDL_ROOT}/lib/cdl/cdl_templates.mk")
        write("BUILD_ROOT = %s"%str(self.build_root))
        write("SIM ?= ${BUILD_ROOT}/sim")
        write("all: sim")
        write("SUBMAKE=${MAKE} CDL_ROOT=${CDL_ROOT}")
        write("")
        pass
    #f makefile_write_library_entry
    def makefile_write_library_entry(self, library_name, library, write):
        library_build_path = Path(self.build_root,library_name)
        write("-include %s/Makefile"%(str(library_build_path)))
        write("$(eval $(call sim_add_cdl_library,%s,%s))"%(str(library_build_path),library_name))
        write("${BUILD_ROOT}/%s/Makefile: %s/library_desc.py"%(library_name, str(library.get_path())))
        write("")
        pass
    #f makefile_write_footer
    def makefile_write_footer(self, write):
        library_names = []
        for (n,l) in self.iter_libraries(): library_names.append(n)
        write("$(eval $(call sim_init_object_file,${BUILD_ROOT},obj_init,%s))"%" ".join(library_names))
        write("$(eval $(call command_line_sim,${SIM},${BUILD_ROOT},${BUILD_ROOT}/obj_init.o))")
        write("")
        write("clean: clean_build")
        write("clean_build:")
        write("\trm -f ${SIM}")
        write("\trm -f ${BUILD_ROOT}/obj_init.o")
        write("\tmkdir -p ${BUILD_ROOT}")
        pass
    #f create_makefile
    def create_makefile(self):
        with open(Path(self.build_root,"Makefile"),"w") as f:
            def write(s): print(s,file=f)
            self.makefile_write_header(write)
            for (n,l) in self.iter_libraries():
                self.makefile_write_library_entry(n,l,write)
                pass
            self.makefile_write_footer(write)
            pass
        pass
    pass

    #f All done
    pass

#a Top level
if __name__ == '__main__':
    import argparse, sys, re
    parser = argparse.ArgumentParser(description='Generate MIF or READMEMH files for APB processor ROM')
    parser.add_argument('--require', type=str, nargs='+',
                    help='Required source libraries - the main source library_descs whose dependents have to be included')
    parser.add_argument('--build_root', type=str, default=None,
                    help='Build directory')
    parser.add_argument('--src_root', type=str, default=None,
                    help='Source root to be used for relative paths')
    parser.add_argument('libraries', type=str, nargs='*',
                    help='a directory (possibly) containing a library_desc.py python CDL library description')
    args = parser.parse_args()
    show_usage = False
    if (args.require==[]) or (args.build_root is None):
        show_usage = True
        pass
    if show_usage:
        parser.print_help()
        sys.exit(0)
        pass

    def error_of_exception(e):
        print(e.str(), file=sys.stderr)
        sys.exit(4)
        pass
    def resolve_path_or_else(path, reason):
        try:
            path = Path(path).resolve(strict=True)
            pass
        except FileNotFoundError:
            print(reason, file=sys.stderr)
            sys.exit(4)
            pass
        except:
            raise
        return path
    build_root = resolve_path_or_else(args.build_root,
                                      "Build root '%s' does not exist, but it must"%args.build_root )
    src_root = build_root
    if args.src_root is not None:
        src_root = resolve_path_or_else(args.src_root,
                                        "Specified source root '%s' does not exist"%args.src_root )
        pass
    required_paths = [Path(p).resolve(strict=False) for p in args.require]
    library_paths  = [Path(p).resolve(strict=False) for p in args.libraries]
    try:
        library_set = ImportedLibrarySet(required_paths)
        for l in library_paths:
            library_set.add_library_from_path(l, required=False)
            pass
    except LibraryLoaded: pass
    except DuplicateLibrary as e: error_of_exception(e)
    except BadLibraryDescription as e: error_of_exception(e)
    except LibraryNotFound as e: error_of_exception(e)
    except:
        print("Failed to import libraries", file=sys.stderr)
        raise
    try:
        library_set.resolve() #verbose=sys.stdout.write)
    except UnknownLibrary as e:
        print(e.str(), file=sys.stderr)
        sys.exit(4)
    except:
        raise

    library_set.set_build_options(build_root=build_root, src_root=src_root)
    library_set.create_library_description_file()
    library_set.create_library_makefiles()
    library_set.create_makefile()
    pass
