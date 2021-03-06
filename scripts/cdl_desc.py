#!/usr/bin/env python3
import sys
import os
import importlib
from pathlib import Path

from typing import Type, Dict, List, Tuple, Optional, Callable, TypeVar, Any, Iterable, cast
from types import ModuleType as PythonModule
LibraryDict = Dict[str,int]
Writer = Callable[[str],None]
T = TypeVar('T')
VerboseFn = Callable[[str],None]

#a Documentation
"""
A CDL 2.0 build is built from a collection of CDL libraries.
Each CDL library has a library_desc.py file that describes it.

A CDL library has the form:

> import cdl_desc
> from cdl_desc import CdlModule, CModel
> class Library(cdl_desc.Library):
>    name = "<library name>"
>    pass
> class SomeModules(cdl_desc.Modules):
>    name = "<module set name>"
>    libraries = {"<required library>":True, "<optional library>":False, ...}
>    export_dirs = ["<header files directory relative to library_desc.py directory>", ...]
>    modules = [ cdl_desc.Modules.__subclasses__() instances ]
>    ...
>    pass
>
> class SomeMoreModules(cdl_desc.Modules):
>    ...
>
> class ExecutableBlah(cdl_desc.Executable):
>    name = "<executable name>"
>    srcs = [ cdl_desc.CSrc() instances ]
>    ...
>    pass
> ...

The Modules subclasses contain descriptions of sets of modules in the library

The Executable subclasses contains descriptions of specific C++/C
Sources required by an executable, in addition to any sources in the
rest of the library.

Using this information a build system can put together a Makefile for a library to create
verilog files, lists of verilog files, CDL C models, and compilation scripts to create C
libraries for C simulation.

The build system can also put together an outer Makefile that invokes sets of library Makefiles
given any required information such as the toplevel for a verilog build, or the test harness
C file for a verilator build. (CDL simulation builds do not require a 'toplevel', as they have a
run-time toplevel instantiation.)

"""

