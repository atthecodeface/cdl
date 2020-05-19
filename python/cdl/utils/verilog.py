#a Imports

#a Useful functions
def comma_if_not_last(i,n):
    if i>=n-1: return ""
    return ","

#a Parameter and module classes
#c ParameterInstance
class ParameterInstance(object):
    #f __init__
    def __init__(self, parameter, value):
        self.parameter = parameter
        self.value = value
        pass
    #f verilog_string
    def verilog_string(self, comma=","):
        return ".%s(%s)%s // %s"%(self.parameter.name, self.parameter.verilog_string(self.value), comma, self.parameter.description)

#c Parameter
class Parameter(object):
    name = None
    options = None
    prange = None
    pdefault = None
    def __init__(self, name, values, description):
        self.name = name
        if type(values)==list:
            self.pdefault = values[0]
            self.options = values
            pass
        elif type(values)==tuple:
            self.pdefault = values[0]
            self.prange    = values
            pass
        else:
            self.pdefault = values
            pass
        self.description = description
        pass
    def is_value_permissible(self, value):
        if type(value)==float:
            if type(self.pdefault)!=float: return False
            if self.prange is not None:
                if (value<self.prange[0]) or (value>self.prange[1]): return False
                pass
            return True
        if type(value)==int:
            if type(self.pdefault)!=int: return False
            if self.prange is not None:
                if (value<self.prange[0]) or (value>self.prange[1]): return False
                pass
            if self.options is not None:
                if value not in self.options: return False
                pass
            return True
        if type(value)==str:
            if type(self.pdefault)!=str: return False
            if self.options is not None:
                if value not in self.options: return False
                pass
            return True
        return False
    def instance(self, parameter_dict):
        if self.name not in parameter_dict: return None
        value = parameter_dict[self.name]
        if not self.is_value_permissible(value):
            raise Exception("Value '%s' not permissible for parameter '%s' (options '%s')"%(str(value), self.name, self.options))
        return ParameterInstance(self, value)
    def verilog_string(self, value):
        if type(value)==str: return '"%s"'%value
        return str(value)

#c Module
class Module(object):
    clocks = []
    input_ports = {}
    output_ports = {}
    wires = {}
    submodules = []
    assignments = {}
    parameter_ports = {}
    default_parameters = {}
    default_attributes = {}
    default_signals    = {}
    signals = {} # mapping for an instance
    parameters = {} # mappings for an instance

    #f __init__
    def __init__(self, instance_name, parameters={}, signals={}, attributes={}):
        self.signal_names = [x for (x,_) in self.signals]
        self.instance_name = instance_name
        self.parameter_values = []
        self.submodules = self.submodules[:]
        for p in self.parameters:
            pv = p.instance(parameters)
            if pv is None:
                pv = p.instance(self.default_parameters)
                pass
            if pv is not None:
                self.parameter_values.append(pv)
                pass
            pass
        self.signal_assignments = {}
        for (sn, sv) in self.default_signals.items():
            self.signal_assignments[sn] = sv
            pass
        for (sn, sv) in signals.items():
            self.signal_assignments[sn] = sv
            pass
        for sn in self.signal_assignments:
            if sn not in self.signal_names:
                raise Exception("Unexpected signal %s"%sn)
            pass
        self.attributes = {}
        for (an, av) in self.default_attributes.items():
            self.attributes[an] = av
            pass
        for (an, av) in attributes.items():
            self.attributes[an] = av
            pass
        pass

    #f output_verilog
    def output_verilog(self, f, include_clk_enables=True):
        module_start = "module %s ( "%(self.name)
        indent = " "*len(module_start)
        i = module_start
        for c in self.clocks:
            print("%sinput          %s,"%(i,c), file=f)
            i = indent
            if include_clk_enables:
                print("%sinput          %s__enable,"%(i,c), file=f)
                pass
            pass
        for (s,w) in self.input_ports.items():
            bw = "[%2d:0] "%(w-1)
            if w==0: bw = " "*7
            print("%sinput  %s %s,"%(i,bw,s), file=f)
            i = indent
            pass
        for (s,w) in self.output_ports.items():
            bw = "[%2d:0] "%(w-1)
            if w==0: bw = " "*7
            print("%soutput %s %s,"%(i,bw,s), file=f)
            i = indent
            pass
        print(");", file=f)
        indent = "    "
        for (p,v) in self.parameter_ports.items():
            if type(v)==str:
                print("%sparameter %s=\"%s\";"%(indent,p,v), file=f)
                pass
            else:
                print("%sparameter %s=%s;"%(indent,p,v), file=f)
                pass
            pass
        for (s,(w,e)) in self.wires.items():
            if type(w) == tuple:
                bw = "[%2d:0] "%(w[1]-1)
                print("%swire %s %s[%d:0];"%(indent,bw,s,w[0]-1), file=f)
                pass
            else:
                bw = "[%2d:0] "%(w-1)
                if w==0: bw = " "*7
                if e is None:
                    print("%swire %s %s;"%(indent,bw,s), file=f)
                    pass
                else:
                    print("%swire %s %s = %s;"%(indent,bw,s,e), file=f)
                    pass
                pass
            pass
        for (a,e) in self.assignments.items():
            print("%sassign %s = %s;"%(indent,a,e), file=f)
            pass
        for i in self.submodules:
            i.output_instance_verilog(f, indent)
            pass
        print("endmodule", file=f)
        pass
    #f output_instance_verilog
    def output_instance_verilog(self, f, indent="    "):
        n = len(self.attributes)
        if n>0:
            print("%s(* "%(indent), end=' ', file=f)
            i=0
            for (an, av) in self.attributes.items():
                print('%s = "%s"%s '%(an,av,comma_if_not_last(i,n)), end=' ', file=f)
                i += 1
                pass
            print(" *)", file=f)
            pass
        print("%s%s"%(indent, self.name), end=' ', file=f)

        n = len(self.parameter_values)
        if n>0:
            print(" #(", file=f)
            i=0
            for pv in self.parameter_values:
                print("%s%s%s"%(indent, indent, pv.verilog_string(comma_if_not_last(i,n))), file=f)
                i += 1
                pass
            print("%s) %s ("%(indent, self.instance_name), file=f)
            pass
        else:
            print(" %s ("%(self.instance_name), file=f)
            pass
        n = 0
        for (sn, sv) in self.signals:
            if sn in self.signal_assignments: sv=self.signal_assignments[sn]
            if sv is not None: n += 1
            pass
        i = 0
        for (sn, sv) in self.signals:
            if sn in self.signal_assignments: sv=self.signal_assignments[sn]
            if sv is not None:
                print("%s%s.%s (%s)%s"%(indent, indent, sn, sv, comma_if_not_last(i,n) ), file=f)
                i += 1
                pass
            pass
        print("%s);"%(indent), file=f)
        pass
    #f All done

