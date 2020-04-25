#!/usr/bin/env python
import sys, copy

#a Parameter and module classes
#c parameter
class parameter:
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
        return parameter_instance(self, value)
    def verilog_string(self, value):
        if type(value)==str: return '"%s"'%value
        return str(value)

#c parameter_instance
class parameter_instance:
    def __init__(self, parameter, value):
        self.parameter = parameter
        self.value = value
        pass
    def verilog_string(self, comma=","):
        return ".%s(%s)%s // %s"%(self.parameter.name, self.parameter.verilog_string(self.value), comma, self.parameter.description)

#c module
def comma_if_not_last(i,n):
    if i>=n-1: return ""
    return ","
class module:
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
        for (sn, sv) in self.default_signals.iteritems():
            self.signal_assignments[sn] = sv
            pass
        for (sn, sv) in signals.iteritems():
            self.signal_assignments[sn] = sv
            pass
        for sn in self.signal_assignments:
            if sn not in self.signal_names:
                raise Exception("Unexpected signal %s"%sn)
            pass
        self.attributes = {}
        for (an, av) in self.default_attributes.iteritems():
            self.attributes[an] = av
            pass
        for (an, av) in attributes.iteritems():
            self.attributes[an] = av
            pass
        pass
    #f output_verilog
    def output_verilog(self, f, include_clk_enables=True):
        module_start = "module %s ( "%(self.name)
        indent = " "*len(module_start)
        i = module_start
        for c in self.clocks:
            print >>f, "%sinput          %s,"%(i,c)
            i = indent
            if include_clk_enables:
                print >>f, "%sinput          %s__enable,"%(i,c)
                pass
            pass
        for (s,w) in self.input_ports.iteritems():
            bw = "[%2d:0] "%(w-1)
            if w==0: bw = " "*7
            print >>f, "%sinput  %s %s,"%(i,bw,s)
            i = indent
            pass
        for (s,w) in self.output_ports.iteritems():
            bw = "[%2d:0] "%(w-1)
            if w==0: bw = " "*7
            print >>f, "%soutput %s %s,"%(i,bw,s)
            i = indent
            pass
        print >>f, ");"
        indent = "    "
        for (p,v) in self.parameter_ports.iteritems():
            if type(v)==str:
                print >>f, "%sparameter %s=\"%s\";"%(indent,p,v)
                pass
            else:
                print >>f, "%sparameter %s=%s;"%(indent,p,v)
                pass
            pass
        for (s,(w,e)) in self.wires.iteritems():
            if type(w) == tuple:
                bw = "[%2d:0] "%(w[1]-1)
                print >>f, "%swire %s %s[%d:0];"%(indent,bw,s,w[0]-1)
                pass
            else:
                bw = "[%2d:0] "%(w-1)
                if w==0: bw = " "*7
                if e is None:
                    print >>f, "%swire %s %s;"%(indent,bw,s)
                    pass
                else:
                    print >>f, "%swire %s %s = %s;"%(indent,bw,s,e)
                    pass
                pass
            pass
        for (a,e) in self.assignments.iteritems():
            print >>f, "%sassign %s = %s;"%(indent,a,e)
            pass
        for i in self.submodules:
            i.output_instance_verilog(f, indent)
            pass
        print >>f, "endmodule"
        pass
    #f output_instance_verilog
    def output_instance_verilog(self, f, indent="    "):
        n = len(self.attributes)
        if n>0:
            print >>f, "%s(* "%(indent),
            i=0
            for (an, av) in self.attributes.iteritems():
                print >>f, '%s = "%s"%s '%(an,av,comma_if_not_last(i,n)),
                i += 1
                pass
            print >>f, " *)"
            pass
        print >>f, "%s%s"%(indent, self.name),
        
        n = len(self.parameter_values)
        if n>0:
            print >>f, " #("
            i=0
            for pv in self.parameter_values:
                print >>f, "%s%s%s"%(indent, indent, pv.verilog_string(comma_if_not_last(i,n)))
                i += 1
                pass
            print >>f, "%s) %s ("%(indent, self.instance_name)
            pass
        else:
            print >>f, " %s ("%(self.instance_name)
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
                print >>f, "%s%s.%s (%s)%s"%(indent, indent, sn, sv, comma_if_not_last(i,n) )
                i += 1
                pass
            pass
        print >>f, "%s);"%(indent)
        pass
    #f All done

