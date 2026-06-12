PYTHON ?= python3
VERILATOR ?= verilator

RTL_SRCS := rtl/eth_parser_pkg.sv rtl/eth_frame_parser.sv
SIM_SRCS := sim/main.cpp sim/packet.cpp sim/reference_parser.cpp sim/scoreboard.cpp sim/trace.cpp
SIM_EXE := obj_dir/eth_parser_sim

.PHONY: build corpus run regression trace waves report test clean

build:
	$(VERILATOR) -Wall -Wno-fatal --trace --cc $(RTL_SRCS) \
		--top-module eth_frame_parser \
		--exe $(SIM_SRCS) \
		-Irtl \
		--Mdir obj_dir \
		--build \
		-o eth_parser_sim \
		-CFLAGS "-std=c++17 -O2"

corpus:
	$(PYTHON) tools/make_corpus.py --random 500 --seed 123

run: build corpus
	$(SIM_EXE) --corpus corpus/directed.json --trace logs/run.trace --seed 123

regression:
	$(PYTHON) tools/run_regression.py --directed 1 --random 500 --seed 123

CASE ?= valid_ipv4_udp_min_payload
trace: build corpus
	@mkdir -p logs
	@rm -f logs/$(CASE).trace
	$(SIM_EXE) --corpus corpus/directed.json --case $(CASE) --trace logs/$(CASE).trace --seed 123
	$(PYTHON) tools/parse_trace.py logs/$(CASE).trace --json-out results/$(CASE)_trace_summary.json

waves: build corpus
	@mkdir -p logs waves
	@rm -f logs/$(CASE).trace waves/$(CASE).vcd
	$(SIM_EXE) --corpus corpus/directed.json --case $(CASE) --trace logs/$(CASE).trace --vcd waves/$(CASE).vcd --seed 123
	@echo "Wrote waves/$(CASE).vcd"

report:
	$(PYTHON) tools/coverage_report.py

test:
	$(PYTHON) -m unittest discover -s tests

clean:
	rm -rf obj_dir build/*
	rm -f logs/*.log logs/*.trace
	rm -f waves/*.vcd waves/*.fst waves/*.gtkw
	rm -f results/*.json results/*.md
	rm -f corpus/*.json