"""

SRC_ROOT    = ${GRIP_ROOT_PATH}/atcf_hardware_bbc
BUILD_ROOT  = $(abspath ${CURDIR})/build
VERILOG_DIR = $(abspath ${CURDIR})/verilog
CDL_EXTRA_FLAGS='--v_clks_must_have_enables  --v_use_always_at_star'
MAKE_OPTIONS = SRC_ROOT=${SRC_ROOT} BUILD_ROOT=${BUILD_ROOT} CDL_EXTRA_FLAGS=${CDL_EXTRA_FLAGS}
VERILATOR = PATH=${VERILATOR_ROOT}/bin:${PATH} ${VERILATOR_ROOT}/bin/verilator
BUILD_VERILATOR_DIR = ${BUILD_ROOT}/verilator

FPGA_ROOT    = ${GRIP_ROOT_PATH}/atcf_fpga

TOP = bbc_micro_with_rams
TOP = bbc_micro_de1_cl
all:

make_verilog:
	mkdir -p ${BUILD_ROOT}
	${MAKE} ${MAKE_OPTIONS} -f ${SRC_ROOT}/Makefile clean
	${MAKE} ${MAKE_OPTIONS} -f ${SRC_ROOT}/Makefile makefiles
	${MAKE} ${MAKE_OPTIONS} -f ${SRC_ROOT}/Makefile clean_verilog verilog
	mkdir ${BUILD_ROOT}/verilog
	cp ${BUILD_ROOT}/*/*.v ${BUILD_ROOT}/verilog

make_verilator_old:
	(cd ${BUILD_ROOT} && ${VERILATOR} --cc --top-module ${TOP} -Wno-fatal ${BUILD_ROOT}/verilog/${TOP}.v +incdir+${BUILD_ROOT}/verilog ${VERILOG_DIR}/*v ${VERILOG_DIR}/xilinx/srams.v)
	(cd ${BUILD_ROOT}/obj_dir && make VERILATOR_ROOT=${VERILATOR_SHARE} -f V${TOP}.mk )
	(cd ${BUILD_ROOT}/obj_dir && g++ -o vsim__${TOP} -include V${TOP}.h -DCLK1=clk -DCLK1_P=2 -DVTOP=V${TOP} ${SRC_ROOT}/tb_v/tb_bbc_micro_with_rams.cpp ${VERILATOR_SHARE}/include/verilated.cpp V${TOP}__ALL.a -I ${VERILATOR_SHARE}/include -I.)

VERILATOR_C_FLAGS = -D VM_THREADS=1 -std=c++11
VERILATOR_C_FLAGS = -DVM_COVERAGE=0 -DVM_SC=0 -DVM_TRACE=0 -faligned-new -DVL_THREADED -std=gnu++14
VERILATOR_LIBS = -pthread -lpthread -latomic -lm -lstdc++

$(eval $(call make_verilator_lib,${BUILD_ROOT},${BUILD_VERILATOR_DIR},bbc_micro_de1_cl,${BUILD_ROOT}/verilog/,${BUILD_ROOT}/verilog,${VERILOG_DIR}/*v ${VERILOG_DIR}/verilate/srams.v))

make_verilator:
	(${VERILATOR} --cc --top-module ${TOP} --threads 1 -Mdir ${BUILD_VERILATOR_DIR} -Wno-fatal ${BUILD_ROOT}/verilog/${TOP}.v +incdir+${BUILD_ROOT}/verilog ${VERILOG_DIR}/*v ${VERILOG_DIR}/xilinx/srams.v)
	(cd ${BUILD_VERILATOR_DIR} && make VERILATOR_ROOT=${VERILATOR_SHARE} -f V${TOP}.mk )
	(cd ${BUILD_VERILATOR_DIR} && g++ -o vsim__${TOP} ${VERILATOR_C_FLAGS} -include V${TOP}.h -DCLK1=clk -DCLK1_P=2 -DVTOP=V${TOP} ${SRC_ROOT}/tb_v/tb_bbc_micro_with_rams.cpp ${VERILATOR_SHARE}/include/verilated.cpp V${TOP}__ALL.a -I ${VERILATOR_SHARE}/include -I. ${VERILATOR_LIBS})

y: ${VLIB__bbc_micro_de1_cl__H} ${VLIB__bbc_micro_de1_cl__LIB}
	g++ -o cv_bbc_micro_de1_cl.o -c csrc/cv_bbc_micro_de1_cl.cpp  -I ${CDL_ROOT}/include/cdl/ -I ${VERILATOR_SHARE}/include -I ${VERILATOR_SHARE}/include/vltstd -I ${BUILD_VERILATOR_DIR}
	g++ -o cdl_wrapped_verilator.o -c csrc/cdl_wrapped_verilator.cpp -I ${CDL_ROOT}/include/cdl/ -I ${CDL_ROOT}/../build/cdl/include
	g++ ${VERILATOR_C_FLAGS} ${VERILATOR_SHARE}/include/verilated.cpp cdl_wrapped_verilator.o cv_bbc_micro_de1_cl.o ${BUILD_VERILATOR_DIR}/Vbbc_micro_de1_cl__ALL.a -I ${VERILATOR_SHARE}/include -I. ${VERILATOR_LIBS} -L ${CDL_ROOT}/lib -lcdl_se_batch

z: ${VLIB__bbc_micro_de1_cl__H} ${VLIB__bbc_micro_de1_cl__LIB}
	g++ -g -o cv_bbc_micro_de1_cl.o -r csrc/cv_bbc_micro_de1_cl.cpp  -I ${CDL_ROOT}/include/cdl/ -I ${VERILATOR_SHARE}/include -I ${VERILATOR_SHARE}/include/vltstd -I ${BUILD_VERILATOR_DIR} ${BUILD_VERILATOR_DIR}/Vbbc_micro_de1_cl__ALL.a  -nostartfiles -nodefaultlibs
	g++ -g -o cdl_wrapped_verilator.o -c csrc/cdl_wrapped_verilator.cpp -I ${CDL_ROOT}/include/cdl/ -I ${VERILATOR_SHARE}/include -I ${CDL_ROOT}/../build/cdl/include
	g++ -g ${VERILATOR_C_FLAGS} ${VERILATOR_SHARE}/include/verilated.cpp cdl_wrapped_verilator.o cv_bbc_micro_de1_cl.o  -I ${VERILATOR_SHARE}/include -I. ${VERILATOR_LIBS} -L ${CDL_ROOT}/lib -lcdl_se_batch


x_clean:
	make -f ${FPGA_ROOT}/Makefile ROOT=${FPGA_ROOT} SRC_ROOT=${BUILD_ROOT} VERILOG_DIR=${BUILD_ROOT}/verilog RTL_DIR=${VERILOG_DIR} BUILD_ROOT=${BUILD_ROOT} PROJECTS_DIR=${CURDIR}/projects PROJECT=de1_cl/bbc USE_MTL_AS_VGA= clean

x:
	make -f ${FPGA_ROOT}/Makefile ROOT=${FPGA_ROOT} SRC_ROOT=${BUILD_ROOT} VERILOG_DIR=${BUILD_ROOT}/verilog RTL_DIR=${VERILOG_DIR} BUILD_ROOT=${BUILD_ROOT} PROJECTS_DIR=${CURDIR}/projects PROJECT=de1_cl/bbc USE_MTL_AS_VGA= synth timing fit


mount_xilinx:
	sudo modprobe nbd max_part=8
	sudo qemu-nbd --connect=/dev/nbd0 /vm/images/Vivado19.0.qcow
	sudo qemu-nbd --connect=/dev/nbd1 /vm/images/Altera18_1.qcow2
	sudo mount /dev/nbd0p1 /xilinx
	sudo mount /dev/nbd1p1 /altera

mount_altera:
	sudo modprobe nbd max_part=8
	sudo qemu-nbd --connect=/dev/nbd1 /vm/images/Altera18_1.qcow2
	sudo mount /dev/nbd1p1 /altera
"""

#a Classes used in library_desc.py files
#c Module - base class for module classes
class Module(object):
    """
    parent is a Modules subclass
    """
    model_name       : str
    src_dir          : Optional[str]= None
    src_lib          : Optional[str]= None
    cpp_include_dirs : List[str] = [] # so they can be inherited
    cdl_include_dirs : List[str] = [] # so they can be inherited
    parent           : 'BuildableGroup'
    inherit          = ["src_dir"]
    def write_makefile(self, write:Writer, library_name:str) -> None: ...

    #f write_makefile_debug_comment
    def write_makefile_debug_comment(self, write:Writer) -> None:
        write("# %s"%(self.__class__.__name__))
        for n in dir(self):
            if n[0]!='_':
                write("#    %s : %s"%(n,str(getattr(self,n))))
                pass
            pass
        pass
        
    #f __init__
    def __init__(self, model_name:str, src_dir:Optional[str]=None, src_lib:Optional[str]=None):
        self.model_name = model_name
        if src_dir is not None: self.src_dir=src_dir
        if src_lib is not None: self.src_lib=src_lib
        pass

    #f validate
    def validate(self) -> None:
        assert not hasattr(self, "include_dir")
        for k in self.inherit:
            if hasattr(self, k) and hasattr(self.parent,k):
                self_value = getattr(self, k)
                parent_value = getattr(self.parent,k)
                if self_value is None:
                    setattr(self, k, parent_value)
                    pass
                elif type(self_value) is list:
                    self_value = self_value[:] + parent_value
                    setattr(self, k, self_value)
                    pass
                pass
            pass
        pass
    
    #f value_or_default
    def value_or_default(self, v:Optional[T], d:T) -> T:
        if v is not None: return v
        return d

    #f set_parent
    def set_parent(self, parent:'BuildableGroup') -> None:
        self.parent = parent
        pass
    
    #f set_attr_options
    def set_attr_options(self, obj:object, options:Dict[str,Any]) -> None:
        for (k,v) in options.items():
            if not hasattr(obj, k):
                raise Exception("Option '%s' not known as an attribute"%k)
            setattr(obj,k,v)
            pass
        pass
    
    #f All done
    pass

