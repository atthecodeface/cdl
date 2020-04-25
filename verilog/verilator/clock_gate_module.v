module clock_gate_module( input CLK_IN,
                          input  ENABLE,
                          output CLK_OUT );
   reg enable_latch;
   always @(negedge CLK_IN) enable_latch <= ENABLE;
   assign CLK_OUT = enable_latch & CLK_IN;
endmodule
