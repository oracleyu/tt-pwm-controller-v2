SIM ?= icarus
TOPLEVEL_LANG := verilog
MODE ?= rtl
ifeq ($(GATES),yes)
MODE := powered
endif
SRC_DIR := $(CURDIR)/../src
SIM_BUILD := sim_build/$(MODE)
ifeq ($(MODE),rtl)
VERILOG_SOURCES := $(SRC_DIR)/project.v
else ifeq ($(MODE),generic)
VERILOG_SOURCES := $(NETLIST)
else
COMPILE_ARGS += -DFUNCTIONAL -DSIM -DUNIT_DELAY=
VERILOG_SOURCES := $(PDK_ROOT)/sky130A/libs.ref/sky130_fd_sc_hd/verilog/primitives.v
VERILOG_SOURCES += $(PDK_ROOT)/sky130A/libs.ref/sky130_fd_sc_hd/verilog/sky130_fd_sc_hd.v
ifeq ($(MODE),powered)
COMPILE_ARGS += -DGL_TEST -DUSE_POWER_PINS
VERILOG_SOURCES += $(CURDIR)/gate_level_netlist.v
else
VERILOG_SOURCES += $(NETLIST)
endif
endif
VERILOG_SOURCES += $(CURDIR)/tb.v
COMPILE_ARGS += -I$(SRC_DIR)
TOPLEVEL := tb
COCOTB_TEST_MODULES := test
include $(shell cocotb-config --makefiles)/Makefile.sim