#c CdlModule
class CdlModule(Module):
    """
    This class describes a model whose source is in CDL

    The output generated is a CPP model for simulation with CDL
    Normally a verilog implementation is also produced

    The CDL source file should, for this build system, include just a single module.
    The *module name* is normally the name of the *model*.
    However, it may be, for example, that a CDL source file provides a generic module,
    with types or constants that are specified for this particular *model*.
    In this case, the *cdl_module_name* should be supplied.

    The CPP, compiled object file, verilog files are assumed to be <model>.<suffix>
    These may be overridden if required.

    The CPP simulation model normally has the name *model*.
    However, sometimes there is a need for more than one CPP simulation model implementation
    for a particular CPP simulation model name. For example, a verilated model, and a plain model;
    or a golden CPP model written by hand and a CDL implementation.
    The standard CDL to CPP compilation of CDL <module name> produces a CPP simulation model called
    <module name>; this can be changed to *name* with registered_name=*name*. The particular implementation
    that the CPP simulation model provides is specified with *implementation_name*.

        if o=="vapi":
            options.append("--v_additional_port_include")
            options.append(v)
        if o=="vabi":
            options.append("--v_additional_body_include")
            options.append(v)
    options.append("--coverage-desc-file")
    options.append("${TARGET_DIR}/"+model_name+".map")
    """
    #c CdlOptions
    class CdlOptions:
        assertions : bool     = False
        system_verilog_assertions : bool     = False
        displays : bool     = False
        coverage : bool     = False
        statements : bool     = False
        multithread : bool     = False
        def cdl_flags(self) -> List[str]:
            """
            Return list of flags required from the properties
            """
            r = []
            if self.assertions:  r.append("--include-assertions")
            if self.system_verilog_assertions:  r.append("--sv-assertions")
            if self.displays:    r.append("--v_displays")
            if self.coverage:    r.append("--include-coverage")
            if self.statements:  r.append("--include-stmt-coverage")
            if self.multithread: r.append("--multithread")
            return r
        pass
    #t Instance properties
    cdl_module_name  : Optional[str]    = None # Name of module within CDL file to be analyzed
    cdl_filename     : str # Name of .cdl file (not including .cdl) in src_dir
    cpp_filename     : str # Name of output .cpp file without suffix
    obj_filename     : str # Name of output .o file without suffix
    verilog_filename : str # Name of output .v file without suffix
    registered_name  : Optional[str] # Name of CDL simulation model, if to be specified
    tool_name        : Optional[str] # Name of e.g. verilated model that a CDL wrapper should use
    implementation   : Optional[str] # Name of CDL simulation model implementation, if to be specified
    cdl_include_dirs : List[str]
    force_includes   : List[str]
    extra_cdlflags   : Dict[str,str]    = {}
    constants        : Dict[str,object] = {} # Dictionary of <constant name> -> value to use for this instance
    types            : Dict[str,str]    = {} # Dictionary of CDL type -> actual CDL type to use for this instance
    instance_types   : Dict[str,str]    = {} # Dictionary of <submodule instance type -> actual submodule type to use for this instance
    cdl_options      : CdlOptions
    build_options    : Dict[str,bool]   = {}
    inherit = Module.inherit[:] + ["cdl_include_dirs"]
    #f __init__
    def __init__(self, model_name:str,
                 cdl_filename :Optional[str]= None,
                 cpp_filename :Optional[str]= None,
                 obj_filename :Optional[str]= None,
                 verilog_filename :Optional[str]= None,
                 cdl_module_name  :Optional[str] =None,
                 registered_name  :Optional[str]= None,
                 tool_name        :Optional[str]= None,
                 implementation   :Optional[str]= None,
                 cdl_include_dirs :List[str] = [],
                 force_includes   :List[str] = [],
                 build_options    :Dict[str,bool] = {},
                 extra_cdlflags   :Dict[str,str] = {},
                 options   :Dict[str,bool] = {},
                 constants :Dict[str,object]   = {}, # dictionary of constant name => value for compilation
                 types     :Dict[str,str]      = {}, # dictionary of source type => desired type for compilation
                 instance_types :Dict[str,str] = {}, # dictionary of source module type => desired type for compilation
                 **kwargs:Any):
        """
        This is a subclass of Module - which has a src_dir option too

        *common options*

        model_name MUST be supplied - it is the makefile target and used to supply default values for filenames
        cdl_filename - name of CDL file in src_dir without .cdl suffix - defaults to model_name
        cdl_include_dirs - list of include directories within the library for includes
        force_includes - list of filenames within include path that are included in CDL compilation as if the first line of the CDL were such includes; used, for example, to force include definition of types for parameterized FIFOs.
        constants - dictionary of name -> value for constants that override definitions in the CDL source code and header files; used to, for example, specify FIFO sizes on parameterized FIFOs.
        types - dictionary of generic_type_name -> type_name for types that override those used in the CDL source code and header files; used to, for example, specify data types of parameterized FIFOs.
        instance_types - dictionary of source module_type_name -> module_type_name to use, for modules that override those used in the CDL source code; used to, for example, specify RAMs for parmaterized FIFOs that use RAMs.
        build_options - dictionary of option -> bool; option can only be 'verilog' at present; use to disable build of verilog from CDL

        *uncommon options* - as in, not used by even experienced hackers

        cpp_filename - name of output CPP file
        obj_filename - name of output OBJ file
        verilog_filename - name of output verilog file
        cdl_module_name - name of module in CDL file if different to *cdl_filename*
        registered_name - name of CPP simulation model as seen by simulation Python files
        implementation_name - name of CPP simulation model implementation as seen by simulation Python files
        extra_cdlflags - dictionary of str->str to cover things not provided for
        options - dictionary of CDL option -> bool, to enable assertions etc
        """
        super(CdlModule,self).__init__(model_name, **kwargs)
        self.cdl_filename     = self.value_or_default(cdl_filename, model_name)
        self.cpp_filename     = self.value_or_default(cpp_filename, model_name)
        self.obj_filename     = self.value_or_default(obj_filename, model_name)
        self.verilog_filename = self.value_or_default(verilog_filename, model_name)
        self.registered_name  = registered_name
        self.tool_name        = tool_name
        self.implementation   = implementation
        self.cdl_include_dirs = cdl_include_dirs + self.cdl_include_dirs
        self.extra_cdlflags   = self.value_or_default(extra_cdlflags, self.extra_cdlflags)
        self.force_includes   = force_includes
        self.cdl_module_name  = cdl_module_name
        if cdl_filename is not None and cdl_module_name is None:
            self.cdl_module_name  = cdl_filename
            pass
        self.constants        = constants
        self.types            = types
        self.instance_types   = instance_types
        self.build_options    = dict(build_options.items())
        self.cdl_options      = self.CdlOptions()
        self.set_attr_options(self.cdl_options, options)
        pass

    #f cdl_flags_string
    def cdl_flags_string(self) -> str:
        """
        Return string of flags required from the properties
        """
        r = ["${CDL_EXTRA_FLAGS} "]
        for i in self.cdl_include_dirs:
            r += ["--include-dir "+self.parent.get_path_str(i)+" "]
            pass
        for i in self.force_includes:
            r += ["--force-include "+i+" "]
            pass
        r += self.cdl_options.cdl_flags()
        for (n,v) in self.extra_cdlflags.items():
            r += ["%s=%s"%(n,str(v))]
            pass
        for (n,vo) in self.constants.items():
            r += ["--constant %s=%s"%(n,str(vo))]
            pass
        for (n,v) in self.types.items():
            r += ["--type-remap %s=%s"%(n,str(v))]
            pass
        if self.cdl_module_name is not None:
            r += ["--remap-module-name %s=%s"%(self.cdl_module_name, self.model_name)]
            pass
        for (n,v) in self.instance_types.items():
            r += ["--remap-instance-type %s.%s=%s"%(self.cdl_module_name,n,str(v))]
            pass
        if self.implementation is not None:
            r += ["--remap-implementation-name %s=%s"%(self.cdl_module_name,self.implementation)]
            pass
        if self.registered_name is not None:
            r += ["--remap-registered-name %s=%s"%(self.cdl_module_name,self.registered_name)]
            pass
        if self.tool_name is not None:
            r += ["--remap-tool-name %s=%s"%(self.cdl_module_name,self.tool_name)]
            pass
        return " ".join(r)

    #f write_makefile
    def write_makefile(self, write:Writer, library_name:str) -> None:
        """
        Write a makefile line for a cdl_template invocation
        """
        verilog_filename = self.verilog_filename+".v"
        if "verilog" in self.build_options and not self.build_options["verilog"]:
            verilog_filename=""
            pass
        src_file = self.parent.get_path_str(self.src_dir)
        r = "$(eval $(call cdl_template,"
        cdl_template = [library_name,
                        src_file,
                        "${BUILD_DIR}",
                        self.cdl_filename+".cdl",
                        self.model_name,
                        self.cpp_filename+".cpp",
                        self.obj_filename+".o",
                        verilog_filename,
                        self.cdl_flags_string(),
                        ]
        r += ",".join(cdl_template)
        r += "))"
        write(r)
        pass

    #f All done
    pass

