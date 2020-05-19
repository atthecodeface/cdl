from cdl.utils.memory import Memory

#a Useful invocation function
def get_define_int(defines, k, default):
    if k in defines:
        return int(defines[k],0)
        pass
    return default

#f file_write
def file_write(filename, fn, mode="w"):
    if filename=='-':
        fn(sys.stdout)
        pass
    else:
        f = open(filename, mode)
        fn(f)
        f.close()
        pass
    pass

#f file_read
def file_read(filename, args, fn):
    must_close = False
    f = sys.stdin
    if filename!='-':
        f = open(filename,"r")
        must_close = True
        pass
    mem = Memory()
    fn(mem, f) # base_address, address_mask, sections, ...
    if must_close:
        f.close()
        pass
    return mem

#f dump_main
def dump_main(dump=None, allow_load=True, description='Generate MEM, MIF or C data of memory'):
    import argparse, sys, re
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--mif', type=str, default=None,
                    help='Output MIF filename')
    parser.add_argument('--mem', type=str, default=None,
                    help='Output READMEMH filename')
    parser.add_argument('--c_data', type=str, default=None,
                    help='Output C data filename')
    parser.add_argument('--pxeboot', type=str, default=None,
                    help='Output pxeboot data filename')
    if allow_load:
        parser.add_argument('--load_mif', type=str, default=None,
                            help='MIF file to load')
        parser.add_argument('--load_elf', type=str, default=None,
                            help='ELF file to load')
        parser.add_argument('--load_dump', type=str, default=None,
                            help='Dump file to load')
    args = parser.parse_args()
    if args.load_mif is not None:
        dump = file_read(args.load_mif, args, c_dump.load_mif)
        pass
    if args.load_elf is not None:
        dump = file_read(args.load_elf, args, c_dump.load_elf)
        pass
    if args.load_dump is not None:
        dump = file_read(args.load_dump, args, c_dump.load_dump)
        pass
    if dump is None:
        parse_args.print_help()
        pass
    if args.mif     is not None: file_write(args.mif,     dump.write_mif)
    if args.mem     is not None: file_write(args.mem,     dump.write_mem)
    if args.c_data  is not None: file_write(args.c_data,  dump.write_c_data, mode="wb")
    if args.pxeboot is not None: file_write(args.pxeboot, dump.write_pxeboot)
    pass

#a Toplevel
if __name__ == "__main__":
    dump_main()
