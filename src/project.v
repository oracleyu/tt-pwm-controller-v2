// SPDX-License-Identifier: Apache-2.0
// V2: oversampled SPI mode 0, atomic 40-bit commands, registered dual PWM.
`default_nettype none
module tt_um_oracleyu_pwm_v2 (
    input wire [7:0] ui_in,
    output wire [7:0] uo_out,
    input wire [7:0] uio_in,
    output wire [7:0] uio_out, uio_oe,
    input wire ena, clk, rst_n
);
    localparam [7:0] CMD_READ=8'h00, CMD_WRITE=8'ha1, CMD_CLEAR=8'hc0;
    // Asynchronous assertion, two-clock synchronous release.
    (* async_reg = "true" *) reg reset_meta, reset_release;
    always @(posedge clk or negedge rst_n)
        if (!rst_n) begin reset_meta<=1'b0; reset_release<=1'b0; end
        else begin reset_meta<=1'b1; reset_release<=reset_meta; end
    wire reset_n = reset_release;

    // No SPI-clocked logic. Input timing limits are part of the interface contract.
    (* async_reg = "true" *) reg [2:0] sck_sync, cs_sync, mosi_sync;
    always @(posedge clk or negedge reset_n) begin
        if (!reset_n) begin
            sck_sync <= 3'b000;
            cs_sync <= 3'b111;
            mosi_sync <= 3'b000;
        end else begin
            sck_sync <= {sck_sync[1:0],ui_in[0]};
            cs_sync <= {cs_sync[1:0],ui_in[1]};
            mosi_sync <= {mosi_sync[1:0],ui_in[2]};
        end
    end
    wire cs_start = cs_sync[2] && !cs_sync[1];
    wire cs_end = !cs_sync[2] && cs_sync[1];
    wire sck_rise = !sck_sync[2] && sck_sync[1];
    wire sck_fall = sck_sync[2] && !sck_sync[1];

    reg [7:0] active_left, active_right, active_div;
    reg active_enable;
    reg [7:0] shadow_left, shadow_right, shadow_div;
    reg shadow_enable, pending, commit_toggle;
    reg frame_error, overrun_error;
    reg [7:0] phase, divider_count;
    reg pwm_left, pwm_right, period_pulse;
    reg [39:0] rx_shift;
    reg [38:0] tx_shift;
    reg [5:0] bit_count;
    reg transaction_active, miso;

    wire tick = divider_count == active_div;
    wire boundary = tick && (&phase);
    wire commit_now = pending && boundary;
    wire [7:0] phase_next = tick ? phase + 8'd1 : phase;
    wire [7:0] next_left = commit_now ? shadow_left : active_left;
    wire [7:0] next_right = commit_now ? shadow_right : active_right;
    wire next_enable = commit_now ? shadow_enable : active_enable;
    wire [7:0] status_byte = {3'b000,commit_toggle,overrun_error,frame_error,pending,active_enable};
    wire [39:0] response = {8'hc2,status_byte,active_left,active_right,active_div};

    always @(posedge clk or negedge reset_n) begin
        if (!reset_n) begin
            active_left<=0; active_right<=0; active_div<=8'd1; active_enable<=0;
            shadow_left<=0; shadow_right<=0; shadow_div<=8'd1; shadow_enable<=0;
            pending<=0; commit_toggle<=0; frame_error<=0; overrun_error<=0;
            phase<=0; divider_count<=0; pwm_left<=0; pwm_right<=0; period_pulse<=0;
            rx_shift<=0; tx_shift<=0; bit_count<=0; transaction_active<=0; miso<=0;
        end else begin
            period_pulse<=0;
            if (!ena) begin
                // Retain PWM/config state; discard an in-progress SPI frame.
                pwm_left<=0; pwm_right<=0;
                transaction_active<=0; bit_count<=0; miso<=0;
            end else begin
                if (tick) begin divider_count<=0; phase<=phase_next; end
                else divider_count<=divider_count+8'd1;
                period_pulse<=boundary;
                // Compute from the next phase/config so every PWM edge is registered.
                pwm_left<=next_enable && (phase_next < next_left);
                pwm_right<=next_enable && (phase_next < next_right);
                if (commit_now) begin
                    active_left<=shadow_left; active_right<=shadow_right;
                    active_div<=shadow_div; active_enable<=shadow_enable;
                    pending<=0; commit_toggle<=!commit_toggle;
                end

                if (cs_start) begin
                    transaction_active<=1; bit_count<=0; rx_shift<=0;
                    tx_shift<=response[38:0]; miso<=response[39];
                end else if (cs_end) begin
                    transaction_active<=0; miso<=0;
                    if (transaction_active) begin
                        if (bit_count != 6'd40) frame_error<=1;
                        else begin
                            case (rx_shift[39:32])
                                CMD_READ: if (rx_shift[31:0] != 0) frame_error<=1;
                                CMD_CLEAR: begin
                                    if (rx_shift[31:0] != 0) frame_error<=1;
                                    else begin frame_error<=0; overrun_error<=0; end
                                end
                                CMD_WRITE: begin
                                    if (rx_shift[7:1] != 0) frame_error<=1;
                                    else if (pending && !commit_now) overrun_error<=1;
                                    else begin
                                        shadow_left<=rx_shift[31:24];
                                        shadow_right<=rx_shift[23:16];
                                        shadow_div<=rx_shift[15:8];
                                        shadow_enable<=rx_shift[0];
                                        pending<=1;
                                    end
                                end
                                default: frame_error<=1;
                            endcase
                        end
                    end
                end else if (transaction_active && !cs_sync[2]) begin
                    if (sck_rise) begin
                        if (bit_count < 6'd40) rx_shift<={rx_shift[38:0],mosi_sync[2]};
                        if (bit_count < 6'd41) bit_count<=bit_count+6'd1;
                    end
                    if (sck_fall) begin
                        tx_shift<={tx_shift[37:0],1'b0}; miso<=tx_shift[38];
                    end
                end
            end
        end
    end
    assign uo_out = {period_pulse,frame_error|overrun_error,phase[7],active_enable,pending,miso,pwm_right,pwm_left};
    assign uio_out=8'b0;
    assign uio_oe=8'b0;
    wire _unused=&{ui_in[7:3],uio_in,1'b0};
endmodule
`default_nettype wire