#c CdlSimVerilatedModule - subclassed in library_desc.py files
class CdlSimVerilatedModule(CdlModule):
    """
    This is a CPP simulation module only.

    It requires a CDL file that provides the CDL module from which verilog
    is produced
    """
    cdl_include_dirs : List[str]     = []
    force_includes   : List[str]     = []
    cdl_filename : str
    model_name : str
    cpp_filename : str
    obj_filename : str
    extra_verilog : List[str]
    #f __init__
    def __init__(self, model_name:str,
                 cdl_filename     : Optional[str]= None,
                 verilog_filename : Optional[str]= None,
                 top_module       : Optional[str]= None,
                 implementation   : Optional[str]= None,
                 extra_verilog    : List[str]    = [],
                 **kwargs:Any):
        self.verilog_filename    = self.value_or_default(verilog_filename, model_name)      # Source containing top module
        self.top_module          = self.value_or_default(top_module, self.verilog_filename) # toplevel module inside source the CDL matches
        implementation           = self.value_or_default(implementation, "verilated")
        super(CdlSimVerilatedModule,self).__init__(
            model_name       = model_name,
            cdl_filename     = cdl_filename,
            verilog_filename = self.verilog_filename,
            tool_name        = self.top_module,
            implementation   = implementation,
            **kwargs)
        self.extra_verilog       = extra_verilog
        self.build_options["verilog"] = False
        pass

    #f write_makefile
    def write_makefile(self, write:Writer, library_name:str) -> None:
        """
        Write the makefile entries for an make_verilator_lib invocation
        """
        verilate_dir = "${BUILD_DIR}/verilate"  # where to build verilator stuff
        other_verilog_files = [""]
        other_verilog_files += [self.verilog_filename]
        other_verilog_dirs  = [""]
        other_verilog_files += ["${CDL_VERILOG_DIR}/verilator/srams.v"]
        other_verilog_files += ["${CDL_VERILOG_DIR}/verilator/clock_gate_module.v"]
        for f in self.extra_verilog:
            other_verilog_files += ["${BUILD_DIR}/%s"%(f)]
            pass
        other_verilog_dirs += ["$(wildcard ${BUILD_DIR}/../*)"] # (hack)

        r = "$(eval $(call make_verilator_lib_template,"
        make_verilator_lib_template = [
            library_name,
            "${BUILD_DIR}", # Output directory (BUILD_DIR is library-specific)
            verilate_dir,
            self.top_module, # module (top for verilator)
            "${BUILD_DIR}", # Source verilog directory
            " ".join(other_verilog_dirs),  # searched for <module>.v
            " ".join(other_verilog_files), # automatically included
        ]
        r += ",".join(make_verilator_lib_template)
        r += "))"
        write(r)

        r = "$(eval $(call cwv_template,"
        cwv_template = [
            library_name,
            self.parent.get_path_str(self.src_dir),
            "${BUILD_DIR}",
            self.cdl_filename+".cdl", # This provides the clocks, inputs and outputs of the module
            self.model_name,
            self.top_module,
            self.cpp_filename+".cpp",
            self.obj_filename+".o",
            self.cdl_flags_string(),
            verilate_dir,
        ]
        r += ",".join(cwv_template)
        r += "))"
        write(r)
        pass
    #f All done
    pass