#a Xilinx primitives
#c mmcme3_base
class mmcme3_base(module):
    name ="MMCME3_BASE"
    parameters = [
        parameter("BANDWIDTH",           ["OPTIMIZED","LOW","HIGH"], "Jitter programming"),
        parameter("STARTUP_WAIT",        ["FALSE", "TRUE"], "Delays DONE until MMCM is locked"),
        parameter("CLKIN1_PERIOD",       10.,     "Input clock period in ns units, ps resolution (i.e. 33.333 is 30 MHz)."),
        parameter("IS_CLKIN1_INVERTED",  [0,1],   "Optional inversion for CLKIN1"),
        parameter("REF_JITTER",          0.,      "Reference input jitter in UI (0.000-0.999)."),
        parameter("DIVCLK_DIVIDE",       (1,106), "Master division value"),
        parameter("CLKFBOUT_MULT_F",     (2,64),  "Multiply value for VCO"), # possibly a float?
        parameter("CLKFBOUT_PHASE",      0.,      "Phase offset in degrees of CLKFB"),
        parameter("CLKOUT0_DIVIDE_F",    (1,128), "Divide amount for CLKOUT0"), # possibly a float?
        parameter("CLKOUT0_DUTY_CYCLE",  0.5,     "Duty cycle"),
        parameter("CLKOUT1_DIVIDE",      (1,128), "Divide amount for CLKOUT1"),
        parameter("CLKOUT2_DIVIDE",      (1,128), "Divide amount for CLKOUT21"),
        parameter("CLKOUT3_DIVIDE",      (1,128), "Divide amount for CLKOUT3"),
        parameter("CLKOUT4_DIVIDE",      (1,128), "Divide amount for CLKOUT4"),
        parameter("CLKOUT5_DIVIDE",      (1,128), "Divide amount for CLKOUT5"),
        parameter("CLKOUT6_DIVIDE",      (1,128), "Divide amount for CLKOUT6"),
        parameter("IS_CLKFBIN_INVERTED", [0,1],   "Optional inversion for CLKFBIN"),
        parameter("IS_PWRDWN_INVERTED",  [0,1],   "Optional inversion for PWRDWN"),
        parameter("IS_RST_INVERTED",     [0,1],   "Optional inversion for RST"),
        ]
    signals = [("RST", None),
               ("PWRDWN", 0),
               ("CLKOUT0", None),
               ("CLKOUT1", None),
               ("CLKOUT2", None),
               ("CLKOUT3", None),
               ("CLKOUT4", None),
               ("CLKOUT5", None),
               ("CLKOUT6", None),
               ("LOCKED", None),
               ("CLKIN1", None),
               ("CLKFBOUT", None),
               ("CLKFBIN", None),
               ]

#c Xdelaye3
class Xdelaye3(module):
    """
    A delay module for an input or output signal (or cascaded from an other idelay/odelay)
    Must be subclassed to idelaye3 or odelaye3
    """
    name = None
    parameters = [
        parameter("DELAY_TYPE",        ["FIXED", "VAR_LOAD", "VARIABLE"], "Delay to use - if variable then CE, LOAD and INC are used"),
        parameter("DELAY_VALUE",       (0,1250), "Delay if fixed (in psec if DELAY_FORMAT is TIME else taps). Up to 512 if taps."),
        parameter("DELAY_FORMAT",      ["TIME", "COUNT"], "If TIME then REFCLK_FREQUENCY is used to determine initial taps; if COUNT then DELAY_VALUE is in taps"),
        parameter("REFCLK_FREQUENCY",  (200., 800.), "Reference clock frequency if DELAY_FORMAT is TIME - else unused"),
        parameter("UPDATE_MODE",       ["ASYNC", "SYNC", "MANUAL"], "ASYNC is preferred - MANUAL requires two toggles of load (one to capture the value, one to make it happen)"),
        parameter("CASCADE",           ["NONE", "MASTER", "SLAVE_MIDDLE", "SLAVE_END"], "Cascading - and where in the chain it is"),
        ]
    signals = [("RST", None), # Deassert synchronously to CLK
               ("CLK", None),
               ("DATAOUT", None), # Output of delay - connect to previous ODELAYE3/IDELAYE3 if CASCADE is SLAVE_MIDDLE or SLAVE_END
               ("CE",   0),  # If asserted high then INC/DEC will be performed
               ("INC",  0),  # If CE high then INC not DEC - if CE is low then LOAD may be performed
               ("LOAD", 0),  # Exclusive with CE - enables a LOAD of the taps (if UPDATE_MODE is ASYNC then immediately; if MANUAL then every other LOAD)
               ("CNTVALUEIN", 0), # 9-bit delay value in
               ("CNTVALUEOUT", None), # 9-bit delay value out - invalid if EN_VTC is high
               ("EN_VTC", 0),         # Enable for automatic voltage-temperature compensation. Use with magic.
               ("CASC_IN",     None), # Connect to previous ODELAYE3/IDELAYE3 CASC_OUT if CASCADE is SLAVE_MIDDLE or SLAVE_END
               ("CASC_OUT",    None), # Connect to next     ODELAYE3/IDELAYE3 CASC_IN  if CASCADE is MASTER or SLAVE_MIDDLE
               ("CASC_RETURN", None), # Connect to next     ODELAYE3/IDELAYE3 DATAOUT  if CASCADE is MASTER or SLAVE_MIDDLE
               ]

#c idelaye3
class idelaye3(Xdelaye3):
    """
    A delay module for an input signal (or cascaded from an odelay)
    """
    name ="IDELAYE3"
    parameters = copy.copy(Xdelaye3.parameters)
    signals    = copy.copy(Xdelaye3.signals)
    parameters += [
        parameter("DELAY_SRC",         ["IDATAIN", "DATAIN"], "Source of data - IOB or internal signal"),
        ]
    signals += [ ("DATAIN", 0),
                 ("IDATAIN", 0),    # Tie to IOB input pin or 0
                 ]

#c odelaye3
class odelaye3(Xdelaye3):
    """
    A delay module for an output signal (or cascaded from an idelay)
    """
    name ="ODELAYE3"
    signals    = copy.copy(Xdelaye3.signals)
    signals += [ ("ODATAIN", 0),
                 ]

