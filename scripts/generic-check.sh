#!/usr/bin/env bash
set -euo pipefail
mkdir -p reports
verilator --lint-only --Wall -Wno-DECLFILENAME --top-module tt_um_oracleyu_pwm_v2 src/project.v 2>&1 | tee reports/lint-native.log
yowasp-yosys -l reports/generic-synthesis.log -p 'read_verilog src/project.v; synth -top tt_um_oracleyu_pwm_v2; check -assert; stat; write_verilog -noattr reports/generic-netlist.v; write_json reports/generic-netlist.json' > reports/generic-synthesis-console.log
bash scripts/test-netlist.sh rtl
bash scripts/test-netlist.sh generic reports/generic-netlist.v