#c Verilog
class Verilog(Module):
    #t Instance properties
    inherit = Module.inherit[:]

    #f __init__
    def __init__(self, model_name:str,
                 verilog_filename:Optional[str] = None,
                 **kwargs:Any):
        super(Verilog,self).__init__(model_name, **kwargs)
        self.verilog_filename = self.value_or_default(verilog_filename, model_name+".v")
        pass

    #f write_makefile
    def write_makefile(self, write:Writer, library_name:str, executable:Optional[str]=None) -> None:
        """
        Write a makefile line for a verilog_template invocation
        """
        r = "$(eval $(call verilog_template,"
        cpp_template = [library_name,
                        self.parent.get_path_str(self.src_dir),
                        "${BUILD_DIR}",
                        self.verilog_filename,
                        self.model_name,
                        ]
        r += ",".join(cpp_template)
        r += "))"
        write(r)
        pass

    #f All done
    pass

#c CModel
class CModel(Module):
    #t Instance properties
    cpp_defines      : Dict[str,str] = {}
    inherit = Module.inherit[:] + ["cpp_include_dirs"]

    #f __init__
    def __init__(self, model_name:str,
                 cpp_filename:Optional[str] = None,
                 obj_filename:Optional[str] = None,
                 cpp_include_dirs:List[str] = [],
                 cpp_defines:Dict[str,str] = {},
                 **kwargs:Any):
        super(CModel,self).__init__(model_name=model_name, **kwargs)
        self.cpp_filename     = self.value_or_default(cpp_filename, model_name)
        self.obj_filename     = self.value_or_default(obj_filename, self.cpp_filename)
        self.cpp_include_dirs = cpp_include_dirs + self.cpp_include_dirs
        self.cpp_defines      = self.value_or_default(cpp_defines,      self.cpp_defines)
        pass

    #f write_makefile
    def write_makefile(self, write:Writer, library_name:str, executable:Optional[str]=None) -> None:
        """
        Write a makefile line for a cpp_template invocation
        """
        r = "$(eval $(call cpp_template,"
        cpp_include_dir_option = ""
        assert not hasattr(self, "include_dir")
        for i in self.cpp_include_dirs:
            cpp_include_dir_option += "-I "+self.parent.get_path_str(i)+" "
            pass
        cpp_defines_option = ""
        for (d,v) in self.cpp_defines.items():
            cpp_defines_option += "-D%s=%s"%(d,v)
            pass
        model_name_to_use = self.model_name
        make_variable_to_use = ""
        if executable is not None: make_variable_to_use=executable # Add it to the library
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

    #f All done
    pass

#c CSrc
class CSrc(CModel):
    """
    Same as a C model except it has no 'model', so model_name=""...
    """
    def __init__(self, cpp_filename:str,
                 **kwargs:Any):
        super(CSrc,self).__init__(model_name="", cpp_filename=cpp_filename, **kwargs)
        pass
    pass

#c CLibrary
class CLibrary(Module):
    #object = { "lib":model_object["args"][0],
    #           }
    #libs["c"].append( object )
    pass

#c BuildableGroup - parent class for Modules/Executable, which are subclassed in library_desc.py
class Resolver(object):
    def get_path(self, subpaths:List[Path], library_name:Optional[str]=None) -> Path: ...
    pass
class BuildableGroup(object):
    #t Instance types
    name    : str
    src_dir : Optional[str] = None
    resolver : Type[Resolver]
    has_been_imported : bool # This gets set when the module is part of a Modules

    # __init__
    def __init__(self, resolver:Type[Resolver]):
        self.resolver = resolver
        pass

    #f new_subclasses
    @classmethod
    def new_subclasses(cls) -> List[Type['BuildableGroup']]:
        l = []
        for m in cls.__subclasses__():
            if hasattr(m,"has_been_imported") and m.has_been_imported: continue
            l.append(m)
            m.has_been_imported = True
            pass
        return l

    #f get_path_str
    def get_path_str(self, subpath:Optional[str], lib:Optional[str]=None ) -> str:
        subpath_list = []
        if subpath is not None: subpath_list = [Path(subpath)]
        return str(self.resolver.get_path(subpath_list, lib))

    #f makefile_write_entries - must be supplied by subclass
    def makefile_write_entries(self, write:Writer, library_name:str) -> None: ...
    #f All done
    pass

#c Modules - subclassed in library_desc.py files
class Modules(BuildableGroup):
    #t Instance types
    modules     : List[Module] = []
    libraries   : LibraryDict = {}
    export_dirs : List[str]   = []
    #f validate - classmethod, validate this class, return error string or None
    @classmethod
    def validate(cls) -> Optional[str]:
        """
        Invoked while examining library_desc.py to validate the file a little
        """
        if type(cls.name)!=str: return "name must be a string (but is %s)"%(str(type(cls.name)))
        if type(cls.libraries)!=dict: return "module '%s' libraries must be a dict (but is %s)"%(cls.name, str(type(cls.libraries)))
        return None

    #f __init__
    def __init__(self, **kwargs:Any):
        super(Modules,self).__init__(**kwargs)
        for m in self.modules:
            m.set_parent(self)
            pass
        for m in self.modules:
            m.validate()
            pass
        pass

    #f makefile_write_entries
    def makefile_write_entries(self, write:Writer, library_name:str) -> None:
        for m in self.modules:
            m.write_makefile(write, library_name)
            pass
        pass
    
    #f All done
    pass