#c oserdese3
class oserdese3(module):
    """
    A serializer module with two pseudo-synchronous clocks
    CLKDIV is CLK divided by (DATA_WIDTH/2)
    Basically it runs in DDR mode (output changes on every edge of CLK)
    To use in SDR mode, replicate data in
    """
    name ="OSERDESE3"
    parameters = [
        parameter("DATA_WIDTH",         [4, 8], "Width of parallel data"),
        parameter("INIT",               [0, 1], "Reset value of serial output"),
        parameter("IS_CLKDIV_INVERTED", [0, 1], "Optional inversion for CLKDIV"),
        parameter("IS_CLK_INVERTED",    [0, 1], "Optional inversion for CLK"),
        parameter("IS_RST_INVERTED",    [0, 1], "Optional inversion for RST"),
        ]
    signals = [("RST", None), # Deassert synchronously to ?
               ("CLK", None),
               ("CLKDIV", None),
               ("D",   0), # Always 8-bits, in width 4 top 4 bits ignored
               ("T",   0), # Tristate input
               ("T_OUT", None), # Tristate output to IOB (assert high to tristate)
               ("OQ",  0),
               ]

#c iserdese3
class iserdese3(module):
    """
    A deserializer module with two pseudo-synchronous clocks
    CLKDIV is CLK divided by (DATA_WIDTH/2)
    Basically it runs in DDR mode (input captured on every edge of CLK)
    To use in SDR mode, use alternate data output bits.
    In FIFO mode 
    """
    name ="ISERDESE3"
    parameters = [
        parameter("DATA_WIDTH",         [4, 8], "Width of parallel data"),
        parameter("FIFO_ENABLE",        ["FALSE", "TRUE"], "FIFO enable option - if true tie FIFO_RD_EN to !FIFO_EMPTY and FIFO_RD_CLK to CLKDIV"),
        # parameter("FIFO_SYNC_MODE",   ["FALSE", "TRUE"], "True is reserved"),
        parameter("IS_CLKDIV_INVERTED", [0, 1], "Optional inversion for CLKDIV"),
        parameter("IS_CLK_INVERTED",    [0, 1], "Optional inversion for CLK"),
        parameter("IS_CLK_B_INVERTED",  [0, 1], "Optional inversion for CLK_B"),
        parameter("IS_RST_INVERTED",    [0, 1], "Optional inversion for RST"),
        ]
    signals = [("RST", None), # Deassert synchronously to ? CLK
               ("CLK", None),
               ("CLK_B", None),
               ("CLKDIV", None),
               ("D", 0),
               ("Q", 0), # Always 8-bits, in width 4 top 4 bits ignored
               ("FIFO_RD_CLK",  0),
               ("FIFO_RD_EN",  0),
               ("FIFO_EMPTY",  None),
               ]

#c obufds
class obufds(module):
    """
    Differential output buffer
    """
    name ="OBUFDS"
    parameters = [
        ]
    signals = [("I",  None),
               ("O",  None),
               ("OB", None),
               ]

#c ibufds
class ibufds(module):
    """
    Differential input buffer with single-ended output
    """
    name ="IBUFDS"
    parameters = [
        ]
    signals = [("I",  None),
               ("IB",  None),
               ("O",  None),
               ]

#c ibufds_diff_out
class ibufds_diff_out(module):
    """
    Differential input buffer, with +ve and -ve outputs (which should be balanced in timing)
    """
    name ="IBUFDS_DIFF_OUT"
    parameters = [
        ]
    signals = [("I",  None),
               ("IB",  None),
               ("O",  None),
               ("OB", None),
               ]

#c fdpe
class fdpe(module):
    """
    Flop with asynchronous preset

    Normally used with attributes of:
      shreg_extract = "no"
      ASYNC_REG = "TRUE"
    """
    name ="FDPE"
    parameters = [
        parameter("INIT",               [1, 0], "Reset value of serial output"),
        parameter("IS_C_INVERTED",      [0, 1], "Optional inversion for C"),
        # parameter("IS_D_INVERTED",    [0, 1], "Optional inversion for D - only valid in IOB registers"),
        parameter("IS_PRE_INVERTED",    [0, 1], "Optional inversion for PRE"),
        ]
    signals = [("PRE", None),
               ("C",   None),
               ("CE",  None),
               ("D",   0),
               ("Q",   None),
               ]

