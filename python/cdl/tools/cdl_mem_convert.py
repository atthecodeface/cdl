#!/usr/bin/env python3

#a Imports
import sys, re
import argparse
from typing import Dict, List, Optional, Any, Callable, IO, cast
from cdl.utils.memory import Memory

#a Useful invocation function
def get_define_int(defines:Dict[str,str], k:str, default:int) -> int:
    if k in defines:
        return int(defines[k],0)
    return default

#f file_write
def file_write(filename:str, fn:Callable[[IO[Any]],None], mode:str="w") -> None:
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
def file_read(filename:str, args:'Args', fn:Callable[[Memory,IO[Any]],None]) -> Memory:
    must_close = False
    f = sys.stdin
    if filename!='-':
        f = open(filename,"r")
        must_close = True
        pass
    mem = Memory(bit_width=args.bit_width, num_words=args.num_words)
    fn(mem, f) # base_address, address_mask, sections, ...
    if must_close:
        f.close()
        pass
    return mem

#f dump_main
class Args(object):
    mif  : Optional[str]
    qmif : Optional[str]
    hex  : Optional[str]
    mem  : Optional[str]
    c_data   : Optional[str]
    pxeboot  : Optional[str]
    bit_width : int
    num_words : int
    load_mif  : Optional[str]
    load_elf  : Optional[str]
    load_dump : Optional[str]
    
def dump_main(dump:Optional[Memory]=None,
              allow_load:bool=True,
              description:str='Generate MEM, MIF or C data of memory') -> None:
    """
    Either given a memory (dump), or by loading in memory,
    write out that memory to an appropriate set of files
    in the correct formats
    """
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--mif', type=str, default=None,
                    help='Output MIF filename')
    parser.add_argument('--qmif', type=str, default=None,
                    help='Output Quartus MIF filename')
    parser.add_argument('--hex', type=str, default=None,
                    help='Output Intel hex filename')
    parser.add_argument('--mem', type=str, default=None,
                    help='Output READMEMH filename')
    parser.add_argument('--c-data', type=str, default=None,
                    help='Output C data filename')
    parser.add_argument('--pxeboot', type=str, default=None,
                    help='Output pxeboot data filename')
    parser.add_argument('--bit-width', type=int, default=32,
                    help='Width of each memory word in bits')
    parser.add_argument('--num-words', type=int, default=0,
                    help='Number of memory words')
    if allow_load:
        parser.add_argument('--load-mif', type=str, default=None,
                            help='MIF file to load')
        parser.add_argument('--load-elf', type=str, default=None,
                            help='ELF file to load')
        parser.add_argument('--load-dump', type=str, default=None,
                            help='Dump file to load')
    args = cast(Args,parser.parse_args())
    if args.load_mif is not None:
        dump = file_read(args.load_mif, args, Memory.load_mif)
        pass
    if args.load_elf is not None:
        dump = file_read(args.load_elf, args, Memory.load_elf)
        pass
    if args.load_dump is not None:
        dump = file_read(args.load_dump, args, Memory.load_objdump)
        pass
    if dump is None:
        parser.print_help()
        pass
    assert dump is not None
    if args.mif     is not None: file_write(args.mif,     dump.write_mif)
    if args.qmif    is not None: file_write(args.qmif,    dump.write_quartus_mif)
    if args.hex     is not None: file_write(args.hex,     dump.write_intel_hex)
    if args.mem     is not None: file_write(args.mem,     dump.write_mem)
    if args.c_data  is not None: file_write(args.c_data,  dump.write_c_data, mode="wb")
    if args.pxeboot is not None: file_write(args.pxeboot, dump.write_pxeboot)
    pass

#a Toplevel
if __name__ == "__main__":
    dump_main()
