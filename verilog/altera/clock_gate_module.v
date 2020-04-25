module clock_gate_module(
                         CLK_IN, ENABLE, CLK_OUT );
   input CLK_IN, ENABLE;
   output CLK_OUT;

`ifndef CLK_GATE_USE_LOGIC
   altclkctrl clock_gate(.ena(ENABLE), .inclk(CLK_IN), .outclk(CLK_OUT) );
`else   

   reg    enable_latch;
   `ifdef CLK_GATE_USE_LATCH
   always @(CLK_IN or ENABLE)
     begin
        if (!CLK_IN)
          begin
             enable_latch = ENABLE;
          end
     end
   `else
   always @(negedge CLK_IN)
     begin
        enable_latch <= ENABLE;
     end
   `endif
   assign CLK_OUT=enable_latch&CLK_IN;
`endif
   
endmodule // clock_gate_module

//module altclkctrl
//#( parameter clock_type = "AUTO",
//parameter intended_device_family = "unused",
//parameter ena_register_mode = "falling edge",
//parameter implement_in_les = "OFF",
//parameter number_of_clocks = 4,
//parameter use_glitch_free_switch_over_implementation = "OFF",
//parameter width_clkselect = 2,
//parameter lpm_type = "altclkctrl",
//parameter lpm_hint = "unused")
//( input wire [width_clkselect-1:0] clkselect,
//input wire ena,
//input wire [number_of_clocks-1:0] inclk,
//output wire outclk)/* synthesis syn_black_box=1 */;
//endmodule //altclkctrl



// // Location: CLKCTRL_G6
// cyclonev_clkena \CLOCK_50~inputCLKENA0 (
// 	.inclk(\CLOCK_50~input_o ),
// 	.ena(vcc),
// 	.outclk(\CLOCK_50~inputCLKENA0_outclk ),
// 	.enaout());
// // synopsys translate_off
// defparam \CLOCK_50~inputCLKENA0 .clock_type = "global clock";
// defparam \CLOCK_50~inputCLKENA0 .disable_mode = "low";
// defparam \CLOCK_50~inputCLKENA0 .ena_register_mode = "always enabled";
// defparam \CLOCK_50~inputCLKENA0 .ena_register_power_up = "high";
// defparam \CLOCK_50~inputCLKENA0 .test_syn = "high";


 
