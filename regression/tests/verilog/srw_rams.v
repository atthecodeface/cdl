//m se_sram_srw_65536x16
module se_sram_srw_65536x16( sram_clock, sram_clock__enable, write_data, address, write_enable, read_not_write, select, data_out );
    parameter initfile="",address_width=16,data_width=16;
    input sram_clock, sram_clock__enable, select, read_not_write;
    input write_enable;
    input [address_width-1:0] address;
    input [data_width-1:0]    write_data;
    output [data_width-1:0]   data_out;
    se_sram_srw_we #(address_width,data_width,initfile) ram(sram_clock,sram_clock__enable,write_data,address, write_enable,read_not_write,select,data_out);
endmodule
