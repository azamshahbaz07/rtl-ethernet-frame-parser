#include "Veth_frame_parser.h"
#include "packet.hpp"
#include "reference_parser.hpp"
#include "scoreboard.hpp"
#include "trace.hpp"
#include "verilated.h"
#include "verilated_vcd_c.h"

#include <algorithm>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <memory>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
struct Options {
    std::string corpus = "corpus/directed.json";
    std::string trace = "logs/sim.trace";
    std::string vcd;
    std::string case_filter;
    uint32_t seed = 1;
};

bool has_tag(const PacketCase& packet, const std::string& tag) {
    return std::find(packet.tags.begin(), packet.tags.end(), tag) != packet.tags.end();
}

Options parse_args(int argc, char** argv) {
    Options options;
    for (int i = 1; i < argc; ++i) {
        const std::string arg = argv[i];
        auto need_value = [&](const std::string& flag) -> std::string {
            if (i + 1 >= argc) {
                throw std::runtime_error("missing value for " + flag);
            }
            return argv[++i];
        };
        if (arg == "--corpus") {
            options.corpus = need_value(arg);
        } else if (arg == "--trace") {
            options.trace = need_value(arg);
        } else if (arg == "--vcd") {
            options.vcd = need_value(arg);
        } else if (arg == "--case") {
            options.case_filter = need_value(arg);
        } else if (arg == "--seed") {
            options.seed = static_cast<uint32_t>(std::stoul(need_value(arg)));
        } else {
            throw std::runtime_error("unknown argument: " + arg);
        }
    }
    return options;
}

class WaveDump {
public:
    WaveDump(Veth_frame_parser& dut, const std::string& path) {
        if (path.empty()) {
            return;
        }
        Verilated::traceEverOn(true);
        trace_ = std::make_unique<VerilatedVcdC>();
        dut.trace(trace_.get(), 99);
        trace_->open(path.c_str());
    }

    ~WaveDump() {
        if (trace_) {
            trace_->close();
        }
    }

    void dump(uint64_t time) {
        if (trace_) {
            trace_->dump(time);
        }
    }

private:
    std::unique_ptr<VerilatedVcdC> trace_;
};

void eval_comb(Veth_frame_parser& dut, WaveDump& waves, uint64_t& sim_time) {
    dut.eval();
    waves.dump(sim_time++);
}

void tick(Veth_frame_parser& dut, uint64_t& cycle, WaveDump& waves, uint64_t& sim_time) {
    dut.clk = 0;
    dut.eval();
    waves.dump(sim_time++);
    dut.clk = 1;
    dut.eval();
    waves.dump(sim_time++);
    ++cycle;
    dut.clk = 0;
    dut.eval();
    waves.dump(sim_time++);
}

void reset(Veth_frame_parser& dut, uint64_t& cycle, WaveDump& waves, uint64_t& sim_time) {
    dut.in_data = 0;
    dut.in_valid = 0;
    dut.in_sop = 0;
    dut.in_eop = 0;
    dut.meta_ready = 1;
    dut.rst_n = 0;
    for (int i = 0; i < 5; ++i) {
        tick(dut, cycle, waves, sim_time);
    }
    dut.rst_n = 1;
    tick(dut, cycle, waves, sim_time);
}

struct RunResult {
    bool pass = false;
    bool observed_meta = false;
    ParsedMeta got;
    ParsedMeta expected;
    std::vector<std::string> messages;
};

