#!/usr/bin/env bash
set -euo pipefail
mode="${1:-rtl}"
netlist="${2:-}"
mkdir -p reports
if [ -n "$netlist" ]; then netlist="$PWD/$netlist"; fi
rm -f test/results.xml test/coverage.json test/tb.vcd
make -C test MODE="$mode" NETLIST="$netlist" > "reports/test-$mode.log" 2>&1
python -m cocotb_tools.check_results test/results.xml
cp test/results.xml "reports/test-$mode.xml"
cp test/coverage.json "reports/coverage-$mode.json"
cp test/tb.vcd "reports/wave-$mode.vcd"
cat "reports/coverage-$mode.json"