#c ramb36e2
class ramb36e2(module):
    """
    These can run in 'true dual port mode' with two read-write ports of width up to 36.
    They can also run in 'simple dual port mode' with a single read port of up to 72 and a single write port of up to 72.

    Hence they can be used as an x64 memory with single read/write port.

    For simple single port memories:
    They can be seen as a 512x64 memory (9 address bits)
    They can be seen as a 1kx32  memory (10 address bits)
    They can be seen as a 2kx16  memory (11 address bits)
    They can be seen as a 4kx8   memory (12 address bits)
    """
    name ="RAMB36E2"
    parameters = [
        parameter("CASCADE_ORDER_A",           ["NONE", "FIRST", "MIDDLE", "LAST"], "Order of cascade - first is bottom"),
        parameter("CASCADE_ORDER_B",           ["NONE", "FIRST", "MIDDLE", "LAST"], "Order of cascade - first is bottom"),
        parameter("CLOCK_DOMAINS",        ["INDEPENDENT", "COMMON"], "Whether A and B are the same clock"),

        parameter("DOA_REG",             [1,0],   "Output register for port A"),
        parameter("ENADDRENA",           ["FALSE", "TRUE"],   "Address enable pin for port A"),
        parameter("RDADDRCHANGEA",       [0,1],   "Enable read address change feature port A"),
        parameter("READ_WIDTH_A",        [0,1,2,4,9,16,36,72],   "Read width for port A"),
        parameter("WRITE_WIDTH_A",       [0,1,2,4,9,16,36,72],   "Write width for port A"),

        parameter("DOB_REG",             [1,0],   "Output register for port B"),
        parameter("ENADDRENB",           ["FALSE", "TRUE"],   "Address enable pin for port B"),
        parameter("RDADDRCHANGEB",       [0,1],   "Enable read address change feature port B"),
        parameter("READ_WIDTH_B",        [0,1,2,4,9,16,36,72],   "Read width for port B"),
        parameter("WRITE_WIDTH_B",       [0,1,2,4,9,16,36,72],   "Write width for port B"),

        parameter("EN_ECC_PIPE",         ("FALSE","TRUE"),   "Enable ECC pipeline stage"),
        parameter("EN_ECC_READ",         ("FALSE","TRUE"),   "Enable ECC for reads - read width must be 72"),
        parameter("EN_ECC_WRITE",        ("FALSE","TRUE"),   "Enable ECC for writes - write width must be 72"),

        parameter("IS_CLKARDCLK_INVERTED",  [0,1],   "Optional inversion for read clock for port A"),
        parameter("IS_ENARDEN_INVERTED",    [0,1],   "Optional inversion for enarden for port A"),
        parameter("IS_ENBWREN_INVERTED",    [0,1],   "Optional inversion for enbwren for port A"),
        parameter("IS_RSTRAMARSTRAM_INVERTED",    [0,1],   "Optional inversion for rstramarstram for port A"),
        parameter("IS_RSTREGARSTREG_INVERTED",    [0,1],   "Optional inversion for rstregarstreg for port A"),
        parameter("IS_RSTRAMB_INVERTED",    [0,1],   "Optional inversion for rstramb for port B"),
        parameter("IS_RSTREGB_INVERTED",    [0,1],   "Optional inversion for rstregb for port A"),
        parameter("IS_CLKBWRCLK_INVERTED",  [0,1],   "Optional inversion for write clock for port B"),

        parameter("SLEEP_ASYNC",  [0,1],   "Is sleep async to clkardclk"),
        ]
    signals = [("SLEEP", 0),
               ("RSTRAMARSTRAM", 0),    # reset
               ("RSTREGARSTREG", None), # reset

               ("RSTRAMB", 0),          # reset
               ("RSTREGB", None),       # reset
               
               ("CLKARDCLK", None),     # Clock for reading or for port A
               ("ADDRARDADDR", None),   # Read address or address for port A (15 bits if 32kx1)
               ("ADDRENA", None),       # Address enable for port A if configured
               ("REGCEAREGCE", None),   # only if DOA REG is 1
               ("DINADIN", None),       # 32 bit data in for writing or for port A
               ("DINPADINP", None),     # 4 bit parity data in for writing or for port A
               ("ENARDEN", None),       # Read enable or enable for port A
               ("WEA", None),           # Four byte-write enables for port A
               ("DOUTADOUT", None),     # 32-bit data out for port A or read data
               ("DOUTPADOUTP", None),   # 4-bit data out for port A or read
               
               ("CLKBWRCLK", None),     # Clock for writing or for port B
               ("ADDRBWRADDR", None),   # Write address port B (15 bits if 32kx1)
               ("ADDRENB", None),       # Address enable for port B if configured
               ("REGCEB", None),        # only if DOB REG is 1
               ("DINBDIN", None),       # 32 bit data in for writing or for port B
               ("DINPBDINP", None),     # 4 bit parity data in for writing or for port B
               ("ENBWREN", None),       # Write enable or enable for port B
               ("WEBWE", None),         # Four byte-write enables for port B or 8 byte-write enables for write port
               ("DOUTBDOUT", None),     # 32-bit data out for port B or read data
               ("DOUTPBDOUTP", None),   # 4-bit data out for port B or read

               ("ECCPIPECE", None),     # Enable for ECC pipe
               ("INJECTDBITERR", None), # Inject data bit errror
               ("INJECTSBITERR", None), # Inject syndrome bit error
               ("DBITERR", None),       # ECC double bit error
               ("SBITERR", None),       # ECC single bit error
               ("ECCPARITY", None),     # 8-bits
               ("RDADDRECC", None),     # 9-bits

               ("CASDIMUXA", None),        # Cascade port A (use CASDINA when high)
               ("CASDINA", None),          # Cascade port A data 32
               ("CASDINPA", None),         # Cascade port A parity 4
               ("CASDOMUXA", None),        # Cascade port A (use CASDINA when high)
               ("CASDOMUXEN_A", None),     # Cascade port A unregistered output data register enable
               ("CASDOREGIMUXA", None),    # Cascade port A
               ("CASDOREGIMUXEN_A", None), # Cascade port A
               ("CASDOUTA", None),         # Cascade port A data 32
               ("CASDOUTPA", None),        # Cascade port A parity 4

               ("CASDIMUXB", None),        # Cascade port B (use CASDINB when high)
               ("CASDINB", None),          # Cascade port B data 32
               ("CASDINPB", None),         # Cascade port B parity 4
               ("CASDOMUXB", None),        # Cascade port B (use CASDINB when high)
               ("CASDOMUXEN_B", None),     # Cascade port B unregistered output data register enable
               ("CASDOREGIMUXB", None),    # Cascade port B
               ("CASDOREGIMUXEN_B", None), # Cascade port B
               ("CASDOUTB", None),         # Cascade port B data 32
               ("CASDOUTPB", None),        # Cascade port B parity 4
    ]

