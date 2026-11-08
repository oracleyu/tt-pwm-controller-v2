#!/usr/bin/env bash
set -euo pipefail
export ASIC_PROJECT_ROOT="$PWD"
: "${PRECHECK_PDK_ROOT:=$PWD/.precheck-pdk}"
export PDK_ROOT="$PRECHECK_PDK_ROOT"
export PDK=sky130A
export PATH="$PWD/scripts/container-tools:$PATH"
mkdir -p reports/precheck-input tt/precheck/reports
# Stage actual final views with the file names expected by the official checker.
cp src/runs/tutorial/final/gds/tt_um_oracleyu_pwm_v2.gds reports/precheck-input/tt_um_oracleyu_pwm_v2.gds
cp src/runs/tutorial/final/lef/tt_um_oracleyu_pwm_v2.lef reports/precheck-input/tt_um_oracleyu_pwm_v2.lef
cp src/runs/tutorial/final/pnl/tt_um_oracleyu_pwm_v2.pnl.v reports/precheck-input/tt_um_oracleyu_pwm_v2.v
cd tt/precheck
python precheck.py --gds "$ASIC_PROJECT_ROOT/reports/precheck-input/tt_um_oracleyu_pwm_v2.gds" --tech sky130A