#c Executable - subclassed in library_desc.py files
class Executable(BuildableGroup):
    #t Instance types
    cpp_include_dirs : List[str]  = []
    srcs             : List[CSrc] = []
    libraries        : LibraryDict = {}
    #f validate - classmethod
    @classmethod
    def validate(cls) -> Optional[str]:
        """
        Invoked while examining library_desc.py to validate the file a little
        """
        if type(cls.name)!=str: return "name must be a string (but is %s)"%(str(type(cls.name)))
        if type(cls.libraries)!=dict: return "module '%s' libraries must be a dict (but is %s)"%(cls.name, str(type(cls.libraries)))
        return None
    #f __init__
    def __init__(self, **kwargs:Any):
        super(Executable,self).__init__(**kwargs)
        for s in self.srcs:
            s.set_parent(self)
            pass
        for s in self.srcs:
            s.validate()
            pass
        pass
    #f write_makefile_entry
    def write_makefile_entry(self, write:Writer, library_name:str) -> None:
        """
        Write a makefile line for an executable_template invocation
        """
        r = "$(eval $(call executable_template,"
        include_dir_option = ""
        assert not hasattr(self, "include_dir")
        for i in self.cpp_include_dirs:
            include_dir_option += "-I "+self.get_path_str(i)+" "
            pass
        obj_names = []
        for s in self.srcs:
            obj_names.append(s.obj_filename)
            pass
        lib_names = [library_name]
        for ln in self.libraries.keys():
            lib_names.append(ln)
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
    #f makefile_write_entries
    def makefile_write_entries(self, write:Writer, library_name:str) -> None:
        for m in self.srcs:
            m.write_makefile(write, library_name, executable=self.name)
            pass
        self.write_makefile_entry(write, library_name)
        pass
    #f All done
    pass

#c Library class - subclassed in library_desc.py files
class Library:
    name : str
    #f __init__
    def __init__(self, library_path:Path):
        self.path = library_path
        self.modules          = Modules.new_subclasses()
        self.executables      = Executable.new_subclasses()
        self.buildables = []
        self.buildables += self.modules
        self.buildables += self.executables
        pass
    #f get_name
    def get_name(self) -> str:
        return self.name
    #f iter_modules
    def iter_modules(self) -> Iterable[Type[Modules]]:
        for m in self.modules:
            yield cast(Type[Modules],m)
            pass
        pass
    #f iter_buildables
    def iter_buildables(self) -> Iterable[Type[BuildableGroup]]:
        for m in self.buildables: yield m
        pass
    pass

#a Classes used here
#c Base LibraryException
class LibraryException(Exception):
    def str(self) -> str: ...
    pass

#c LibraryLoaded Exception
class LibraryLoaded(LibraryException):
    """
    Not really an error if we allow reloading the same file
    """
    pass

#c DuplicateLibrary Exception
class DuplicateLibrary(LibraryException):
    def __init__(self, library_name:str, library_path:Path, other_library_path:Path):
        self.library_name = library_name
        self.library_path=library_path
        self.other_library_path=other_library_path
        pass
    def str(self) -> str:
        return "Duplicate library %s (at %s and %s)"%(self.library_name, str(self.library_path), str(self.other_library_path))
    pass

#c LibraryNotFound Exception
class LibraryNotFound(LibraryException):
    """
    Indicates a library_desc.py could not be found at library_path
    """
    def __init__(self, library_path:Path):
        self.library_path = library_path
        pass
    def str(self) -> str:
        return "Library path %s is invalid or does not contain a library_desc.py file"%(self.library_path)
    pass

 #c UnknownLibrary Exception
class UnknownLibrary(LibraryException):
    def __init__(self, library:'ImportedLibrary', library_required:str):
        self.library = library
        self.library_required = library_required
        pass
    def str(self) -> str:
        return "Library %s requires '%s' but that is unknown"%(self.library.get_name(), self.library_required)
    pass

#c BadLibraryDescription Exception
class BadLibraryDescription(LibraryException):
    def __init__(self, library_path:Path, reason:str):
        self.library_path = library_path
        self.reason = reason
        pass
    def str(self) -> str:
        return "%s: Bad library description: %s"%(str(self.library_path), self.reason)

