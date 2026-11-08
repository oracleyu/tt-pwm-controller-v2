SHELL := /bin/bash
.DEFAULT_GOAL := help
VENV ?= $(CURDIR)/.venv
PDK_ROOT ?= $(CURDIR)/.pdk
PRECHECK_PDK_ROOT ?= $(CURDIR)/.precheck-pdk
export PRECHECK_PDK_ROOT
IMAGE ?= ghcr.io/librelane/librelane:3.0.14@sha256:f851ed1ae33a641389239dcf93194a8a2077e39eab9b1afdf8f9321078e49a18
export LIBRELANE_IMAGE_OVERRIDE := $(IMAGE)
export PDK_ROOT
export PATH := $(VENV)/bin:$(PATH)
export DYLD_FALLBACK_LIBRARY_PATH := /opt/homebrew/lib
export XDG_CACHE_HOME := $(CURDIR)/.cache
.PHONY: help setup config rtl gds resume sky-synth gate plots collect warnings package all fresh cocotb cocotb-gate sta-check precheck precheck-setup cdc-audit firmware-test
help:
	@echo 'make setup; make all; see README.md'
setup:
	python3 scripts/prepare-tt.py
	HOMEBREW_NO_AUTO_UPDATE=1 brew install icarus-verilog verilator cairo libpng
	python3 -m venv "$(VENV)"
	"$(VENV)/bin/python" -m pip install -r requirements-host.txt
	docker pull $(IMAGE)
	"$(VENV)/bin/ciel" enable --pdk-root "$(PDK_ROOT)" --pdk sky130 -l sky130_fd_sc_hd -l sky130_fd_pr -l sky130_fd_io 8afc8346a57fe1ab7934ba5a6056ea8b43078e71
config:
	DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib "$(VENV)/bin/python" tt/tt_tool.py --pdk sky130A --create-user-config
rtl:
	bash scripts/generic-check.sh
cocotb-gate:
	cp src/runs/tutorial/final/pnl/tt_um_oracleyu_pwm_v2.pnl.v test/gate_level_netlist.v
	bash scripts/test-netlist.sh powered
cocotb:
	bash scripts/test-netlist.sh rtl
gds: config
	@mkdir -p reports
	set -o pipefail; "$(VENV)/bin/python" -m librelane --docker-no-tty --dockerized --pdk-root "$(PDK_ROOT)" --pdk sky130A --manual-pdk -j 2 --run-tag tutorial --hide-progress-bar src/config_merged.json 2>&1 | tee reports/flow.log
resume:
	@mkdir -p reports
	set -o pipefail; "$(VENV)/bin/python" -m librelane --docker-no-tty --dockerized --pdk-root "$(PDK_ROOT)" --pdk sky130A --manual-pdk -j 2 --run-tag tutorial --hide-progress-bar src/config_merged.json 2>&1 | tee -a reports/flow.log
sky-synth:
	"$(VENV)/bin/python" scripts/sky-synth.py
	bash scripts/sky-gate-check.sh
gate:
	bash scripts/final-gate-check.sh
plots:
	"$(VENV)/bin/python" scripts/plot-wave.py
	"$(VENV)/bin/python" scripts/render-layout.py
warnings:
	@rg -n 'WARN|ERROR|Violation|violation' reports/flow.log || true
precheck-setup:
	"$(VENV)/bin/ciel" enable --pdk-root "$(PRECHECK_PDK_ROOT)" --pdk sky130 -l sky130_fd_sc_hd 0536d02d875c8f67dd7cca3902ac457e62f20005
	"$(VENV)/bin/python" -m pip install gdstk==0.9.60
precheck:
	set -o pipefail; bash scripts/precheck.sh 2>&1 | tee reports/precheck.log
sta-check:
	docker run --rm --platform linux/arm64 --cpus 2 --memory 3g -v "$(CURDIR):/project" -v "$(PDK_ROOT):/pdk" -e PDK_ROOT=/pdk -w /project --entrypoint sta $(IMAGE) -exit scripts/sta-crosscheck.tcl > reports/sta-crosscheck.log 2>&1
fresh:
	python3 scripts/fresh.py
cdc-audit:
	"$(VENV)/bin/python" scripts/cdc-audit.py
firmware-test:
	@mkdir -p .cache/bin reports
	cc -std=c11 -Wall -Wextra -Werror -fsanitize=address,undefined -I firmware firmware/pwm_spi.c firmware/test_driver.c -o .cache/bin/firmware-test
	.cache/bin/firmware-test > reports/firmware-host-test.log
collect:
	"$(VENV)/bin/python" scripts/collect.py
all:
	$(MAKE) fresh
	$(MAKE) config
	$(MAKE) rtl
	$(MAKE) sky-synth
	$(MAKE) gds
	$(MAKE) gate
	$(MAKE) cocotb-gate
	$(MAKE) sta-check
	$(MAKE) cdc-audit
	$(MAKE) firmware-test
	$(MAKE) plots
	$(MAKE) package
package: collect
	python3 scripts/package.py
