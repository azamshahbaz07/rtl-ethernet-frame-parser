#pragma once

#include "reference_parser.hpp"

#include <cstdint>
#include <fstream>
#include <string>
#include <vector>

class TraceLog {
public:
    explicit TraceLog(const std::string& path);
    void set_enabled(bool enabled);
    void byte(uint64_t cycle, uint8_t data, bool sop, bool eop, int state, uint16_t byte_idx, bool in_ready);
    void meta(uint64_t cycle, const ParsedMeta& meta, bool ready);
    void message(const std::string& text);
    const std::vector<std::string>& tail() const;

private:
    void write_line(const std::string& line);

    bool enabled_ = true;
    std::ofstream file_;
    std::vector<std::string> tail_;
};
