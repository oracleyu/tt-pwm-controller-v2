# Independent read-back of the final netlist, constraints, and extracted RC.
read_liberty $::env(PDK_ROOT)/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__ss_100C_1v60.lib
read_verilog src/runs/tutorial/final/nl/tt_um_oracleyu_pwm_v2.nl.v
link_design tt_um_oracleyu_pwm_v2
read_sdc src/runs/tutorial/final/sdc/tt_um_oracleyu_pwm_v2.sdc
read_spef src/runs/tutorial/final/spef/max/tt_um_oracleyu_pwm_v2.max.spef
puts "ACTUAL_PROPAGATED_CLOCK=[get_property [get_clocks clk] is_propagated]"
puts "REGISTER_CLOCK_PIN_COUNT=[llength [all_registers -clock_pins]]"
puts "REGISTER_DATA_PIN_COUNT=[llength [all_registers -data_pins]]"
puts "REGISTER_TO_REGISTER_SETUP_SS_MAX_RC"
report_checks -from [all_registers -clock_pins] -to [all_registers -data_pins] -path_delay max -group_path_count 3 -digits 6
puts "ALL_PATHS_SETUP_SS_MAX_RC"
report_worst_slack -max
puts "CONSTRAINT_COVERAGE"
check_setup -verbose -unconstrained_endpoints -no_clock -no_input_delay -loops