#a Xilinx derived modules
#c sync_reset_reg
class sync_reset_reg(fdpe):
    default_parameters={"INIT":1}
    default_attributes={"shreg_extract":"no", "ASYNC_REG":"TRUE"}
    pass

#c idelaye3_count_load - default of not cascaded
class idelaye3_count_load(idelaye3):
    default_parameters={ "DELAY_TYPE":"VAR_LOAD",
                         "DELAY_VALUE":0,
                         "DELAY_FORMAT":"COUNT",
                         "UPDATE_MODE":"ASYNC",
                         "CASCADE":"NONE",
    }
    default_signals    = {"EN_VTC":0,
                          "CE": 0,
                          "INC": 0,
                          "CASC_IN":0,
                          "CASC_RETURN":0,
    }
    
#c odelaye3_count_load - default of not cascaded
class odelaye3_count_load(odelaye3):
    default_parameters={ "DELAY_TYPE":"VAR_LOAD",
                         "DELAY_VALUE":0,
                         "DELAY_FORMAT":"COUNT",
                         "UPDATE_MODE":"ASYNC",
                         "CASCADE":"NONE",
    }
    default_signals    = {"EN_VTC":0,
                          "CE": 0,
                          "INC": 0,
                          "CASC_IN":0,
                          "CASC_RETURN":0,
    }
    
#a Toplevel
#f PLL 300 in to 225/150/100/50
p = mmcme3_base("pll_i",
                parameters={"CLKIN1_PERIOD":3.33, # 300MHz in
                            "DIVCLK_DIVIDE":1,
                            "CLKFBOUT_MULT_F":3,  # FB @ 900MHz
                            "CLKOUT0_DIVIDE_F":4, # clk0 @ 225MHz
                            "CLKOUT1_DIVIDE":6,   # clk1 @ 150MHz
                            "CLKOUT2_DIVIDE":9,   # clk2 @ 100MHz
                            "CLKOUT3_DIVIDE":18,  # clk3 @ 50MHz
                },
                signals = {"RST":"rst",
                           "PWRDWN":"0",
                           "CLKOUT0":"outclk_225",
                           "CLKOUT1":"outclk_150",
                           "CLKOUT2":"outclk_100",
                           "CLKOUT3":"outclk_50",
                           "LOCKED":"locked",
                           "CLKIN1":"refclk",
                           "CLKFBOUT":"clk_fb",
                           "CLKFBIN":"clk_fb",
                           }
                )
p.output_instance_verilog(sys.stdout)

#f PLL 125 in to 625 / 312.5 / 125 / 25
p = mmcme3_base("pll_i",
                parameters={"CLKIN1_PERIOD":8.00, # 125MHz in
                            "DIVCLK_DIVIDE":1,
                            "CLKFBOUT_MULT_F":5,  # FB @ 625MHz
                            "CLKOUT0_DIVIDE_F":1, # clk0 @ 625MHz
                            "CLKOUT1_DIVIDE":2,   # clk1 @ 312.5MHz
                            "CLKOUT2_DIVIDE":5,   # clk2 @ 125MHz
                            "CLKOUT3_DIVIDE":25,  # clk3 @ 25MHz
                },
                signals = {"RST":"rst",
                           "PWRDWN":"0",
                           "CLKOUT0":"outclk_625",
                           "CLKOUT1":"outclk_312_5",
                           "CLKOUT2":"outclk_125",
                           "CLKOUT3":"outclk_25",
                           "LOCKED":"locked",
                           "CLKIN1":"refclk",
                           "CLKFBOUT":"clk_fb",
                           "CLKFBIN":"clk_fb",
                           }
                )
p.output_instance_verilog(sys.stdout)

#f Four BSRAMs as 4kx32 (16kB) with byte write enables - by using one RAM per byte
class bram__se_sram_srw_4096x32_we8(module):
    name = "bram__se_sram_srw_4096x32_we8"
    clocks = ["sram_clock",]
    input_ports = {"select":0,
                   "read_not_write":0,
                   "write_enable":4, # byte enables
                   "address":12,
                   "write_data":32,
    }
    output_ports = {"data_out":32,
    }
    parameter_ports = {"initfile":"", "address_width":12, "data_width":32}
    assignments = {"data_out[ 7: 0]":"read_data_mem[0][7:0]",
                   "data_out[15: 8]":"read_data_mem[1][7:0]",
                   "data_out[23:16]":"read_data_mem[2][7:0]",
                   "data_out[31:24]":"read_data_mem[3][7:0]",
    }
    wires = {"read_data_mem":((4,32),None)}
    submodules = [
        ramb36e2("ram_%d"%byte,
                 parameters={"DOA_REG":0,
                             "DOB_REG":0,
                             "READ_WIDTH_A":9,
                             "WRITE_WIDTH_A":9,
                             "ENADDRENA":"FALSE",
                         },
                signals = {"CLKARDCLK":"sram_clock",
                           "ENARDEN":"sram_clock__enable && select",
                           "ADDRARDADDR":"{address[11:0],3'b0}",
                           "WEA":"{3'b0,write_enable[%d] && !read_not_write}"%byte,
                           "DINADIN":"{24'b0,write_data[%d:%d]}"%((byte*8+7),(byte*8)),
                           "DOUTADOUT":"read_data_mem[%d]"%byte,
                           "CLKBWRCLK":"0",                           
                           "WEBWE":"0",
                       },
                 attributes = {"ram_addr_begin":0,
                               "ram_addr_end":4095,
                               "ram_slice_begin":byte*8,
                               "ram_slice_end":7+byte*8,
                           },
             ) for byte in range(4)]
    pass
