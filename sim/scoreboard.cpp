#include "scoreboard.hpp"

#include <iomanip>
#include <sstream>

namespace {
template <typename T>
void check_field(CompareResult& result, const std::string& name, T expected, T got) {
    if (expected == got) {
        return;
    }
    result.pass = false;
    std::ostringstream oss;
    oss << "field: " << name << "\n"
        << "expected: 0x" << std::hex << std::setfill('0') << +expected << "\n"
        << "got:      0x" << +got;
    result.messages.push_back(oss.str());
}

void check_bool(CompareResult& result, const std::string& name, bool expected, bool got) {
    if (expected == got) {
        return;
    }
    result.pass = false;
    std::ostringstream oss;
    oss << "field: " << name << "\n"
        << "expected: " << expected << "\n"
        << "got:      " << got;
    result.messages.push_back(oss.str());
}
}  // namespace

CompareResult compare_meta(const ParsedMeta& expected, const ParsedMeta& got) {
    CompareResult result;

    check_field(result, "dst_mac", expected.dst_mac, got.dst_mac);
    check_field(result, "src_mac", expected.src_mac, got.src_mac);
    check_field(result, "ethertype", expected.ethertype, got.ethertype);
    check_bool(result, "vlan_present", expected.vlan_present, got.vlan_present);
    check_field(result, "vlan_id", expected.vlan_id, got.vlan_id);
    check_field(result, "vlan_pcp", expected.vlan_pcp, got.vlan_pcp);
    check_bool(result, "vlan_dei", expected.vlan_dei, got.vlan_dei);
    check_field(result, "inner_ethertype", expected.inner_ethertype, got.inner_ethertype);
    check_bool(result, "ipv4_present", expected.ipv4_present, got.ipv4_present);
    check_field(result, "ipv4_version", expected.ipv4_version, got.ipv4_version);
    check_field(result, "ipv4_ihl", expected.ipv4_ihl, got.ipv4_ihl);
    check_field(result, "ipv4_total_length", expected.ipv4_total_length, got.ipv4_total_length);
    check_field(result, "ipv4_protocol", expected.ipv4_protocol, got.ipv4_protocol);
    check_field(result, "ipv4_ttl", expected.ipv4_ttl, got.ipv4_ttl);
    check_field(result, "src_ip", expected.src_ip, got.src_ip);
    check_field(result, "dst_ip", expected.dst_ip, got.dst_ip);
    check_bool(result, "udp_present", expected.udp_present, got.udp_present);
    check_field(result, "udp_src_port", expected.udp_src_port, got.udp_src_port);
    check_field(result, "udp_dst_port", expected.udp_dst_port, got.udp_dst_port);
    check_field(result, "udp_length", expected.udp_length, got.udp_length);
    check_field(result, "frame_length", expected.frame_length, got.frame_length);
    check_field(result, "header_bytes", expected.header_bytes, got.header_bytes);
    check_bool(result, "unsupported_ethertype", expected.unsupported_ethertype, got.unsupported_ethertype);
    check_bool(result, "unsupported_inner_ethertype", expected.unsupported_inner_ethertype, got.unsupported_inner_ethertype);
    check_bool(result, "unsupported_l4_protocol", expected.unsupported_l4_protocol, got.unsupported_l4_protocol);
    check_bool(result, "error_short_frame", expected.error_short_frame, got.error_short_frame);
    check_bool(result, "error_ipv4_bad_version", expected.error_ipv4_bad_version, got.error_ipv4_bad_version);
    check_bool(result, "error_ipv4_options_unsupported", expected.error_ipv4_options_unsupported, got.error_ipv4_options_unsupported);
    check_bool(result, "error_ipv4_total_length", expected.error_ipv4_total_length, got.error_ipv4_total_length);
    check_bool(result, "error_udp_length", expected.error_udp_length, got.error_udp_length);
    check_bool(result, "error_unexpected_eop", expected.error_unexpected_eop, got.error_unexpected_eop);
    check_bool(result, "error_missing_eop", expected.error_missing_eop, got.error_missing_eop);

    return result;
}