#c ImportedLibrary class - for each library_desc.py that is loaded (and loading them)
class ImportedLibrary(Resolver):
    name : str
    path : Path
    library : Library
    buildable_instances : List[BuildableGroup]= []
    required_library_names : List[str]
    optional_library_names : List[str]
    library_set            :'ImportedLibrarySet'
    #f __init__
    def __init__(self, library_path:Path, library_set:'ImportedLibrarySet'):
        """
        Import a library from specified path - it has to contain a library_desc.py file that is importable
        """
        self.library_set = library_set
        python_module = None
        try:
            library_path = library_path.resolve(strict=True)
            pass
        except FileNotFoundError:
            raise LibraryNotFound(library_path)
        sys.path.insert(0, library_path.as_posix())
        try:
            python_module = importlib.import_module("library_desc")
            del sys.modules["library_desc"]
        except ModuleNotFoundError as e:
            raise LibraryNotFound(library_path)
        except Exception as e:
            raise e
        sys.path.pop(0)
        (library, library_name, library_path) = self.validate_library_module(python_module)
        self.library_set.add_library(library_name, self)
        self.path      = library_path
        self.name      = library_name
        self.library   = library
        self.buildable_instances = []
        self.find_dependencies()
        pass
    
    #f validate_library_module
    def validate_library_module(self, python_module:PythonModule) -> Tuple[Library, str, Path]:
        library_path = Path(python_module.__file__).parent
        if not hasattr(python_module, "Library"):
            raise BadLibraryDescription(library_path, "library_desc.py must contain a Library class derived from cdl_desc.Library")
        # get mypy to ignore getting Library attribute - it has got one as we just discovered
        library = python_module.Library(library_path) # type: ignore
        library_name = library.get_name()
        m = self.library_set.find_library(library_name)
        if m is not None:
            if m.path != library_path:
                raise DuplicateLibrary(library_name, library_path, m.path)
            raise LibraryLoaded
        for b in library.iter_buildables():
            error = b.validate()
            if error is not None: raise BadLibraryDescription(library_path, error)
            pass
        return (library, library_name, library_path)

    #f get_name
    def get_name(self) -> str:
        return self.name

    #f get_libraries
    def get_libraries(self, required:bool=True) -> List[str]:
        if required: return self.required_library_names
        return self.optional_library_names
    
    #f get_path
    def get_path(self, subpaths:List[Path]=[], library_name:Optional[str]=None) -> Path:
        if library_name is not None:
            m = self.library_set.find_library(library_name)
            if m is None: raise UnknownLibrary(self, library_name)
            return m.get_path(subpaths=subpaths, library_name=None)
        path = self.path
        for s in subpaths:
            path = Path(path, s)
            pass
        return path
    
    #f get_exported_paths
    def get_exported_paths(self, relative_to:Optional[Path]=None) -> List[Path]:
        """
        Get a list (without duplicates) of exported directories
        for all the modules in the library
        """
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
    def find_dependencies(self) -> None:
        """
        Find list of library dependencies without duplicates

        This might do optional or build-time options in the future
        """
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
    def create_instances(self) -> None:
        if self.buildable_instances != []: return
        self.buildable_instances = []
        for b in self.library.iter_buildables():
            instance = b(resolver=self)
            self.buildable_instances.append(instance)
            pass
        pass

    #f makefile_write_header
    def makefile_write_header(self, write:Writer, build_path:Path, library_description_path:Path, relative_to:Path) -> None:
        write("LIB_NAME=%s"%self.get_name())
        write("")
        write("include ${CDL_ROOT}/lib/cdl/cdl_templates.mk")
        write("")
        write("BUILD_DIR=%s"%str(build_path))
        write("")
        write("$(eval $(call library_init_template,${LIB_NAME},${BUILD_DIR},%s,%s,%s))"%(str(self.get_path()),library_description_path,relative_to))
        write("")
        write("LIB__${LIB_NAME}__MAKEFILE=${BUILD_DIR}/Makefile")
        write("CDL_FLAGS += --library-desc=%s --source-root=%s"%(library_description_path,relative_to))
        write("")
        pass

    #f makefile_write_footer
    def makefile_write_footer(self, write:Writer, library_name:str) -> None:
        write("$(eval $(call library_init_object_file,%s,${BUILD_DIR},lib_%s_init))"%(library_name, library_name))
        write("$(eval $(call cdl_library_template,%s,${BUILD_DIR}))"%(library_name))
        write("")
        pass

    #f create_makefile
    def create_makefile(self, library_name:str, build_path:Path, library_description_path:Path, relative_to:Path) -> None:
        self.create_instances()
        with open(Path(build_path,"Makefile"),"w") as f:
            def write(s:str)->None:
                print(s,file=f)
                pass
            self.makefile_write_header(write, build_path, library_description_path, relative_to)
            for bi in self.buildable_instances:
                bi.makefile_write_entries(write, library_name)
                pass
            self.makefile_write_footer(write, library_name)
            pass
        pass

    #f All done
    pass