print "*"*80
bram__se_sram_srw_4096x32_we8("").output_verilog(sys.stdout)

#f Sixteen BSRAMs as 16kx32 (64kB) with byte write enables - by using one RAM per byte
class bram__se_sram_srw_16384x32_we8(module):
    """
WARNING: [DRC REQP-1902] RAMB36E2_AB_cascade_out_must_use_parity: The RAMB36E2 cell dut/riscv/mem/ram_1_0 has CASCADE_ORDER_A attribute set to MIDDLE with the CASDOUTA[31:0] bus used, but is missing appropriate connection(s) for the CASDOUTPA[3:0] bus.
WARNING: [DRC REQP-1902] RAMB36E2_AB_cascade_out_must_use_parity: The RAMB36E2 cell dut/riscv/mem/ram_1_1 has CASCADE_ORDER_A attribute set to MIDDLE with the CASDOUTA[31:0] bus used, but is missing appropriate connection(s) for the CASDOUTPA[3:0] bus.
WARNING: [DRC REQP-1902] RAMB36E2_AB_cascade_out_must_use_parity: The RAMB36E2 cell dut/riscv/mem/ram_1_2 has CASCADE_ORDER_A attribute set to MIDDLE with the CASDOUTA[31:0] bus used, but is missing appropriate connection(s) for the CASDOUTPA[3:0] bus.
WARNING: [DRC REQP-1902] RAMB36E2_AB_cascade_out_must_use_parity: The RAMB36E2 cell dut/riscv/mem/ram_1_3 has CASCADE_ORDER_A attribute set to MIDDLE with the CASDOUTA[31:0] bus used, but is missing appropriate connection(s) for the CASDOUTPA[3:0] bus.
WARNING: [DRC REQP-1902] RAMB36E2_AB_cascade_out_must_use_parity: The RAMB36E2 cell dut/riscv/mem/ram_2_0 has CASCADE_ORDER_A attribute set to MIDDLE with the CASDOUTA[31:0] bus used, but is missing appropriate connection(s) for the CASDOUTPA[3:0] bus.
WARNING: [DRC REQP-1902] RAMB36E2_AB_cascade_out_must_use_parity: The RAMB36E2 cell dut/riscv/mem/ram_2_1 has CASCADE_ORDER_A attribute set to MIDDLE with the CASDOUTA[31:0] bus used, but is missing appropriate connection(s) for the CASDOUTPA[3:0] bus.
WARNING: [DRC REQP-1902] RAMB36E2_AB_cascade_out_must_use_parity: The RAMB36E2 cell dut/riscv/mem/ram_2_2 has CASCADE_ORDER_A attribute set to MIDDLE with the CASDOUTA[31:0] bus used, but is missing appropriate connection(s) for the CASDOUTPA[3:0] bus.
WARNING: [DRC REQP-1902] RAMB36E2_AB_cascade_out_must_use_parity: The RAMB36E2 cell dut/riscv/mem/ram_2_3 has CASCADE_ORDER_A attribute set to MIDDLE with the CASDOUTA[31:0] bus used, but is missing appropriate connection(s) for the CASDOUTPA[3:0] bus.
WARNING: [DRC REQP-1902] RAMB36E2_AB_cascade_out_must_use_parity: The RAMB36E2 cell dut/riscv/mem/ram_3_0 has CASCADE_ORDER_A attribute set to FIRST with the CASDOUTA[31:0] bus used, but is missing appropriate connection(s) for the CASDOUTPA[3:0] bus.
WARNING: [DRC REQP-1902] RAMB36E2_AB_cascade_out_must_use_parity: The RAMB36E2 cell dut/riscv/mem/ram_3_1 has CASCADE_ORDER_A attribute set to FIRST with the CASDOUTA[31:0] bus used, but is missing appropriate connection(s) for the CASDOUTPA[3:0] bus.
WARNING: [DRC REQP-1902] RAMB36E2_AB_cascade_out_must_use_parity: The RAMB36E2 cell dut/riscv/mem/ram_3_2 has CASCADE_ORDER_A attribute set to FIRST with the CASDOUTA[31:0] bus used, but is missing appropriate connection(s) for the CASDOUTPA[3:0] bus.
WARNING: [DRC REQP-1902] RAMB36E2_AB_cascade_out_must_use_parity: The RAMB36E2 cell dut/riscv/mem/ram_3_3 has CASCADE_ORDER_A attribute set to FIRST with the CASDOUTA[31:0] bus used, but is missing appropriate connection(s) for the CASDOUTPA[3:0] bus.
    """
    name = "bram__se_sram_srw_16384x32_we8"
    clocks = ["sram_clock",]
    input_ports = {"select":0,
                   "read_not_write":0,
                   "write_enable":4, # byte enables
                   "address":14,
                   "write_data":32,
    }
    output_ports = {"data_out":32,
    }
    parameter_ports = {"initfile":"", "address_width":14, "data_width":32}
    wires = {"read_data_mem":((16,32),None),
             "casc_data_out":((20,32),None),
             "casc_data_out_p":((20,4),None),
             "word_sel":(4,None),
    }
    assignments = {"data_out[ 7: 0]":"read_data_mem[0][7:0]",
                   "data_out[15: 8]":"read_data_mem[1][7:0]",
                   "data_out[23:16]":"read_data_mem[2][7:0]",
                   "data_out[31:24]":"read_data_mem[3][7:0]",
                   "word_sel[0]":"(address[13:12]==0) && select",
                   "word_sel[1]":"(address[13:12]==1) && select",
                   "word_sel[2]":"(address[13:12]==2) && select",
                   "word_sel[3]":"(address[13:12]==3) && select",
                   "casc_data_out[16]":"0",
                   "casc_data_out[17]":"0",
                   "casc_data_out[18]":"0",
                   "casc_data_out[19]":"0",
                   "casc_data_out_p[16]":"0",
                   "casc_data_out_p[17]":"0",
                   "casc_data_out_p[18]":"0",
                   "casc_data_out_p[19]":"0",
    }
    submodules = []
    for word in range(4):
        for byte in range(4):
            ram_id = "_%d_%d"%(word,byte)
            ram_n = byte + word*4
            next_ram_n = byte + (word+1)*4
            p = ramb36e2("ram%s"%ram_id,
                        parameters={"DOA_REG":0,
                                    "DOB_REG":0,
                                    "READ_WIDTH_A":9,
                                    "WRITE_WIDTH_A":9,
                                    "ENADDRENA":"FALSE",
                                    "CASCADE_ORDER_A":["LAST", "MIDDLE", "MIDDLE", "FIRST"][word],
                        },
                        signals = {"CLKARDCLK":"sram_clock",
                                   "ENARDEN":"sram_clock__enable && word_sel[%d]"%(word),
                                   "ADDRARDADDR":"{address[11:0],3'b0}",
                                   "WEA":"{3'b0,write_enable[%d] && !read_not_write && word_sel[%d]}"%(byte,word),
                                   "DINADIN":"{24'b0,write_data[%d:%d]}"%((byte*8+7),(byte*8)),
                                   "DOUTADOUT":"read_data_mem[%d]"%ram_n,
                                   "CLKBWRCLK":"0",                           
                                   "WEBWE":"0",
                                   "CASDINA"    :"casc_data_out[%d]"%next_ram_n,
                                   "CASDINPA"   :"casc_data_out_p[%d]"%next_ram_n,
                                   "CASDIMUXA"  :"0", # Always use DIN
                                   "CASDOUTA"   :"casc_data_out[%d]"%ram_n,
                                   "CASDOUTPA"  :"casc_data_out_p[%d]"%ram_n,
                                   "CASDOMUXA"  :"!word_sel[%d]"%word,
                                   "CASDOMUXEN_A":"sram_clock__enable",
                                   },
                         attributes = {"ram_addr_begin" :word*4096 + 0,
                                       "ram_addr_end"   :word*4096 + 4095,
                                       "ram_slice_begin":byte*8,
                                       "ram_slice_end"  :byte*8+7,
                         },
            )
            submodules.append(p)
            pass
        pass
    pass

