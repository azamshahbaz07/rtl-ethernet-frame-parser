#include "trace.hpp"

#include <iomanip>
#include <sstream>

TraceLog::TraceLog(const std::string& path) {
    if (!path.empty()) {
        file_.open(path, std::ios::app);
    }
}

void TraceLog::set_enabled(bool enabled) {
    enabled_ = enabled;
}

void TraceLog::byte(uint64_t cycle, uint8_t data, bool sop, bool eop, int state, uint16_t byte_idx, bool in_ready) {
    std::ostringstream oss;
    oss << "cycle=" << cycle
        << " event=byte"
        << " data=0x" << std::hex << std::setw(2) << std::setfill('0') << static_cast<unsigned>(data)
        << std::dec
        << " sop=" << sop
        << " eop=" << eop
        << " state=" << state
        << " byte_idx=" << byte_idx
        << " in_ready=" << in_ready;
    write_line(oss.str());
}

void TraceLog::meta(uint64_t cycle, const ParsedMeta& meta, bool ready) {
    std::ostringstream oss;
    oss << "cycle=" << cycle
        << " event=meta"
        << " ready=" << ready
        << " " << meta_to_string(meta)
        << " unsupported_ethertype=" << meta.unsupported_ethertype
        << " unsupported_inner_ethertype=" << meta.unsupported_inner_ethertype
        << " unsupported_l4_protocol=" << meta.unsupported_l4_protocol
        << " error_short_frame=" << meta.error_short_frame
        << " error_ipv4_bad_version=" << meta.error_ipv4_bad_version
        << " error_ipv4_options_unsupported=" << meta.error_ipv4_options_unsupported
        << " error_ipv4_total_length=" << meta.error_ipv4_total_length
        << " error_udp_length=" << meta.error_udp_length
        << " error_unexpected_eop=" << meta.error_unexpected_eop
        << " error_missing_eop=" << meta.error_missing_eop;
    write_line(oss.str());
}

void TraceLog::message(const std::string& text) {
    write_line(text);
}

const std::vector<std::string>& TraceLog::tail() const {
    return tail_;
}

void TraceLog::write_line(const std::string& line) {
    if (enabled_ && file_) {
        file_ << line << "\n";
    }
    tail_.push_back(line);
    if (tail_.size() > 20) {
        tail_.erase(tail_.begin());
    }
}
