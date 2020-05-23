//a Module ram_burst
module ram_burst_v
(
    clk,
    // clk__enable,

    addr,
    count,
    go,
    reset_n,

    data,
    done
);

    //b Clocks
    input clk;
    // input clk__enable;
    wire   clk__enable=1;
   

    //b Inputs
    input [15:0]addr;
    input [7:0]count;
    input go;
    input reset_n;

    //b Outputs
    output [15:0]data;
    output done;

// output components here

    //b Output combinatorials
    reg [15:0]data;
    reg done;

    //b Output nets

    //b Internal and output registers
    reg state__running;
    reg [7:0]state__count;
    reg [15:0]state__addr;
    reg [15:0]state__data;
    reg state__sram_has_data;
    reg state__sram_has_last_data;
    reg state__done;

    //b Internal combinatorials
    reg combs__sram_read;

    //b Internal nets
    wire [15:0]sram_read_data;

    //b Clock gating module instances
    //b Module instances
    se_sram_srw_65536x16 ram(
        .sram_clock(clk),
        .sram_clock__enable(clk__enable),
        .address(state__addr),
        .select(combs__sram_read),
        .write_data(16'h0),
        .write_enable(1'h0),
        .read_not_write(1'h1),
        .data_out(            sram_read_data)         );
    //b my_code__comb combinatorial process
    always @( //my_code__comb
        state__running or
        state__count or
        state__done or
        state__data )
    begin: my_code__comb_code
    reg combs__sram_read__var;
        combs__sram_read__var = 1'h0;
        if ((state__running!=1'h0))
        begin
            if ((state__count>=8'h1))
            begin
                combs__sram_read__var = 1'h1;
            end //if
        end //if
        done = state__done;
        data = {state__data[7:0],state__data[15:8]};
        combs__sram_read = combs__sram_read__var;
    end //always

    //b my_code__posedge_clk_active_low_reset_n clock process
    always @( posedge clk or negedge reset_n)
    begin : my_code__posedge_clk_active_low_reset_n__code
        if (reset_n==1'b0)
        begin
            state__data <= 16'h0;
            state__sram_has_data <= 1'h0;
            state__sram_has_last_data <= 1'h0;
            state__done <= 1'h0;
            state__running <= 1'h0;
            state__count <= 8'h0;
            state__addr <= 16'h0;
        end
        else if (clk__enable)
        begin
            if ((state__sram_has_data!=1'h0))
            begin
                state__data <= (state__data+sram_read_data);
            end //if
            state__sram_has_data <= 1'h0;
            state__sram_has_last_data <= 1'h0;
            state__done <= 1'h0;
            if ((!(state__running!=1'h0)&&(go!=1'h0)))
            begin
                state__running <= 1'h1;
                state__count <= count;
                state__addr <= addr;
                state__data <= 16'h0;
            end //if
            if ((state__running!=1'h0))
            begin
                state__addr <= (state__addr+16'h1);
                state__done <= 1'h0;
                if ((state__count>=8'h1))
                begin
                    state__sram_has_data <= 1'h1;
                    state__sram_has_last_data <= (state__count==8'h1);
                end //if
                if ((state__count>8'h0))
                begin
                    state__count <= (state__count-8'h1);
                end //if
                if ((state__sram_has_last_data!=1'h0))
                begin
                    state__running <= 1'h0;
                    state__done <= 1'h1;
                end //if
            end //if
        end //if
    end //always

endmodule // ram_burst