print "*"*80
bram__se_sram_srw_16384x32_we8("").output_verilog(sys.stdout)

#f Output differential DDR serializer of 4 bits (CLK runs at 2x CLK_DIV2)
class diff_ddr_serializer4(module):
    name = "diff_ddr_serializer4"
    clocks = ["clk", "clk_div2"]
    input_ports = {"reset_n":0, "data":4}
    output_ports = {"pin__p":0, "pin__n":0}
    wires = {"reset":(0,"!reset_n")}
    submodules = [
    sync_reset_reg("reset_sync_0", signals={"PRE":"reset", "C":"clk_div2", "CE":"1", "D":"reset",    "Q":"reset__0"} ),
    sync_reset_reg("reset_sync_1", signals={"PRE":"reset", "C":"clk_div2", "CE":"1", "D":"reset__0", "Q":"reset__1"} ),
    sync_reset_reg("reset_sync_2", signals={"PRE":"reset", "C":"clk_div2", "CE":"1", "D":"reset__1", "Q":"reset__2"} ),
    sync_reset_reg("reset_sync_3", signals={"PRE":"0",     "C":"clk_div2", "CE":"1", "D":"reset__2", "Q":"reset__sync_clk_div2"} ),
    oserdese3("serializer",
              parameters={"DATA_WIDTH":4,
              },
              signals = {"RST":"reset__sync_clk_div2",
                         "CLK":"clk",
                         "CLKDIV":"clk_div2",
                         "D":"{4'b0, data}",
                         "OQ":"serial_data",
              },
    ),
    obufds("diff_io",
               signals = {"I":"serial_data",
                          "O":"pin__p",
                          "OB":"pin__n",
               },
    ),
    ]
print "*"*80
diff_ddr_serializer4("").output_verilog(sys.stdout)