RunResult run_one(const PacketCase& packet, uint32_t seed, TraceLog& trace, const std::string& vcd_path) {
    RunResult result;
    result.expected = parse_reference(packet.frame);

    Veth_frame_parser dut;
    WaveDump waves(dut, vcd_path);
    uint64_t cycle = 0;
    uint64_t sim_time = 0;
    reset(dut, cycle, waves, sim_time);

    std::mt19937 rng(seed);
    std::uniform_real_distribution<double> dist(0.0, 1.0);

    for (size_t i = 0; i < packet.frame.size(); ++i) {
        if (packet.input_gap_prob > 0.0 && dist(rng) < packet.input_gap_prob) {
            const int gaps = 1 + static_cast<int>(rng() % 3);
            for (int g = 0; g < gaps; ++g) {
                dut.in_valid = 0;
                dut.in_sop = 0;
                dut.in_eop = 0;
                dut.meta_ready = 1;
                tick(dut, cycle, waves, sim_time);
            }
        }

        dut.in_data = packet.frame[i];
        dut.in_valid = 1;
        dut.in_sop = (i == 0);
        dut.in_eop = (i == packet.frame.size() - 1);
        dut.meta_ready = 1;
        eval_comb(dut, waves, sim_time);
        while (!dut.in_ready) {
            dut.in_valid = 0;
            dut.in_sop = 0;
            dut.in_eop = 0;
            tick(dut, cycle, waves, sim_time);
            dut.in_data = packet.frame[i];
            dut.in_valid = 1;
            dut.in_sop = (i == 0);
            dut.in_eop = (i == packet.frame.size() - 1);
            eval_comb(dut, waves, sim_time);
        }
        trace.byte(cycle, packet.frame[i], i == 0, i == packet.frame.size() - 1,
                   dut.state_dbg, dut.byte_idx_dbg, dut.in_ready);
        tick(dut, cycle, waves, sim_time);
        dut.in_valid = 0;
        dut.in_sop = 0;
        dut.in_eop = 0;
    }

    int stall_remaining = packet.meta_stall_cycles;
    int wait_cycles = 0;
    bool have_previous_stalled_meta = false;
    ParsedMeta previous_stalled_meta;

    while (wait_cycles < 200) {
        dut.in_valid = 0;
        dut.in_sop = 0;
        dut.in_eop = 0;
        eval_comb(dut, waves, sim_time);

        const bool valid_now = dut.meta_valid;
        dut.meta_ready = (valid_now && stall_remaining > 0) ? 0 : 1;
        eval_comb(dut, waves, sim_time);

        if (dut.meta_valid) {
            ParsedMeta current = unpack_dut_meta(dut.meta_flat);
            trace.meta(cycle, current, dut.meta_ready);

            if (!dut.meta_ready) {
                if (have_previous_stalled_meta) {
                    CompareResult stable = compare_meta(previous_stalled_meta, current);
                    if (!stable.pass) {
                        result.messages.push_back("metadata changed while meta_valid && !meta_ready");
                        result.messages.insert(result.messages.end(), stable.messages.begin(), stable.messages.end());
                    }
                }
                previous_stalled_meta = current;
                have_previous_stalled_meta = true;
            }

            if (dut.meta_ready) {
                result.got = current;
                result.observed_meta = true;
                tick(dut, cycle, waves, sim_time);
                break;
            }
        }

        tick(dut, cycle, waves, sim_time);
        if (valid_now && stall_remaining > 0) {
            --stall_remaining;
        }
        ++wait_cycles;
    }

    if (!result.observed_meta) {
        result.messages.push_back("DUT did not emit metadata within timeout");
        return result;
    }

    CompareResult comparison = compare_meta(result.expected, result.got);
    result.pass = comparison.pass && result.messages.empty();
    result.messages.insert(result.messages.end(), comparison.messages.begin(), comparison.messages.end());
    return result;
}

void print_failure(const PacketCase& packet, const RunResult& result, const TraceLog& trace) {
    std::cout << "[FAIL] " << packet.name << "\n";
    for (const std::string& message : result.messages) {
        std::cout << message << "\n";
    }
    std::cout << "frame length: " << packet.frame.size() << "\n";
    std::cout << "frame bytes: " << bytes_to_hex(packet.frame) << "\n";
    std::cout << "expected: " << meta_to_string(result.expected) << "\n";
    if (result.observed_meta) {
        std::cout << "got:      " << meta_to_string(result.got) << "\n";
    }
    std::cout << "last trace events:\n";
    for (const std::string& line : trace.tail()) {
        std::cout << line << "\n";
    }
}
}  // namespace

int main(int argc, char** argv) {
    Verilated::commandArgs(argc, argv);

    try {
        const Options options = parse_args(argc, argv);
        if (!options.vcd.empty() && options.case_filter.empty()) {
            throw std::runtime_error("--vcd requires --case so one waveform file maps to one packet case");
        }
        const std::vector<PacketCase> cases = load_corpus(options.corpus);
        TraceLog trace(options.trace);

        int run_count = 0;
        int pass_count = 0;
        for (const PacketCase& packet : cases) {
            if (!options.case_filter.empty() && packet.name != options.case_filter) {
                continue;
            }
            const uint32_t case_seed = options.seed ^ static_cast<uint32_t>(std::hash<std::string>{}(packet.name));
            RunResult result = run_one(packet, case_seed, trace, options.vcd);
            ++run_count;
            if (result.pass) {
                ++pass_count;
                std::cout << "[PASS] " << packet.name << "\n";
            } else {
                print_failure(packet, result, trace);
                std::cout << "Regression: " << pass_count << "/" << run_count << " PASS\n";
                return 1;
            }
        }

        if (run_count == 0) {
            std::cout << "[FAIL] no cases matched";
            if (!options.case_filter.empty()) {
                std::cout << " filter=" << options.case_filter;
            }
            std::cout << "\n";
            return 1;
        }

        std::cout << "Regression: " << pass_count << "/" << run_count << " PASS\n";
        return pass_count == run_count ? 0 : 1;
    } catch (const std::exception& ex) {
        std::cerr << "[ERROR] " << ex.what() << "\n";
        return 2;
    }
}