#c ImportedLibrarySet class - set of imported libraries
class ImportedLibrarySet:
    #t Instance properties
    imported_libraries : Dict[str,ImportedLibrary]
    required_libraries : List[ImportedLibrary]
    optional_libraries : List[ImportedLibrary]
    libraries_to_use   : Dict[str,ImportedLibrary]
    library_paths_required : List[Path]
    build_root : Path
    src_root : Path
    library_description_path : Path
    
    #f __init__
    def __init__(self, required_paths:List[Path], optional_paths:List[Path]):
        """
        Import all libraries from required
        """
        self.imported_libraries = {}
        self.required_libraries = []
        self.optional_libraries = []
        self.libraries_to_use = {}
        self.library_paths_required = required_paths
        for path in required_paths:
            try:
                self.add_library_from_path(path, required=True)
                pass
            except:
                raise
            pass
        for path in optional_paths:
            try:
                self.add_library_from_path(path, required=False)
                pass
            except LibraryLoaded: pass
            except DuplicateLibrary: pass
            except LibraryNotFound: pass
            except:
                raise
            pass
        pass

    #f add_library - invoked by ImportedLibrary to add itself to the set of libraries
    def add_library(self, library_name:str, library:ImportedLibrary) -> None:
        self.imported_libraries[library_name] = library
        pass
        
    #f find_library - invoked by ImportedLibrary to add itself to the set of libraries
    def find_library(self, library_name:str) -> Optional[ImportedLibrary]:
        if library_name in self.imported_libraries:
            return self.imported_libraries[library_name]
        return None
        
    #f add_library_from_path
    def add_library_from_path(self, library_path:Path, required:bool=True) -> None:
        try:
            if not Path(library_path,"library_desc.py").is_file: raise LibraryNotFound(library_path)
            lib = ImportedLibrary(library_path, self)
            if required: self.required_libraries.append(lib)
            else: self.optional_libraries.append(lib)
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
    def accumulate_library_and_dependencies(self, acc:Dict[str,ImportedLibrary], library_name:str, include_optional:bool=False) -> Dict[str,ImportedLibrary]:
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
            ln = libraries_to_add.pop()
            acc = self.accumulate_library_and_dependencies(acc, ln, include_optional=False)
            pass
        return acc

    #f calculate_required_set
    def calculate_required_set(self) -> None:
        libraries_required :Dict[str,ImportedLibrary]= {}
        for l in self.required_libraries:
            libraries_required = self.accumulate_library_and_dependencies(libraries_required, l.get_name(), include_optional=False)
            pass
        self.libraries_to_use = libraries_required
        pass

    #f resolve
    def resolve(self, verbose:Optional[VerboseFn]=None) -> None:
        self.calculate_required_set()
        if verbose is not None:
            for (n,l) in self.libraries_to_use.items():
                verbose("%s : %s\n"%(n, str(l.get_path())))
                pass
            pass
        pass
    
    #f iter_libraries
    def iter_libraries(self) -> Iterable[Tuple[str,ImportedLibrary]]:
        """
        Iterate over libraries that are to be used
        """
        return self.libraries_to_use.items()

    #f set_build_options
    def set_build_options(self, build_root:Path, src_root:Path) -> None:
        self.build_root = build_root
        self.src_root = src_root
        self.library_description_path = Path(build_root,"cdl_library_description")
        pass

    #f create_library_description_file
    def create_library_description_file(self) -> None:
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
    def create_library_makefiles(self) -> None:
        for (n,l) in self.iter_libraries():
            library_build_path = Path(self.build_root,n)
            library_build_path.mkdir(parents=False, exist_ok=True)
            l.create_makefile(n, library_build_path, library_description_path=self.library_description_path, relative_to=self.src_root)
            pass
        pass

    #f makefile_write_header
    def makefile_write_header(self, write:Writer) -> None:
        default_cdl_root = "set_cdl_root"
        if "CDL_ROOT" in os.environ: default_cdl_root=os.environ["CDL_ROOT"]
        write("CDL_ROOT ?= %s"%default_cdl_root)
        write("include ${CDL_ROOT}/lib/cdl/cdl_templates.mk")
        write("BUILD_ROOT = %s"%str(self.build_root))
        write("SIM   ?= ${BUILD_ROOT}/sim")
        write("PYSIM ?= ${BUILD_ROOT}/py_engine.so")
        write("all: sim")
        write("SUBMAKE=${MAKE} CDL_ROOT=${CDL_ROOT}")
        write("")
        write("$(eval $(call toplevel_init_template))")
        write("")
        r = "$(eval $(call cdl_makefile_template,"
        makefile_template = [" ".join(str(l) for l in self.library_paths_required),
                             str(self.build_root),
                             " ".join([str(l.get_path()) for l in self.optional_libraries]),
        ]
        r += ",".join(makefile_template)
        r += "))"
        write(r)
        pass

    #f makefile_write_library_entry
    def makefile_write_library_entry(self, library_name:str, library:ImportedLibrary, write:Writer) -> None:
        library_build_path = Path(self.build_root,library_name)
        write("-include %s/Makefile"%(str(library_build_path)))
        write("$(eval $(call sim_add_cdl_library,%s,%s))"%(str(library_build_path),library_name))
        write("${BUILD_ROOT}/%s/Makefile: %s/library_desc.py"%(library_name, str(library.get_path())))
        write("")
        pass
    
    #f makefile_write_footer
    def makefile_write_footer(self, write:Writer) -> None:
        library_names = []
        for (n,l) in self.iter_libraries(): library_names.append(n)
        write("$(eval $(call sim_init_object_file_template,${BUILD_ROOT},obj_init,%s))"%" ".join(library_names))
        write("$(eval $(call command_line_sim_template,${SIM},${BUILD_ROOT},${BUILD_ROOT}/obj_init.o))")
        write("$(eval $(call python_library_template,${PYSIM},${BUILD_ROOT},${BUILD_ROOT}/obj_init.o))")

        write("")
        write("$(eval $(call toplevel_clean_template))")
        pass

    #f create_makefile
    def create_makefile(self) -> None:
        with open(Path(self.build_root,"Makefile"),"w") as f:
            def write(s:str) -> None:
                print(s,file=f)
                pass
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
#f error_of_exception
def error_of_exception(e:LibraryException) -> str:
    print(e.str(), file=sys.stderr)
    sys.exit(4)
    pass
    
#f resolve_path_or_else
def resolve_path_or_else(path_str:str, reason:str) -> Path:
    try:
        path = Path(path_str).resolve(strict=True)
        pass
    except FileNotFoundError:
        print(reason, file=sys.stderr)
        sys.exit(4)
        pass
    except:
        raise
    return path

#f main
if __name__ == '__main__':
    import argparse, sys, re
    parser = argparse.ArgumentParser(description='Generate MIF or READMEMH files for APB processor ROM')
    parser.add_argument('--require', action='append', required=True,
                    help='Required source libraries - the main source library_descs whose dependents have to be included')
    parser.add_argument('--build_root', type=str, default=None, required=True,
                    help='Build directory')
    parser.add_argument('--src_root', type=str, default=None,
                    help='Source root to be used for relative paths')
    parser.add_argument('libraries', nargs='*',
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

    build_root = resolve_path_or_else(args.build_root,
                                      "Build root '%s' does not exist, but it must"%args.build_root )
    src_root = build_root
    if args.src_root is not None:
        src_root = resolve_path_or_else(args.src_root,
                                        "Specified source root '%s' does not exist"%args.src_root )
        pass

    required_paths = [Path(p).resolve(strict=False) for p in args.require]
    optional_paths = [Path(p).resolve(strict=False) for p in args.libraries]

    try:
        library_set = ImportedLibrarySet(required_paths, optional_paths)
        pass
    except BadLibraryDescription as e:
        error_of_exception(e)
        pass
    except LibraryNotFound as e:
        error_of_exception(e)
        pass
    except:
        print("Failed to import libraries", file=sys.stderr)
        raise
    try:
        library_set.resolve() #verbose=sys.stdout.write)
    except UnknownLibrary as e:
        error_of_exception(e)
    except:
        raise

    library_set.set_build_options(build_root=build_root, src_root=src_root)
    library_set.create_library_description_file()
    library_set.create_library_makefiles()
    library_set.create_makefile()
    pass
