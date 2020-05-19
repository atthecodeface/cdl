#!/usr/bin/env python
import re
import os
import argparse
param_re = re.compile(r"(.*)#(.*)")
class remap:
    def __init__(self, module_name, module_type=None, parameters=None):
        self.module_name = module_name
        self.module_type = module_type
        self.parameters  = parameters
        self.module_re = re.compile(r"(.*) %s\((.*)"%self.module_name)
        self.parameter_string = ""
        for (pn,pv) in self.parameters.iteritems():
            if self.parameter_string!="":
                self.parameter_string = "%s, %s(%s)"%(self.parameter_string,pn,pv)
                pass
            else:
                self.parameter_string = "#(.%s(%s)"%(pn,pv)
                pass
            pass
        if self.parameter_string!="":
            self.parameter_string = " %s) "%self.parameter_string
            pass
        else:
            self.parameter_string = " "
            pass
        pass
    def rewrite_file(self, lines):
        new_lines = []
        for l in lines:
            match = self.module_re.search(l)
            if match is not None:
                unparam = match.group(1)
                unparam_match = param_re.match(unparam)
                if unparam_match is not None: unparam=unparam_match.group(1)
                unparam = unparam.rstrip(' ')
                if self.module_type is not None:
                    indent = unparam.split(unparam.lstrip())[0]
                    unparam = indent + self.module_type
                    pass
                l = "%s%s%s(%s"%(unparam, self.parameter_string, self.module_name, match.group(2))
                pass
            new_lines.append(l)
            pass
        return new_lines
    pass

class parametrize_file:
    filename = "file.v"
    reamppings = [] # list of remap objects
    def __init__(self, filename=None, remappings=None):
        if remappings is not None: self.remappings = remappings
        f = open(filename)
        lines = []
        for l in f:
            l = l.rstrip()
            lines.append(l)
            pass
        f.close()
        self.file_lines = lines
        pass
    def rewrite_verilog(self, filename, backup=True):
        lines = self.file_lines
        for r in self.remappings:
            lines = r.rewrite_file(lines)
            pass
        if backup:
            try:
                os.unlink(filename+".bkp")
                pass
            except:
                pass
            os.rename(filename, filename+".bkp")
            pass
        f = open("%s"%(filename),"w")
        for l in lines:
            print >>f, l
            pass
        f.close()
        pass
    pass

#a Toplevel
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Update verilog file with remapping for a module instance')
    parser.add_argument('--file', type=str, default=None, required=True,
                    help='Verilog file to change')
    parser.add_argument('--module', type=str, default=None, required=True,
                    help='Module instance name to change')
    parser.add_argument('--type', type=str, default=None,
                    help='Instance type to remap to')
    parser.add_argument('--parameter', type=str, default=[], action='append',
                    help='Add parameter "a=b" to module')
    parser.add_argument('--no_backup', type=str, default=False,
                    help='Suppress backup')
    args = parser.parse_args()
    parameters = {}
    pre = re.compile(r"(.*)=(.*)")
    for p in args.parameter:
        m = pre.match(p)
        if m is None:
            parameters[p] = 1
            pass
        else:
            parameters[m.group(1)] = m.group(2)
            pass
        pass
    remappings = []
    remappings.append(remap(args.module, args.type, parameters))
    pf = parametrize_file(filename=args.file, remappings=remappings)
    pf.rewrite_verilog(filename=args.file, backup=not args.no_backup)
