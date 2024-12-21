#a Documentation
"""
This module provides a Memory class

The Memory has contents that is stored in a dictionary of address -> value
The addresses are word addresses for the memory - the memory may have a word of any number of bits
The memory also supports labels, which are mappings from strings to integers (usually word addresses)
Particularly the entry_point

The class supports loading and writing the memory in many different formats, including:

Loading:
  binary, simple hex, objdump output, hex address/data, ELF

Writing:
  C, Intel Hex, Quartus MIF, plain text, pxeboot
"""

#a Imports
import re
import sys, struct
HAVE_ELF = False
try:
    import elftools.elf.elffile # type: ignore
    HAVE_ELF = True
    pass
except:
    pass
from typing import Dict, List, Any, Tuple, Optional, IO, Iterable, Sequence

#a Useful functions
def write_u16(f:IO[bytes],d:int) -> None:
    f.write(struct.pack('<H', d))
    pass

def write_u32(f:IO[bytes],d:int) -> None:
    f.write(struct.pack('<I', d))
    pass

#a Classes
#c Descriptor
class Descriptor(object):
    def __init__(self) -> None:
        self.entry_point = 0
        pass
    pass
#c Memory
class Memory(object):
    #b Static properties
    res = {}
    res["hex"]        = r"([0-9a-fA-f]+)"
    res["opt_whitespace"] = r"\s*"
    res["whitespace"] = r"(\s+)"
    res["uid"]        = r"([a-zA-Z_][a-zA-Z_0-9]*)"
    res["any"]        = r"(.*)"
    obj_res = {}
    obj_res["label_match"]          = re.compile(r"%s%s%s<%s>:"%(res["opt_whitespace"], res["hex"], res["whitespace"], res["uid"]))
    obj_res["data_match"]           = re.compile(r"%s%s:%s%s.*"%(res["opt_whitespace"], res["hex"], res["whitespace"], res["hex"]))
    obj_res["data_label_match"]     = re.compile(r"#%s%s%s<%s>"%(res["whitespace"], res["hex"], res["whitespace"], res["uid"]))
    mif_res = {}
    mif_res["mif_label_match"]      = re.compile(r"#%s%s:%s:"%(res["whitespace"], res["hex"], res["uid"]))
    mif_res["mif_data_match"]       = re.compile(r"%s:%s%s%s"%(res["hex"], res["whitespace"], res["hex"], res["any"]))
    mif_res["mif_more_data_match"]  = re.compile(r"%s%s%s"%(res["whitespace"], res["hex"], res["any"]))
    mif_res["mif_data_label_match"] = re.compile(r"#%s%s%s<%s>"%(res["whitespace"], res["hex"], res["whitespace"], res["uid"]))

    #t Type properties
    labels : Dict[str,int]
    data : Dict[int,int]
    descriptor: Descriptor

    #f __init__
    def __init__(self, bit_width:int=32, num_words:int=0) -> None:
        self.reset()
        self.bit_width      = bit_width
        self.bytes_per_word = (bit_width+7) // 8
        self.word_mask      = (1<<self.bit_width) - 1
        self.num_words      = num_words
        pass
    #f reset - Clear labels and data
    def reset(self) -> None:
        self.labels = {}
        self.data   = {}
        self.descriptor = Descriptor()
        pass

    #f linear_address_range
    def linear_address_range(self) -> Tuple[int,int]:
        """
        Ensure the data is a linear address range with no holes
        Return first and last addresses that *have* data
        """
        addresses = list(self.data.keys())
        addresses.sort()
        if len(addresses)==0: return (0,0)
        start_address = addresses[0]
        end_address = addresses[-1]
        if len(addresses)!=end_address-start_address+1:
            raise Exception("Address space is not linear")
        return (start_address, end_address)
    #f resolve_address_range
    def resolve_address_range(self, address_range:Optional[Iterable[int]],
                              linear:bool=True,
                              starts_at_zero:bool=False,
                              as_bytes:bool=False ) -> Iterable[int]:
        if address_range is not None:
            for a in address_range: yield a # If starts_at_zero then trust the user knows what they are doing
            return
        seq : Sequence[int]
        if linear:
            (start, end) = self.linear_address_range()
            seq = range(start, end+1)
            pass
        else:
            seq = list(self.data.keys())
            seq.sort()
            pass
        first = True
        for a in seq:
            if starts_at_zero and first and (a!=0):
                raise Exception("default address range requires memory to start at address 0")
            first = False
            if as_bytes:
                for b in range(self.bytes_per_word):
                    yield a*self.bytes_per_word+b
                    pass
                pass
            else:
                yield a
                pass
            pass
        pass
    #f load_binary
    def load_binary(self, f:IO[str], byte_address:int=0) -> None:
        """
        Load data in from a binary file
        """
        while True:
            binary = f.read(self.bytes_per_word)
            if len(binary)==0: break
            word = 0
            for i in range(len(binary)): word = word + ( ord(binary[i])<<(8*i) )
            self.add_data_word(word, byte_address)
            byte_address = byte_address+self.bytes_per_word
            pass
        pass

    #f load_floppy_disk
    def load_floppy_disk(self, f:IO[str], num_tracks:int=40, sectors_per_track:int=10, byte_data_start:int=0, byte_desc_start:int=0x7000) -> None:
        """
        Create a memory image from a binary of a BBC disk for the FDC8271 model
        """
        byte_address = byte_data_start
        while True:
            binary = f.read(self.bytes_per_word)
            if len(binary)==0: break
            word = 0
            for i in range(len(binary)): word = word + ( ord(binary[i])<<(8*i) )
            self.add_data_word(word, byte_address)
            byte_address = byte_address + self.bytes_per_word
            pass
        byte_address = byte_desc_start
        for track in range(num_tracks):
            for sector in range(sectors_per_track):
                self.add_data_byte(track,  byte_address)
                self.add_data_byte(sector, byte_address+1)
                self.add_data_byte(1,      byte_address+2)
                self.add_data_byte(0,      byte_address+3)
                byte_address = byte_address+4
                pass
            pass
        pass

    #f load_legacy
    def load_legacy(self, f:IO[str], base_address:int=0) -> None:
        """
        Legacy is simply hex values, one per memory word
        Comments starting with # or // are permitted - they ignore the rest of the line
        """
        byte_address = base_address
        for line in f:
            if '#' in line or '//' in line:
                line = line.split('#')[0]
                line = line.split('//')[0]
                pass
            if len(line) == 0: continue
            vals = line.split(" ")
            for val in vals:
                val = val.strip()
                if len(val) == 0: continue
                self.add_data_word(int(val,16), byte_address)
                byte_address += self.bytes_per_word
                pass
            pass
        pass

    #f load_objdump - check bytes_per_word
    def load_objdump(self, f:IO[str], base_address:int=0, address_mask:int=0xffffffff) -> None:
        """
        A file consists of Labels, Data, or Data. Generated by objdump

        Labels - label = hex_address
            [space] hex_address space <label>:

        Data - [hex_address] <= hex_data
            [space] hex_address: space hex_data .*

        Data and label - [hex_address] <= hex_data, label = hex_label_address
            [space] hex_address: space hex_data # hex_label_address space <label>
        """
        self.reset()
        for l in f:
            label_match = self.obj_res["label_match"].match(l)
            data_match  = self.obj_res["data_match"].match(l)
            data_label_match  = self.obj_res["data_label_match"].search(l)
            if label_match:
                self.add_label(label_match.group(3), int(label_match.group(1),16), base_address, address_mask)
                pass
            if data_match:
                self.add_data_word(int(data_match.group(3),16), int(data_match.group(1),16), base_address, address_mask)
                pass
            if data_label_match:
                self.add_label(data_label_match.group(4), int(data_label_match.group(2),16), base_address, address_mask)
                pass
            pass
        pass

    #f load_mif - check bytes_per_word
    def load_mif(self, f:IO[str], base_address:int=0, address_mask:int=0xffffffff) -> None:
        """
        A simple 32-bit data format file consists of Labels, Data, or Data, with word addresses

        Labels - label = hex_address
            # space hex_address:<label>:

        Data - [hex_word_address] <= hex_data
            hex_word_address: space hex_data [more data]

        Data and label - [hex_address] <= hex_data, label = hex_label_address
            hex_word_address: space hex_data [*] # hex_label_address space <label>
        """
        self.reset()
        for l in f:
            label_match = self.mif_res["mif_label_match"].match(l)
            data_match  = self.mif_res["mif_data_match"].match(l)
            data_label_match  = self.mif_res["mif_data_label_match"].search(l)
            if label_match:
                self.add_label(label_match.group(3), int(label_match.group(1),16), base_address, address_mask)
                pass
            if data_match:
                address = self.bytes_per_word*int(data_match.group(1),16)
                self.add_data_word(int(data_match.group(3),16), address, base_address, address_mask)
                rest = data_match.group(4)
                while True:
                    more_match = self.mif_res["mif_more_data_match"].match(rest)
                    if not more_match: break
                    address = address + self.bytes_per_word
                    self.add_data_word(int(more_match.group(2),16), address, base_address, address_mask)
                    rest = more_match.group(3)
                    pass
                pass
            if data_label_match:
                self.add_label(data_label_match.group(4), int(data_label_match.group(2),16), base_address, address_mask)
                pass
            pass
        pass
    #f load_elf - check bytes_per_word
    def load_elf(self, f:IO[str], base_address:int=0, address_mask:int=0xffffffff) -> None:
        if not HAVE_ELF:
            raise Exception("elftools was not imported, so load_elf is not possible")
        self.reset()
        elf = elftools.elf.elffile.ELFFile(f)
        self.descriptor.entry_point = elf.header.e_entry
        for i in elf.iter_sections():
            #print i.name, i.header
            if i.header.sh_type=='SHT_SYMTAB':   self.load_elf_symtab_section(i, base_address, address_mask)
            if i.header.sh_type=='SHT_PROGBITS': self.load_elf_data_section(i, base_address, address_mask)
        pass
    #f load_elf_symtab_section - add labels based on symbols
    def load_elf_symtab_section(self, section:Any, base_address:int=0, address_mask:int=0xffffffff) -> None:
        for s in section.iter_symbols():
            self.add_label(s.name, s.entry.st_value)
            pass
        pass
    #f load_elf_data_section - add data using bytes
    def load_elf_data_section(self, section:Any, base_address:int=0, address_mask:int=0xffffffff) -> None:
        flags = section.header.sh_flags
        if (flags & elftools.elf.constants.SH_FLAGS.SHF_ALLOC)==0:
            print("Not loading section %s as it has not got ALLOC set in flags"%(section.name))
            return
        address = section.header.sh_addr
        size = section.data_size
        data = section.data()
        print("Load section %s of %d bytes to %08x"%(section.name,size,address))
        n = 0
        for d in data:
            self.add_data_byte(ord(d),address+n,base_address,address_mask)
            n += 1
            pass
        pass
    #f add_label - add label
    def add_label(self,label:str, address:int, base_address:int=0, address_mask:int=0xffffffff) -> None:
        address = (address-base_address) & address_mask
        self.labels[label] = address
        pass
    #f add_data_byte - add a byte of data
    def add_data_byte(self, data:int, address:int, base_address:int=0, address_mask:int=0xffffffff) -> None:
        address = (address-base_address) & address_mask
        word_address = address // self.bytes_per_word
        offset       = address % self.bytes_per_word
        data = data << (8*offset)
        if word_address in self.data:
            mask = (0xff << (8*offset)) ^ self.word_mask
            data = data | (self.data[word_address] & mask)
            pass
        self.data[word_address] = data
        pass
    #f add_data_word
    def add_data_word(self, data:int, address:int, base_address:int=0, address_mask:int=0xffffffff) -> None:
        address = (address-base_address) & address_mask
        data = data & self.word_mask
        word_address = address // self.bytes_per_word
        offset       = address % self.bytes_per_word
        if offset != 0:
            self.add_data_word((data<<(8*offset)), word_address*self.bytes_per_word, base_address=0)
            data = data >> (8*(self.bytes_per_word-offset))
            word_address = word_address + 1
            pass
        if word_address in self.data:
            data = data | self.data[word_address]
            pass
        self.data[word_address] = data
        pass
    #f get_byte
    def get_byte(self, byte_address:int, default:Optional[int]=None) -> Optional[int]:
        word_address = byte_address // self.bytes_per_word
        offset       = byte_address % self.bytes_per_word
        if word_address not in self.data: return default
        return (self.data[word_address] >> (offset*8)) & 0xff
    #f get
    def get(self, word_address:int, default:Optional[int]=None) -> Optional[int]:
        if word_address not in self.data: return default
        return self.data[word_address]
        pass
    #f get_exc
    def get_exc(self, word_address:int) -> int:
        d = self.get(word_address)
        if d is None: raise Exception("Memory does not contain word address 0x%x"%word_address)
        return d
    #f resolve_label
    def resolve_label(self, label:str) -> int:
        if label not in self.labels:
            raise Exception("Unable to find label '%s'"%label)
        return self.labels[label]
    #f has_label
    def has_label(self, label:str) -> bool:
        return  label in self.labels
    #f package_data
    def package_data(self, max_per_base:int=1024) -> List[Tuple[int,List[int]]]:
        """
        Package data in to a list of (base, [data*])
        """
        package = []
        addresses = list(self.data.keys())
        addresses.sort()
        while len(addresses)>0:
            base = addresses[0]
            data : List[int] = []
            i = base
            while (len(addresses)>0) and (i==addresses[0]) and (len(data)<max_per_base):
                data.append(self.data[i])
                addresses.pop(0)
                i += 1
                pass
            package.append((base,data))
            pass
        return package
    #f write_hex
    def write_hex(self, f:IO[str], format:str="%x", address_range:Optional[Iterable[int]]=None) -> None:
        """
        Writes each word of the address_range as plain hex
        """
        address_range_nn = self.resolve_address_range(address_range)
        for d in address_range_nn:
            print(format%self.data[d], file=f)
            pass
        return
    #f write_intel_hex
    def write_intel_hex(self, f:IO[str], byte_address_range:Optional[Iterable[int]]=None, bytes_per_line:int=1) -> None:
        """
        Write the address range as plain data for Intel Hex format
        Each line is then :<num bytes><address>00<data bytes><csum>
        num bytes is a 2-digit hex value of the number of data bytes in the line
        address is a 4-digit hex value of the byte address of the first byte
        data bytes are 2-digit hex values of the data for the line
        csum is 2-digit hex value of the LSB of the twos complement of the sum of the data bytes
        """
        byte_address_range_nn = self.resolve_address_range(byte_address_range, linear=True, starts_at_zero=True, as_bytes=True)
        def iter_over_line(r:Iterable[int]) -> Iterable[Tuple[int,int]]:
            last_n = 0
            first = True
            for i in r:
                if first:
                    last_n = i-1
                    first = False
                    pass
                if (i-last_n) == bytes_per_line:
                    yield (last_n+1, bytes_per_line)
                    last_n = i
                    pass
                pass
            if (i-last_n) >0 :
                yield (last_n+1, i-last_n)
                pass
            pass
        for (byte_address, n) in iter_over_line(byte_address_range_nn):
            csum = 0
            text = ":%02x%04x00"%(n,byte_address)
            csum += n
            csum += (byte_address>>8)&0xff
            csum += (byte_address)&0xff
            for j in range(n):
                d = self.get_byte(byte_address=byte_address+j, default=0)
                assert d is not None # Guaranteed because default was 0
                csum = csum + d
                text = text + ("%02x"%d)
                pass
            csum = (256-csum)&0xff
            text = text + ("%02x"%csum)
            print(text, file=f)
            pass
        pass
    #f write_quartus_mif
    def write_quartus_mif(self, f:IO[str], address_range:Optional[Iterable[int]]=None) -> None:
        address_range_nn = self.resolve_address_range(address_range, linear=False)
        mem_format = "%x:%0"+str(((self.bit_width+3)//4))+"x;"
        print( "DEPTH = %d;" % self.num_words, file = f)
        print( "WIDTH = %d;" % self.bit_width, file = f)
        print( "ADDRESS_RADIX = HEX;", file = f)
        print( "DATA_RADIX = HEX;", file = f)
        print( "CONTENT", file = f)
        print( "BEGIN", file = f)
        for word_address in address_range_nn:
            opt_d = self.get(word_address)
            if word_address>self.num_words:
                print("Skipping output of address %x (and any further words) as it is beyond the end of memory for qmif")
                break
            if opt_d is None: continue
            if opt_d == 0:continue
            print( mem_format%(word_address, opt_d), file=f )
            pass
        print( "END;", file=f)
        pass
    #f write_mif
    def write_mif(self, f:IO[str]) -> None:
        labels = list(self.labels.keys())
        key = lambda a:self.labels[a]
        labels.sort(key=key)

        label_addresses_map : Dict[int,List[str]] = {}
        for l in labels:
            la = self.labels[l]
            if la not in label_addresses_map: label_addresses_map[la]=[]
            label_addresses_map[la].append(l)
            pass

        for l in labels:
            print("#%8x:%s"%(self.labels[l],l), file=f)
            pass

        addresses = list(self.data.keys())
        addresses.sort()
        for a in addresses:
            r = "%08x: "%a
            r += "%08x" % self.data[a]
            if a in label_addresses_map:
                r += " #"
                for l in label_addresses_map[a]:
                    r += " %s"%l
                    pass
                pass
            print(r, file=f)
            pass
        pass
    #f write_mem
    def write_mem(self, f:IO[str], address_range:Optional[Iterable[int]]=None) -> None:
        address_range_nn = self.resolve_address_range(address_range, linear=False)
        fmt = "%08x"
        for word_address in address_range_nn:
            r = "@%08x "%word_address
            r += fmt % self.data[word_address]
            print(r, file=f)
            pass
        pass
    #f write_c_data
    def write_c_data(self, f:IO[str], c_type:str="uint32_t", c_var:str="data", address_range:Optional[Iterable[int]]=None) -> None:
        address_range_nn = self.resolve_address_range(address_range, linear=False)
        print("static %s %s[] = {"%(c_type, c_var), file=f)
        r = ""
        for word_address in address_range_nn:
            r += " %d, 0x%08x,"%(word_address,self.data[word_address])
            if (len(r)>50):
                print(r, file=f)
                r = ""
                pass
            pass
        r += " -1, -1"
        print(r, file=f)
        print("};", file=f)
        pass
    #f write_pxeboot
    def write_pxeboot(self, f:IO[bytes], address_range:Optional[Iterable[int]]=None) -> None:
        address_range_nn = self.resolve_address_range(address_range, linear=False)
        ranges = []
        current_range = None
        for word_address in address_range_nn:
            if current_range is None:
                current_range = (word_address,word_address)
                pass
            elif current_range[1]+1==word_address:
                current_range=(current_range[0],word_address)
                pass
            else:
                ranges.append(current_range)
                current_range = (word_address,word_address)
                pass
            pass
        if current_range is not None:
            ranges.append(current_range)
            pass
        for (start,end) in ranges:
            byte_length  = (end-start+1)*self.bytes_per_word
            byte_address = start*self.bytes_per_word

            byte_offset  = byte_address & 3
            byte_address = byte_address - byte_offset
            byte_length  = byte_length + byte_offset
            assert (byte_address // 4)==0 # as otherwise pxeboot loader cannot cope
            while byte_length>0:
                block_length = byte_length
                if byte_length>256:
                    block_length = 256
                    pass
                write_u16(f,1)
                write_u16(f,block_length)
                write_u32(f,byte_address)
                for d in range(block_length // 4):
                    value = 0
                    for i in range(4):
                        data = self.get_byte(byte_address+i, default=0)
                        assert data is not None # Guaranteed because default was 0
                        value += data << (8*i)
                        pass
                    write_u32(f,value)
                    pass
                byte_address += block_length
                byte_length -= block_length
                pass
            pass
        write_u16(f,2)
        write_u16(f,0)
        write_u32(f,self.descriptor.entry_point)
        pass
    #f All done
    pass