#f Input differential DDR deserializer, with configurable delay, of 4 bits (CLK runs at 2x CLK_DIV2)
# To enable phase tracking of data in with respect to CLK this has two delay modules
# The first should be used for the data - its delay value is handled with data_delay__load/value
# The second should use data_delay + half a clock edge - this is tracker
# If 'data_delay' is *slightly* too small then tracker will have *ALL* the same edges as data
# If 'data_delay' is *slightly* too large then tracker will have *ALL* the same edges as data delayed by a bit
# If 'data_delay' is just right then it will be capturing the changing phase of the data bits, and so equal number of edges will be delayed as not
# in theory
diff_ddr_deserializer4  = [
    sync_reset_reg("reset_sync_0", signals={"PRE":"reset", "C":"clk_div2", "CE":"1", "D":"reset",    "Q":"reset__0"} ),
    sync_reset_reg("reset_sync_1", signals={"PRE":"reset", "C":"clk_div2", "CE":"1", "D":"reset__0", "Q":"reset__1"} ),
    sync_reset_reg("reset_sync_2", signals={"PRE":"reset", "C":"clk_div2", "CE":"1", "D":"reset__1", "Q":"reset__2"} ),
    sync_reset_reg("reset_sync_3", signals={"PRE":"0",     "C":"clk_div2", "CE":"1", "D":"reset__2", "Q":"reset__sync_clk_div2"} ),
    ibufds_diff_out("diff_io",
               signals = {"I":"pin__p",
                          "IB":"pin__n",
                          "O":"data__p",
                          "OB":"data__n",
               },
    ),
    idelaye3_count_load("data_delay",
              parameters={"DELAY_SRC":"IDATAIN",
              },
              signals = {"RST":"reset__sync_clk_div2",
                         "CLK":"clk_div2", # Update clock
                         "IDATAIN":"data__p",
                         "LOAD":      "data_delay__load",
                         "CNTVALUEIN":"data_delay__value",
                         "DATAOUT":   "data_delayed",
              },
    ),
    iserdese3("data_deserializer",
              parameters={"DATA_WIDTH":4,
                          "FIFO_ENABLE":"FALSE",
              },
              signals = {"RST":"reset__sync_clk_div2",
                         "CLK":"clk",
                         "CLK_B":"~clk",
                         "CLKDIV":"clk_div2",
                         "D":"data_delayed",
                         "Q":"data_out", # 8 bits, only use bottom 4 bits
              },
    ),
    idelaye3_count_load("tracker_delay",
              parameters={"DELAY_SRC":"IDATAIN",
              },
              signals = {"RST":"reset__sync_clk_div2",
                         "CLK":"clk_div2", # Update clock
                         "IDATAIN":"data__n",
                         "LOAD":      "tracker_delay__load",
                         "CNTVALUEIN":"tracker_delay__value",
                         "DATAOUT":   "tracker_delayed",
              },
    ),
    iserdese3("tracker_deserializer",
              parameters={"DATA_WIDTH":4,
                          "FIFO_ENABLE":"FALSE",
              },
              signals = {"RST":"reset__sync_clk_div2",
                         "CLK":"clk",
                         "CLK_B":"~clk",
                         "CLKDIV":"clk_div2",
                         "D":"tracker_delayed",
                         "Q":"tracker_out", # 8 bits, only use bottom 4 bits
              },
    ),
]
for m in diff_ddr_deserializer4:
    m.output_instance_verilog(sys.stdout)
    pass

#f Cascaded delay pair
# Pair of delays for an internal signal
# This provides on an Ultrascale device for a delay of up to 1024 taps or 2.5ns
# If you have a 600MHz clock that is 800ps low, 800ps high
# Register the output of this delay pair on a lower speed clock
# To measure the clock low time one can find the lowest delay value that captures steady 0
# then increase the delay value until it captures a steady 1
# More simply use two FSMs - the higher level one being:
#  state idle : -> find_initial_stable_value on request, starting with delay 0
#  state find_initial_stable_value : if shift register is all 1s or all zeros then -> record value and find_inverted_stable_value
#  state find_initial_stable_value : if shift register is not all 1s or all zeros then -> increment delay and find_initial_stable_value
#  state find_initial_stable_value : if shift register is not all (inverted recorded value) -> increment delay and find_inverted_stable_value
#  state find_initial_stable_value : if shift register is all (inverted recorded value) -> record value and present_result
#  state find_initial_stable_value : if delay maxes out -> abort
#  state present_result : -> idle
#  state abort : -> idle
# 
# The lower FSM has to idle, handle load of delay, wait some cycles for stable, clear shift register, shift in all bits, then wait
cascaded_delay_pair  = [
    idelaye3_count_load("idelay",
              parameters={"DELAY_SRC":"DATAIN",
                          "CASCADE"  :"MASTER",
              },
              signals = {"RST":"reset__sync_clk",
                         "CLK":"clk", # Update clock
                         "DATAIN":    "data_in",
                         "LOAD":      "delay__load",
                         "CNTVALUEIN":"delay__value",
                         "DATAOUT":   "data_out",
                         "CASC_OUT":    "casc_to_odelay",
                         "CASC_RETURN": "casc_to_idelay",
              },
    ),
    odelaye3_count_load("odelay",
              parameters={"DELAY_SRC":"DATAIN",
                          "CASCADE"  :"SLAVE_END",
              },
              signals = {"RST":"reset__sync_clk",
                         "CLK":"clk", # Update clock
                         "ODATAIN":   "0",
                         "LOAD":      "delay__load",
                         "CNTVALUEIN":"delay__value",
                         "DATAOUT":   "casc_to_idelay",
                         "CASC_IN":   "casc_to_odelay",
              },
    ),
]
for m in cascaded_delay_pair:
    m.output_instance_verilog(sys.stdout)
    pass
