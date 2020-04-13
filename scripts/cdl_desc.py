#!/usr/bin/env python3
import sys
import os
import importlib

class Module(object):
    """
    parent is a Modules subclass
    """
    model_name = None
    src_dir = None
    include_dir = None
    parent = None
    inherit = ["src_dir", "include_dir"]
    def __init__(self, model_name, src_dir=None):
        self.model_name = model_name
        if src_dir is not None: self.src_dir=src_dir
        pass
    def validate(self):
        for k in self.inherit:
            if hasattr(self, k):
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
    def __init__(self, model_name,
                 cdl_filename = None,
                 cpp_filename = None,
                 obj_filename = None,
                 verilog_filename = None,
                 cdl_include_dirs = None,
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
    def write_makefile(self, write):
        """
        Write a makefile line for a cdl_template invocation
        """
        r = "$(eval $(call cdl_template,"
        cdl_include_dir_option = ""
        if self.include_dir is not None:
            cdl_include_dir_option += "--include-dir "+self.parent.get_src_path(self.include_dir)+" "
            pass
        for i in self.cdl_include_dirs:
            cdl_include_dir_option += "--include-dir "+self.parent.get_src_path(i)+" "
            pass
        cdl_template = [self.parent.get_src_path(self.src_dir),
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

class CSrc(Module):
    """
    Same as a C model except it has no 'model'...
    """
    pass

class CModel(Module):
    cpp_include_dirs = []
    cpp_defines = {}
    def __init__(self, model_name,
                 cpp_filename = None,
                 obj_filename = None,
                 cpp_include_dirs = None,
                 cpp_defines = {},
                 **kwargs):
        Module.__init__(self, model_name, **kwargs)
        self.cpp_filename     = self.value_or_default(cpp_filename, model_name)
        self.obj_filename     = self.value_or_default(obj_filename, model_name)
        self.cpp_include_dirs = self.value_or_default(cpp_include_dirs, self.cpp_include_dirs)
        self.cpp_defines      = self.value_or_default(cpp_defines,      self.cpp_defines)
        pass
    def write_makefile(self, write):
        """
        Write a makefile line for a cdl_template invocation
        """
        r = "$(eval $(call cpp_template,"
        cpp_include_dir_option = ""
        if self.include_dir is not None:
            cpp_include_dir_option += "-I "+self.parent.get_src_path(self.include_dir)+" "
            pass
        for i in self.cpp_include_dirs:
            cpp_include_dir_option += "-I "+self.parent.get_src_path(i)+" "
            pass
        cpp_defines_option = ""
        for (d,v) in self.cpp_defines.items():
            cpp_defines_option += "-D%s=%s"%(d,v)
            pass
        cpp_template = [self.parent.get_src_path(self.src_dir),
                        "${BUILD_DIR}",
                        self.cpp_filename+".cpp",
                        self.model_name,
                        self.obj_filename+".o",
                        cpp_include_dir_option+cpp_defines_option,
                        ]
        r += ",".join(cpp_template)
        r += "))"
        write(r)
        pass
    pass

class CLibrary(Module):
    #object = { "lib":model_object["args"][0],
    #           }
    #libs["c"].append( object )
    pass


class Modules(object):
    src_dir = None
    include_dir = None
    modules = []
    def __init__(self, src_root):
        self.src_root = src_root
        for m in self.modules:
            m.set_parent(self)
            pass
        for m in self.modules:
            m.validate()
            pass
        pass
    def get_src_path(self, path):
        return os.path.join(self.src_root, path)
    def write_makefile(self, write):
        for m in self.modules:
            m.write_makefile(write)
            pass
        pass
    pass

class Makefile:
    def __init__(self, library_name, modules, src_root=None, cdl_root=None, build_root=None, build_subdir="${LIB_NAME}"):
        if src_root is None: src_root="."
        self.src_root = os.path.abspath(src_root)
        self.library_name = library_name
        self.modules = []
        for m in modules:
            self.modules.append(m(src_root=self.src_root))
            pass
        self.cdl_root = cdl_root
        self.build_root = build_root
        self.build_subdir = build_subdir
        pass
    def write(self, write):
        self.write_header(write)
        for m in self.modules:
            m.write_makefile(write)
            pass
        self.write_footer(write)
        pass
    def write_header(self, write):
        if self.cdl_root is not None:
            write("CDL_ROOT=%s"%self.cdl_root)
            pass
        if self.build_root is not None:
            write("BUILD_ROOT=$(abspath ${CURDIR})/build")
            pass
        write("LIB_NAME=%s"%self.library_name)
        write("")
        write("include ${CDL_ROOT}/lib/cdl/cdl_templates.mk")
        write("")
        write("BUILD_DIR=${BUILD_ROOT}/%s"%(self.build_subdir))
        write("LIB_MAKEFILE=${BUILD_ROOT}/Makefile")
        write("")
        pass
    def write_footer(self, write):
        write("$(eval $(call library_init_object_file,${BUILD_DIR},lib_init,${LIB_NAME}))")
        write("$(eval $(call init_object_file,${BUILD_DIR},obj_init,${LIB_NAME}))")
        write("$(eval $(call cdl_library_template,${BUILD_DIR},${LIB_NAME}))")
        write("$(eval $(call command_line_sim,sim,${BUILD_DIR},${LIB_NAME}))")
        write("")
        write("clean: clean_build")
        write("")
        write("clean_build:")
        write("\trm -rf ${BUILD_DIR}")
        write("\tmkdir -p ${BUILD_DIR}")
        pass
    pass

class Library:
    library_modules = {}
    def __init__(self, library_name, library_directory=None):
        self.library_name = library_name
        self.library_directory = library_directory
        module = None
        if library_directory is not None:
            sys.path = os.path.abspath(library_directory)+sys.path
            pass
        try:
            module = importlib.import_module("library_desc")
            self.library_modules[library_name] = module
            del sys.modules["library_desc"]
        except ImportError as e:
            raise e
        
        if library_directory is not None:
            sys.path.pop(0)
            pass
        self.module = module
        pass
    def get_makefile(self):
        return Makefile(self.library_name, self.module.modules(), src_root=self.library_directory, build_subdir=self.library_name)
    pass


if __name__ == '__main__':
    x = Library("atcf_hardware_apb")
    m = x.get_makefile()
    def write(s):
        print(s)
        pass
    m.write(write)
    pass
