SIM ?= icarus
TOPLEVEL_LANG ?= verilog
SV2V ?= /export/sv2v/bin/sv2v

VERILOG_SOURCES :=
VERILOG_SOURCES += $(PWD)/wrap_spi_slave.v
VERILOG_SOURCES += $(PWD)/spi_slave.sv

TOPLEVEL := wrap_spi_slave

MODULE := tb_spi_slave

include $(shell cocotb-config --makefiles)/Makefile.sim

%.v: %.sv
	$(SV2V) -w $@ $<
