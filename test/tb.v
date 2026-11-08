`default_nettype none
`timescale 1ns/1ps
module tb;
    reg clk, rst_n, ena;
    reg [7:0] ui_in, uio_in;
    wire [7:0] uo_out, uio_out, uio_oe;
`ifdef GL_TEST
    wire VPWR=1'b1, VGND=1'b0;
`endif
    tt_um_oracleyu_pwm_v2 user_project (
`ifdef GL_TEST
        .VPWR(VPWR),.VGND(VGND),
`endif
        .clk(clk),.rst_n(rst_n),.ena(ena),.ui_in(ui_in),.uio_in(uio_in),
        .uo_out(uo_out),.uio_out(uio_out),.uio_oe(uio_oe)
    );
    initial begin
        $dumpfile("tb.vcd"); $dumpvars(1,tb);
        #100000; $dumpoff;
    end
endmodule
`default_nettype wire
