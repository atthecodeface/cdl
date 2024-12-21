module top(input clk, input reset_l);
   reg [7:0] i0, i1;
   reg [7:0] last_i0, last_i1;
   wire [7:0] o0, o1;

   always @(posedge clk or negedge reset_l) begin
      if (reset_l==0) begin
         i0 <= 0;
         i1 <= 0;
      end
      else
        begin
           last_i0 <= i0;
           last_i1 <= i1;
           i0 <= i0 + 1;
           i1 <= i1 + i0;
           $display(last_i0,last_i1,last_i0+last_i1,o0,o1);
        end
      
   end
   
   vector_sum__width_8 blob(.io_clock(clk),

    .vector_input_1(i1),
    .vector_input_0(i0),
    .io_reset(!reset_l),

    .vector_output_1(o1),
    .vector_output_0(o0)
);
endmodule
