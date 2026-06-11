#pragma once

#include <cstdint>
#include <string>
#include <vector>

struct PacketCase {
    std::string name;
    std::vector<uint8_t> frame;
    std::vector<std::string> tags;
    double input_gap_prob = 0.0;
    int meta_stall_cycles = 0;
};

std::vector<PacketCase> load_corpus(const std::string& path);
