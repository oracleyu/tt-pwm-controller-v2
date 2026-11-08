# Units: ns, pF in SKY130 HD. ena is synchronous; SPI and raw reset are asynchronous.
create_clock -name clk -period 20.0 [get_ports clk]
set_clock_uncertainty -setup 0.20 [get_clocks clk]
set_clock_uncertainty -hold 0.10 [get_clocks clk]
set_clock_transition 0.15 [get_clocks clk]
set data_inputs [get_ports {ui_in* uio_in* ena rst_n}]
set_input_delay -clock clk -max 4.0 $data_inputs
set_input_delay -clock clk -min 1.0 $data_inputs
set_input_transition 0.20 $data_inputs
# External asynchronous paths terminate at the synchronizer inputs/reset pins.
# Internal synchronizer-stage and synchronized-reset paths remain timed.
set_false_path -from [get_ports {ui_in[0] ui_in[1] ui_in[2] rst_n}]
set_output_delay -clock clk -max 4.0 [all_outputs]
set_output_delay -clock clk -min 1.0 [all_outputs]
set_load 0.05 [all_outputs]
# Match LibreLane clock handling: ideal before CTS, propagated after CTS.
if {[info exists ::env(OPENLANE_SDC_IDEAL_CLOCKS)] && $::env(OPENLANE_SDC_IDEAL_CLOCKS)} {
    unset_propagated_clock [all_clocks]
} else {
    set_propagated_clock [all_clocks]
}
